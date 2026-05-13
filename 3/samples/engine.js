(function attachReportEngine(root, factory) {
  const engine = factory();
  if (typeof module === "object" && module.exports) {
    module.exports = engine;
  }
  root.ReportEngine = engine;
})(typeof globalThis !== "undefined" ? globalThis : this, function createReportEngine() {
  const keywordSets = {
    completed: [
      "完成",
      "已完成",
      "搞定",
      "交付",
      "上线",
      "发布",
      "修复",
      "解决",
      "提交",
      "合并",
      "实现",
      "整理",
      "撰写",
      "输出",
      "部署",
      "验收",
      "done",
      "fixed",
      "finished",
      "closed",
    ],
    blocked: [
      "延期",
      "阻塞",
      "卡住",
      "等待",
      "依赖",
      "未完成",
      "问题",
      "报错",
      "失败",
      "缺少",
      "异常",
      "延迟",
      "返工",
      "delay",
      "blocked",
      "blocker",
      "failed",
    ],
    risk: ["风险", "可能", "担心", "不确定", "瓶颈", "隐患", "冲突", "超时", "不可控"],
    planned: [
      "下周",
      "计划",
      "准备",
      "将",
      "继续",
      "预计",
      "待办",
      "排期",
      "安排",
      "目标",
      "下一步",
      "todo",
      "follow up",
    ],
    output: [
      "产出",
      "成果",
      "文档",
      "报告",
      "版本",
      "原型",
      "PR",
      "MR",
      "commit",
      "代码",
      "脚本",
      "接口",
      "看板",
      "图表",
      "PPT",
      "演示",
      "demo",
      "方案",
      "模板",
      "数据集",
    ],
    meeting: ["会议", "评审", "沟通", "对齐", "同步", "讨论", "需求会", "周会", "答辩"],
  };

  const metricDefinitions = [
    { key: "taskTotal", label: "任务数", unit: "项", type: "count" },
    { key: "completed", label: "完成数", unit: "项", type: "count" },
    { key: "completionRate", label: "完成率", unit: "%", type: "rate" },
    { key: "delayed", label: "延期/阻塞", unit: "项", type: "count" },
    { key: "outputs", label: "产出数", unit: "项", type: "count" },
    { key: "issues", label: "问题数", unit: "项", type: "count" },
    { key: "risks", label: "风险数", unit: "项", type: "count" },
    { key: "plans", label: "下周计划", unit: "项", type: "count" },
  ];

  function normalizeText(text) {
    return String(text || "")
      .replace(/\r\n/g, "\n")
      .replace(/\r/g, "\n")
      .replace(/\u3000/g, " ")
      .replace(/[ \t]+/g, " ")
      .trim();
  }

  function stripMarkdownMarker(line) {
    return line
      .replace(/^\s{0,4}[-*+]\s+/, "")
      .replace(/^\s{0,4}\d+[.)、]\s+/, "")
      .replace(/^\s{0,4}>+\s?/, "")
      .replace(/^\s{0,4}\[[ xX]\]\s+/, "")
      .replace(/^#+\s*/, "")
      .trim();
  }

  function splitEntries(text) {
    const normalized = normalizeText(text);
    if (!normalized) return [];

    return normalized
      .replace(/([。；;!?！？])\s+/g, "$1\n")
      .split(/\n+/)
      .flatMap((line) => {
        const trimmed = stripMarkdownMarker(line);
        if (!trimmed) return [];
        if (trimmed.length > 80 && /[。；;]/.test(trimmed)) {
          return trimmed
            .split(/(?<=[。；;])\s*/)
            .map(stripMarkdownMarker)
            .filter(Boolean);
        }
        return [trimmed];
      })
      .map((line) => line.replace(/\s+/g, " ").trim())
      .filter((line) => line.length >= 2);
  }

  function includesKeyword(text, keywords) {
    const upper = text.toUpperCase();
    const lower = text.toLowerCase();
    return keywords.some((keyword) => {
      if (/^[a-z0-9 _-]+$/i.test(keyword)) {
        return lower.includes(keyword.toLowerCase());
      }
      return upper.includes(keyword.toUpperCase());
    });
  }

  function countKeywords(text, keywords) {
    return keywords.reduce((score, keyword) => score + (includesKeyword(text, [keyword]) ? 1 : 0), 0);
  }

  function detectExplicitLabel(entry) {
    const compact = entry.replace(/\s+/g, "");
    const labelPatterns = [
      { status: "completed", bucket: "results", pattern: /^(完成|已完成|成果|产出|Done|Result|Output)[：:]/i },
      { status: "blocked", bucket: "issues", pattern: /^(问题|风险|阻塞|延期|Issue|Risk|Blocker)[：:]/i },
      { status: "planned", bucket: "plans", pattern: /^(下周|计划|待办|下一步|Plan|Todo)[：:]/i },
      { status: "in_progress", bucket: "tasks", pattern: /^(任务|进展|推进|本周|Task|Progress)[：:]/i },
    ];
    return labelPatterns.find((item) => item.pattern.test(compact)) || null;
  }

  function detectStatus(entry) {
    const explicit = detectExplicitLabel(entry);
    if (explicit) return explicit.status;

    const completedScore = countKeywords(entry, keywordSets.completed);
    const blockedScore = countKeywords(entry, keywordSets.blocked) + countKeywords(entry, keywordSets.risk);
    const plannedScore = countKeywords(entry, keywordSets.planned);

    if (blockedScore > 0 && completedScore === 0) return "blocked";
    if (completedScore > 0) return "completed";
    if (plannedScore > 0) return "planned";
    if (blockedScore > 0) return "blocked";
    return "in_progress";
  }

  function detectTags(entry) {
    const tags = new Set();
    const topicRules = [
      { name: "KPI", pattern: /KPI|指标|完成率|环比|统计/i },
      { name: "可视化", pattern: /可视化|图表|看板|分布图|趋势图/i },
      { name: "Markdown", pattern: /Markdown|md|周报|飞书|钉钉|企业微信|Notion/i },
      { name: "语音输入", pattern: /语音|听写|转写|识别/i },
      { name: "AI 润色", pattern: /DeepSeek|Coze|扣子|LLM|大模型|润色|Prompt/i },
      { name: "答辩材料", pattern: /海报|答辩|演示|PPT|展示/i },
    ];
    topicRules.forEach((rule) => {
      if (rule.pattern.test(entry)) tags.add(rule.name);
    });

    const hashMatches = entry.match(/#[\p{L}\p{N}_-]+/gu) || [];
    hashMatches.forEach((tag) => tags.add(tag.replace(/^#/, "")));

    const bracketMatches = entry.match(/[【[]([^】\]]{1,16})[】\]]/g) || [];
    bracketMatches.forEach((tag) => tags.add(tag.replace(/[【】[\]]/g, "")));

    const prefix = entry.match(/^([\p{L}\p{N}_-]{2,12})[：:]/u);
    if (prefix && !/^(完成|问题|风险|计划|下周|任务|本周|周[一二三四五六日天]|星期[一二三四五六日天])$/u.test(prefix[1])) {
      tags.add(prefix[1]);
    }

    if (tags.size === 0 && includesKeyword(entry, keywordSets.meeting)) tags.add("沟通协作");
    return Array.from(tags).slice(0, 3);
  }

  function cleanEntry(entry) {
    return entry.replace(/^(完成|已完成|成果|产出|问题|风险|阻塞|延期|下周|计划|待办|下一步|任务|进展|推进|本周)[：:]\s*/i, "").trim();
  }

  function createItem(entry, index) {
    const status = detectStatus(entry);
    const tags = detectTags(entry);
    const text = cleanEntry(entry);
    return {
      id: `item-${index + 1}`,
      text,
      raw: entry,
      status,
      tags,
      hasOutput: includesKeyword(entry, keywordSets.output),
      hasRisk: includesKeyword(entry, keywordSets.risk),
      hasMetric: /\d+(\.\d+)?\s*(%|个|项|次|份|篇|小时|h|H|天|页|条|人)/.test(entry),
    };
  }

  function uniqueByText(items) {
    const seen = new Set();
    return items.filter((item) => {
      const key = item.text.replace(/\s+/g, "");
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });
  }

  function analyze(rawText) {
    const rawEntries = splitEntries(rawText);
    const items = uniqueByText(rawEntries.map(createItem));
    const tasks = items.filter((item) => item.status !== "planned");
    const completedItems = tasks.filter((item) => item.status === "completed");
    const blockedItems = tasks.filter((item) => item.status === "blocked");
    const outputItems = tasks.filter((item) => item.hasOutput || (item.status === "completed" && item.hasMetric));
    const results = uniqueByText([...outputItems, ...completedItems]).slice(0, 12);
    const issues = blockedItems.slice(0, 12);
    const risks = tasks.filter((item) => item.hasRisk || item.status === "blocked").slice(0, 12);
    const plans = items.filter((item) => item.status === "planned").slice(0, 12);

    const taskTotal = tasks.length;
    const completed = completedItems.length;
    const delayed = blockedItems.length;
    const outputs = outputItems.length || completedItems.filter((item) => item.hasMetric).length;
    const completionRate = taskTotal === 0 ? 0 : Math.round((completed / taskTotal) * 100);
    const focusTags = buildTagSummary(items);

    const kpi = {
      taskTotal,
      completed,
      completionRate,
      delayed,
      outputs,
      issues: issues.length,
      risks: risks.length,
      plans: plans.length,
      meetings: tasks.filter((item) => includesKeyword(item.raw, keywordSets.meeting)).length,
      focusTags,
    };

    return {
      entries: items,
      tasks,
      results,
      issues,
      risks,
      plans,
      kpi,
      summary: buildSummary({ taskTotal, completed, completionRate, delayed, outputs, issues, risks, plans, focusTags }),
    };
  }

  function buildTagSummary(items) {
    const counts = new Map();
    items.forEach((item) => {
      item.tags.forEach((tag) => counts.set(tag, (counts.get(tag) || 0) + 1));
    });
    return Array.from(counts.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5)
      .map(([name, count]) => ({ name, count }));
  }

  function buildSummary({ taskTotal, completed, completionRate, delayed, outputs, issues, risks, plans, focusTags }) {
    const parts = [];
    if (taskTotal > 0) {
      parts.push(`本周共推进 ${taskTotal} 项任务，完成 ${completed} 项，完成率 ${completionRate}%。`);
    } else {
      parts.push("本周暂无可统计任务，建议补充具体动作、结果或计划。");
    }
    if (outputs > 0) parts.push(`形成 ${outputs} 项可交付产出。`);
    if (delayed > 0) parts.push(`存在 ${delayed} 项延期或阻塞，需要优先处理。`);
    if (issues.length > 0 || risks.length > 0) parts.push(`识别到 ${issues.length} 个问题、${risks.length} 个风险点。`);
    if (plans.length > 0) parts.push(`下周计划 ${plans.length} 项。`);
    if (focusTags.length > 0) parts.push(`重点集中在 ${focusTags.map((tag) => tag.name).join("、")}。`);
    return parts.join("");
  }

  function parsePreviousPayload(payload) {
    if (!payload) return null;
    if (typeof payload === "string") {
      try {
        return parsePreviousPayload(JSON.parse(payload));
      } catch (error) {
        return null;
      }
    }
    if (payload.kpi) return payload.kpi;
    return payload;
  }

  function compareKpis(currentKpi, previousPayload) {
    const previous = parsePreviousPayload(previousPayload);
    return metricDefinitions.map((metric) => {
      const current = Number(currentKpi?.[metric.key] || 0);
      const previousValue = previous ? Number(previous[metric.key] || 0) : null;
      const diff = previousValue === null ? null : current - previousValue;
      const trend = diff === null || diff === 0 ? "flat" : diff > 0 ? "up" : "down";
      return {
        ...metric,
        current,
        previous: previousValue,
        diff,
        trend,
        currentLabel: formatMetric(current, metric),
        previousLabel: previousValue === null ? "无" : formatMetric(previousValue, metric),
        diffLabel: diff === null ? "无上周数据" : formatDiff(diff, metric),
      };
    });
  }

  function formatMetric(value, metric) {
    if (metric.type === "rate") return `${Math.round(value)}%`;
    return `${Math.round(value)}${metric.unit}`;
  }

  function formatDiff(value, metric) {
    if (value === 0) return "持平";
    const sign = value > 0 ? "+" : "";
    if (metric.type === "rate") return `${sign}${Math.round(value)}pct`;
    return `${sign}${Math.round(value)}${metric.unit}`;
  }

  function listMarkdown(title, items, fallback) {
    if (!items || items.length === 0) return `## ${title}\n${fallback}\n`;
    return `## ${title}\n${items.map((item) => `- ${item.text}`).join("\n")}\n`;
  }

  function generateMarkdown({ analysis, weekLabel, previousKpi }) {
    const safeWeek = weekLabel || "本周";
    const comparisons = compareKpis(analysis.kpi, previousKpi);
    const kpiTable = [
      "| 指标 | 本周 | 上周 | 环比 |",
      "| --- | ---: | ---: | ---: |",
      ...comparisons.map((row) => `| ${row.label} | ${row.currentLabel} | ${row.previousLabel} | ${row.diffLabel} |`),
    ].join("\n");

    const focusLine =
      analysis.kpi.focusTags.length > 0
        ? analysis.kpi.focusTags.map((tag) => `${tag.name}(${tag.count})`).join("、")
        : "暂无明显主题";

    return [
      `# ${safeWeek} 周报`,
      "",
      "## 一、本周摘要",
      analysis.summary,
      "",
      "## 二、KPI 指标",
      kpiTable,
      "",
      `重点主题：${focusLine}`,
      "",
      listMarkdown("三、主要成果", analysis.results, "- 暂未识别到明确成果，可补充“完成/交付/输出”等描述。"),
      listMarkdown("四、任务进展", analysis.tasks, "- 暂未识别到任务进展。"),
      listMarkdown("五、问题与风险", uniqueByText([...analysis.issues, ...analysis.risks]), "- 暂无明显问题或风险。"),
      listMarkdown("六、下周计划", analysis.plans, "- 暂未识别到下周计划。"),
      "## 七、备注",
      "- 本周报由流水账文本自动结构化生成，建议提交前人工确认关键数字与项目名称。",
    ]
      .join("\n")
      .replace(/\n{3,}/g, "\n\n")
      .trim();
  }

  function buildExportPayload(analysis, weekLabel) {
    return {
      version: 1,
      weekLabel: weekLabel || "本周",
      generatedAt: new Date().toISOString(),
      kpi: analysis.kpi,
      summary: analysis.summary,
      results: analysis.results.map((item) => item.text),
      issues: analysis.issues.map((item) => item.text),
      risks: analysis.risks.map((item) => item.text),
      plans: analysis.plans.map((item) => item.text),
    };
  }

  return {
    analyze,
    buildExportPayload,
    compareKpis,
    generateMarkdown,
    metricDefinitions,
    splitEntries,
  };
});
