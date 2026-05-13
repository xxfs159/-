const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => Array.from(document.querySelectorAll(selector));

const state = {
  analysis: null,
  previousKpi: null,
  markdown: "",
};

const sampleText = `周一：完成周报机器人需求拆解，整理出流水账输入、KPI 自动统计、Markdown 输出三个核心模块。
周二：实现文本解析脚本，完成 12 条测试日志的任务/问题/计划分类。
周三：输出可视化原型，完成任务分布图、完成率环比图和 Markdown 预览。
周四：修复导入上周 JSON 时完成率显示异常的问题，补充错误提示。
周五：和小组同步展示方案，确认答辩时演示“粘贴流水账到生成周报”的完整流程。
问题：语音识别在部分浏览器上不可用，需要提供文本导入兜底。
风险：如果原始记录过短，自动 KPI 统计会偏少，需要在界面提示补充具体动作和结果。
下周：接入 DeepSeek/Coze 工作流做语言润色，并增加一键复制到飞书的格式适配。
下周：准备海报中的系统架构图、核心算法流程和演示截图。`;

const defaultPreviousKpi = {
  taskTotal: 7,
  completed: 4,
  completionRate: 57,
  delayed: 2,
  outputs: 3,
  issues: 2,
  risks: 1,
  plans: 4,
};

function init() {
  $("#weekLabel").value = getDefaultWeekLabel();
  $("#rawInput").value = sampleText;
  state.previousKpi = defaultPreviousKpi;

  $("#analyzeBtn").addEventListener("click", analyzeAndRender);
  $("#sampleBtn").addEventListener("click", () => {
    $("#rawInput").value = sampleText;
    analyzeAndRender();
  });
  $("#clearBtn").addEventListener("click", clearWorkspace);
  $("#copyBtn").addEventListener("click", copyMarkdown);
  $("#downloadBtn").addEventListener("click", downloadMarkdown);
  $("#exportJsonBtn").addEventListener("click", exportCurrentJson);
  $("#importLog").addEventListener("change", importLogFile);
  $("#importPrevious").addEventListener("change", importPreviousFile);
  $("#voiceBtn").addEventListener("click", startVoiceInput);
  $("#promptBtn").addEventListener("click", copyPolishPrompt);

  analyzeAndRender();
}

function getDefaultWeekLabel() {
  const now = new Date();
  const firstDay = new Date(now.getFullYear(), 0, 1);
  const pastDays = Math.floor((now - firstDay) / 86400000);
  const week = Math.ceil((pastDays + firstDay.getDay() + 1) / 7);
  return `${now.getFullYear()} 年第 ${week} 周`;
}

function analyzeAndRender() {
  const rawText = $("#rawInput").value;
  state.analysis = ReportEngine.analyze(rawText);
  state.markdown = ReportEngine.generateMarkdown({
    analysis: state.analysis,
    weekLabel: $("#weekLabel").value,
    previousKpi: state.previousKpi,
  });
  renderAll();
}

function renderAll() {
  renderKpis();
  renderDistribution();
  renderComparison();
  renderLists();
  $("#markdownOutput").value = state.markdown;
  $("#summaryText").textContent = state.analysis.summary;
  $("#entryCount").textContent = `${state.analysis.entries.length} 条记录`;
}

function renderKpis() {
  const wrap = $("#kpiGrid");
  const comparisons = ReportEngine.compareKpis(state.analysis.kpi, state.previousKpi);
  wrap.innerHTML = comparisons
    .slice(0, 6)
    .map(
      (item) => `
        <article class="metric-card">
          <span>${item.label}</span>
          <strong>${item.currentLabel}</strong>
          <small class="${item.trend}">${item.diffLabel}</small>
        </article>
      `,
    )
    .join("");
}

function renderDistribution() {
  const data = [
    ["完成", state.analysis.kpi.completed, "var(--green)"],
    ["推进中", Math.max(state.analysis.kpi.taskTotal - state.analysis.kpi.completed - state.analysis.kpi.delayed, 0), "var(--blue)"],
    ["阻塞", state.analysis.kpi.delayed, "var(--red)"],
    ["计划", state.analysis.kpi.plans, "var(--amber)"],
  ];
  const max = Math.max(...data.map((row) => row[1]), 1);
  $("#distributionChart").innerHTML = data
    .map((row) => {
      const width = Math.max((row[1] / max) * 100, row[1] > 0 ? 8 : 0);
      return `
        <div class="bar-row">
          <span>${row[0]}</span>
          <div class="bar-track"><i style="width:${width}%;background:${row[2]}"></i></div>
          <b>${row[1]}</b>
        </div>
      `;
    })
    .join("");
}

function renderComparison() {
  const comparisons = ReportEngine.compareKpis(state.analysis.kpi, state.previousKpi);
  $("#comparisonTable").innerHTML = `
    <table>
      <thead>
        <tr><th>指标</th><th>本周</th><th>上周</th><th>环比</th></tr>
      </thead>
      <tbody>
        ${comparisons
          .map(
            (row) =>
              `<tr><td>${row.label}</td><td>${row.currentLabel}</td><td>${row.previousLabel}</td><td class="${row.trend}">${row.diffLabel}</td></tr>`,
          )
          .join("")}
      </tbody>
    </table>
  `;
}

function renderLists() {
  renderList("#resultList", state.analysis.results, "暂无明确成果");
  renderList("#issueList", [...state.analysis.issues, ...state.analysis.risks], "暂无明显问题");
  renderList("#planList", state.analysis.plans, "暂无下周计划");
}

function renderList(selector, items, fallback) {
  const target = $(selector);
  if (!items.length) {
    target.innerHTML = `<li class="muted">${fallback}</li>`;
    return;
  }
  target.innerHTML = items.slice(0, 6).map((item) => `<li>${item.text}</li>`).join("");
}

async function copyMarkdown() {
  if (!state.markdown) analyzeAndRender();
  await navigator.clipboard.writeText(state.markdown);
  flash("#copyBtn", "已复制");
}

function copyPolishPrompt() {
  const prompt = [
    "请把下面的自动周报润色成正式、简洁、适合发到飞书/钉钉/企业微信的 Markdown 周报。",
    "要求：保留 KPI 表格；不要虚构事实；问题与风险要写出下一步动作；语气专业。",
    "",
    state.markdown,
  ].join("\n");
  navigator.clipboard.writeText(prompt);
  flash("#promptBtn", "Prompt 已复制");
}

function downloadMarkdown() {
  downloadText(`${safeFileName($("#weekLabel").value)}-weekly-report.md`, state.markdown, "text/markdown;charset=utf-8");
}

function exportCurrentJson() {
  if (!state.analysis) analyzeAndRender();
  const payload = ReportEngine.buildExportPayload(state.analysis, $("#weekLabel").value);
  downloadText(`${safeFileName($("#weekLabel").value)}-kpi.json`, JSON.stringify(payload, null, 2), "application/json;charset=utf-8");
}

function downloadText(filename, content, type) {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

function safeFileName(name) {
  return String(name || "weekly-report").replace(/[\\/:*?"<>|\s]+/g, "-").replace(/^-+|-+$/g, "");
}

function importLogFile(event) {
  const file = event.target.files[0];
  if (!file) return;
  readFile(file).then((text) => {
    $("#rawInput").value = text;
    analyzeAndRender();
  });
}

function importPreviousFile(event) {
  const file = event.target.files[0];
  if (!file) return;
  readFile(file).then((text) => {
    try {
      state.previousKpi = JSON.parse(text).kpi || JSON.parse(text);
      analyzeAndRender();
      flashLabel("#previousStatus", "已导入上周 KPI");
    } catch (error) {
      flashLabel("#previousStatus", "JSON 格式无效");
    }
  });
}

function readFile(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = reject;
    reader.readAsText(file, "utf-8");
  });
}

function clearWorkspace() {
  $("#rawInput").value = "";
  state.previousKpi = null;
  analyzeAndRender();
}

function startVoiceInput() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    flashLabel("#voiceStatus", "当前浏览器不支持语音识别，请导入转写文本");
    return;
  }
  const recognition = new SpeechRecognition();
  recognition.lang = "zh-CN";
  recognition.continuous = true;
  recognition.interimResults = false;
  recognition.onstart = () => flashLabel("#voiceStatus", "正在听写");
  recognition.onerror = () => flashLabel("#voiceStatus", "语音识别失败");
  recognition.onresult = (event) => {
    const transcript = Array.from(event.results)
      .map((result) => result[0].transcript)
      .join("\n");
    $("#rawInput").value = `${$("#rawInput").value}\n${transcript}`.trim();
    analyzeAndRender();
    flashLabel("#voiceStatus", "已写入文本框");
  };
  recognition.onend = () => setTimeout(() => flashLabel("#voiceStatus", "语音输入"), 1200);
  recognition.start();
}

function flash(selector, label) {
  const element = $(selector);
  const old = element.textContent;
  element.textContent = label;
  setTimeout(() => {
    element.textContent = old;
  }, 1200);
}

function flashLabel(selector, text) {
  const element = $(selector);
  element.textContent = text;
}

document.addEventListener("DOMContentLoaded", init);
