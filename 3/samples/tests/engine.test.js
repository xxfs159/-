const assert = require("node:assert/strict");
const engine = require("../engine.js");

const log = `
完成：实现 Markdown 周报生成，输出 1 份演示报告。
完成：修复 KPI 完成率计算异常。
推进：设计任务分布可视化。
问题：语音识别在当前浏览器不可用。
风险：日志过短时可能导致 KPI 统计偏少。
下周：接入 DeepSeek 润色工作流。
`;

const analysis = engine.analyze(log);

assert.equal(analysis.kpi.taskTotal, 5);
assert.equal(analysis.kpi.completed, 2);
assert.equal(analysis.kpi.completionRate, 40);
assert.equal(analysis.kpi.delayed, 2);
assert.equal(analysis.kpi.plans, 1);
assert.ok(analysis.results.length >= 2);
assert.ok(analysis.issues.length >= 1);
assert.ok(analysis.risks.length >= 1);

const markdown = engine.generateMarkdown({
  analysis,
  weekLabel: "测试周",
  previousKpi: { taskTotal: 4, completed: 1, completionRate: 25, delayed: 1, outputs: 1, issues: 1, risks: 1, plans: 0 },
});

assert.match(markdown, /# 测试周 周报/);
assert.match(markdown, /\| 完成率 \| 40% \| 25% \| \+15pct \|/);
assert.match(markdown, /Markdown 周报生成/);

console.log("engine tests passed");
