import { useState, useEffect, useRef } from "react";
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, RadarChart, Radar, PolarGrid, PolarAngleAxis, Cell } from "recharts";

const COLORS = { blue: "#378ADD", teal: "#1D9E75", amber: "#BA7517", coral: "#D85A30", purple: "#7F77DD", green: "#639922" };
const SUBJECTS = ["数学", "英语", "物理", "化学", "语文", "历史", "生物", "计算机"];

const initialSessions = [
  { id: 1, subject: "数学", duration: 90, date: "2025-10-08", type: "练习", accuracy: 85, notes: "二次函数" },
  { id: 2, subject: "英语", duration: 60, date: "2025-10-09", type: "背诵", accuracy: 78, notes: "词汇" },
  { id: 3, subject: "物理", duration: 75, date: "2025-10-10", type: "刷题", accuracy: 72, notes: "力学" },
  { id: 4, subject: "数学", duration: 120, date: "2025-10-11", type: "练习", accuracy: 88, notes: "微积分" },
  { id: 5, subject: "英语", duration: 45, date: "2025-10-12", type: "阅读", accuracy: 82, notes: "完形填空" },
  { id: 6, subject: "化学", duration: 60, date: "2025-10-14", type: "刷题", accuracy: 65, notes: "有机化学" },
  { id: 7, subject: "物理", duration: 90, date: "2025-10-15", type: "复习", accuracy: 80, notes: "电磁学" },
  { id: 8, subject: "数学", duration: 100, date: "2025-10-16", type: "练习", accuracy: 91, notes: "概率统计" },
  { id: 9, subject: "化学", duration: 50, date: "2025-10-18", type: "刷题", accuracy: 68, notes: "化学键" },
  { id: 10, subject: "语文", duration: 70, date: "2025-10-19", type: "写作", accuracy: 75, notes: "作文" },
  { id: 11, subject: "英语", duration: 80, date: "2025-10-21", type: "练习", accuracy: 84, notes: "语法" },
  { id: 12, subject: "物理", duration: 65, date: "2025-10-22", type: "刷题", accuracy: 76, notes: "光学" },
  { id: 13, subject: "数学", duration: 110, date: "2025-10-24", type: "练习", accuracy: 93, notes: "向量" },
  { id: 14, subject: "化学", duration: 55, date: "2025-10-25", type: "复习", accuracy: 70, notes: "反应速率" },
  { id: 15, subject: "英语", duration: 60, date: "2025-10-26", type: "听力", accuracy: 79, notes: "听力训练" },
];

function callClaude(messages, systemPrompt) {
  return fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      model: "claude-sonnet-4-20250514",
      max_tokens: 1000,
      system: systemPrompt,
      messages
    })
  }).then(r => r.json()).then(d => d.content?.map(c => c.text || "").join("") || "");
}

function StatCard({ label, value, sub, color }) {
  return (
    <div style={{ background: "var(--color-background-secondary)", borderRadius: "var(--border-radius-md)", padding: "14px 16px", flex: 1, minWidth: 0 }}>
      <div style={{ fontSize: 12, color: "var(--color-text-secondary)", marginBottom: 4 }}>{label}</div>
      <div style={{ fontSize: 22, fontWeight: 500, color: color || "var(--color-text-primary)" }}>{value}</div>
      {sub && <div style={{ fontSize: 11, color: "var(--color-text-tertiary)", marginTop: 2 }}>{sub}</div>}
    </div>
  );
}

function SubjectTag({ subject }) {
  const colorMap = { "数学": COLORS.blue, "英语": COLORS.teal, "物理": COLORS.purple, "化学": COLORS.coral, "语文": COLORS.amber, "历史": COLORS.green, "生物": "#1D9E75", "计算机": "#D4537E" };
  const c = colorMap[subject] || COLORS.blue;
  return <span style={{ fontSize: 11, padding: "2px 8px", borderRadius: 20, background: c + "22", color: c, fontWeight: 500 }}>{subject}</span>;
}

export default function StudyTracker() {
  const [tab, setTab] = useState("dashboard");
  const [sessions, setSessions] = useState(initialSessions);
  const [chatMessages, setChatMessages] = useState([{ role: "assistant", content: "你好！我是你的学习档案AI助手。你可以问我关于学习进度、薄弱知识点、学习建议等任何问题。" }]);
  const [chatInput, setChatInput] = useState("");
  const [chatLoading, setChatLoading] = useState(false);
  const [report, setReport] = useState("");
  const [reportLoading, setReportLoading] = useState(false);
  const [form, setForm] = useState({ subject: "数学", duration: "", type: "练习", accuracy: "", notes: "", date: new Date().toISOString().slice(0, 10) });
  const chatEndRef = useRef(null);

  useEffect(() => { chatEndRef.current?.scrollIntoView({ behavior: "smooth" }); }, [chatMessages]);

  const totalMinutes = sessions.reduce((s, x) => s + x.duration, 0);
  const avgAccuracy = Math.round(sessions.reduce((s, x) => s + x.accuracy, 0) / sessions.length);
  const subjectMap = {};
  sessions.forEach(s => {
    if (!subjectMap[s.subject]) subjectMap[s.subject] = { total: 0, count: 0, accuracy: 0 };
    subjectMap[s.subject].total += s.duration;
    subjectMap[s.subject].count++;
    subjectMap[s.subject].accuracy += s.accuracy;
  });
  const subjectStats = Object.entries(subjectMap).map(([name, v]) => ({
    name, total: v.total, count: v.count, avg: Math.round(v.accuracy / v.count)
  })).sort((a, b) => a.avg - b.avg);
  const weakSubjects = subjectStats.slice(0, 2);

  const trendData = sessions.slice(-8).map((s, i) => ({
    date: s.date.slice(5), accuracy: s.accuracy, duration: Math.round(s.duration / 10)
  }));

  const radarData = subjectStats.map(s => ({ subject: s.name, accuracy: s.avg }));

  function addSession() {
    if (!form.duration || !form.accuracy) return;
    setSessions(prev => [...prev, { ...form, id: Date.now(), duration: +form.duration, accuracy: +form.accuracy }]);
    setForm(f => ({ ...f, duration: "", accuracy: "", notes: "" }));
  }

  async function sendChat() {
    if (!chatInput.trim() || chatLoading) return;
    const userMsg = chatInput.trim();
    setChatInput("");
    const newMsgs = [...chatMessages, { role: "user", content: userMsg }];
    setChatMessages(newMsgs);
    setChatLoading(true);
    const statsStr = JSON.stringify(subjectStats);
    const recentStr = JSON.stringify(sessions.slice(-5));
    const system = `你是一个学习档案AI助手。用户的学习数据如下：
总学习时长：${totalMinutes}分钟，平均正确率：${avgAccuracy}%
各科目统计：${statsStr}
最近学习记录：${recentStr}
薄弱科目：${weakSubjects.map(s => s.name).join("、")}
请根据数据给出具体、有针对性的回答。回答简洁、实用，不超过200字。`;
    try {
      const reply = await callClaude(newMsgs.map(m => ({ role: m.role, content: m.content })), system);
      setChatMessages(prev => [...prev, { role: "assistant", content: reply }]);
    } catch { setChatMessages(prev => [...prev, { role: "assistant", content: "抱歉，AI服务暂时不可用，请稍后再试。" }]); }
    setChatLoading(false);
  }

  async function generateReport() {
    setReportLoading(true);
    setReport("");
    const system = `你是一个学习周报生成AI。请基于以下数据生成一份结构化的学习周报。
格式：
## 📊 本周学习总结
## 🎯 各科目表现分析
## ⚠️ 薄弱知识点诊断
## 💡 学习习惯问题
## 📅 下周学习计划建议
用中文，简洁专业，每个章节3-5句话。`;
    const content = `总学习时长：${totalMinutes}分钟，总学习次数：${sessions.length}次，平均正确率：${avgAccuracy}%
各科目：${JSON.stringify(subjectStats)}
最近记录：${JSON.stringify(sessions.slice(-6))}`;
    try {
      const r = await callClaude([{ role: "user", content }], system);
      setReport(r);
    } catch { setReport("AI服务暂时不可用，请稍后再试。"); }
    setReportLoading(false);
  }

  const tabs = [
    { id: "dashboard", icon: "ti-layout-dashboard", label: "仪表盘" },
    { id: "input", icon: "ti-edit", label: "记录学习" },
    { id: "analysis", icon: "ti-chart-bar", label: "数据分析" },
    { id: "report", icon: "ti-report-analytics", label: "AI周报" },
    { id: "chat", icon: "ti-message-circle-2", label: "AI问答" },
  ];

  return (
    <div style={{ fontFamily: "var(--font-sans)", maxWidth: 700, margin: "0 auto", padding: "0 0 2rem" }}>
      <h2 className="sr-only">个人学习档案AI助手</h2>

      {/* Header */}
      <div style={{ padding: "1.25rem 0 0.75rem", borderBottom: "0.5px solid var(--color-border-tertiary)", marginBottom: "0.75rem" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{ width: 32, height: 32, borderRadius: 8, background: COLORS.blue + "22", display: "flex", alignItems: "center", justifyContent: "center" }}>
            <i className="ti ti-brain" style={{ fontSize: 18, color: COLORS.blue }} aria-hidden />
          </div>
          <div>
            <div style={{ fontSize: 16, fontWeight: 500, color: "var(--color-text-primary)" }}>个人学习档案 AI 助手</div>
            <div style={{ fontSize: 12, color: "var(--color-text-secondary)" }}>AI-Powered Personal Study Tracker</div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display: "flex", gap: 4, marginBottom: "1rem", overflowX: "auto" }}>
        {tabs.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)} style={{
            display: "flex", alignItems: "center", gap: 5, padding: "6px 12px", borderRadius: "var(--border-radius-md)",
            border: tab === t.id ? `0.5px solid ${COLORS.blue}` : "0.5px solid var(--color-border-tertiary)",
            background: tab === t.id ? COLORS.blue + "18" : "transparent",
            color: tab === t.id ? COLORS.blue : "var(--color-text-secondary)",
            fontSize: 13, fontWeight: tab === t.id ? 500 : 400, cursor: "pointer", whiteSpace: "nowrap"
          }}>
            <i className={`ti ${t.icon}`} style={{ fontSize: 14 }} aria-hidden />
            {t.label}
          </button>
        ))}
      </div>

      {/* DASHBOARD */}
      {tab === "dashboard" && (
        <div>
          <div style={{ display: "flex", gap: 10, marginBottom: 12, flexWrap: "wrap" }}>
            <StatCard label="总学习时长" value={`${Math.floor(totalMinutes / 60)}h ${totalMinutes % 60}m`} sub="累计学习时间" color={COLORS.blue} />
            <StatCard label="学习次数" value={sessions.length} sub="总记录次数" color={COLORS.teal} />
            <StatCard label="平均正确率" value={`${avgAccuracy}%`} sub="综合学习效率" color={avgAccuracy >= 80 ? COLORS.green : COLORS.amber} />
            <StatCard label="科目数量" value={Object.keys(subjectMap).length} sub="已覆盖科目" color={COLORS.purple} />
          </div>

          <div style={{ background: "var(--color-background-primary)", border: "0.5px solid var(--color-border-tertiary)", borderRadius: "var(--border-radius-lg)", padding: "1rem 1.25rem", marginBottom: 12 }}>
            <div style={{ fontSize: 13, fontWeight: 500, marginBottom: 10, color: "var(--color-text-primary)" }}>近期学习趋势</div>
            <ResponsiveContainer width="100%" height={160}>
              <LineChart data={trendData} margin={{ top: 4, right: 8, bottom: 4, left: 0 }}>
                <XAxis dataKey="date" tick={{ fontSize: 10, fill: "#888" }} />
                <YAxis domain={[50, 100]} tick={{ fontSize: 10, fill: "#888" }} />
                <Tooltip contentStyle={{ fontSize: 12, borderRadius: 8, border: "0.5px solid var(--color-border-secondary)" }} />
                <Line type="monotone" dataKey="accuracy" stroke={COLORS.blue} strokeWidth={2} dot={{ r: 3 }} name="正确率%" />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div style={{ background: "var(--color-background-primary)", border: "0.5px solid var(--color-border-tertiary)", borderRadius: "var(--border-radius-lg)", padding: "1rem 1.25rem", marginBottom: 12 }}>
            <div style={{ fontSize: 13, fontWeight: 500, marginBottom: 4, color: "var(--color-text-primary)" }}>薄弱知识点预警</div>
            {weakSubjects.map(s => (
              <div key={s.name} style={{ display: "flex", alignItems: "center", gap: 10, padding: "8px 0", borderBottom: "0.5px solid var(--color-border-tertiary)" }}>
                <i className="ti ti-alert-triangle" style={{ fontSize: 16, color: COLORS.amber }} aria-hidden />
                <SubjectTag subject={s.name} />
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 12, color: "var(--color-text-secondary)" }}>平均正确率偏低，建议加强练习</div>
                </div>
                <div style={{ fontSize: 16, fontWeight: 500, color: COLORS.coral }}>{s.avg}%</div>
              </div>
            ))}
          </div>

          <div style={{ background: "var(--color-background-primary)", border: "0.5px solid var(--color-border-tertiary)", borderRadius: "var(--border-radius-lg)", padding: "1rem 1.25rem" }}>
            <div style={{ fontSize: 13, fontWeight: 500, marginBottom: 8, color: "var(--color-text-primary)" }}>最近学习记录</div>
            {sessions.slice(-5).reverse().map(s => (
              <div key={s.id} style={{ display: "flex", alignItems: "center", gap: 10, padding: "7px 0", borderBottom: "0.5px solid var(--color-border-tertiary)" }}>
                <SubjectTag subject={s.subject} />
                <div style={{ flex: 1, fontSize: 12, color: "var(--color-text-secondary)" }}>{s.notes || s.type}</div>
                <div style={{ fontSize: 12, color: "var(--color-text-tertiary)" }}>{s.duration}分钟</div>
                <div style={{ fontSize: 12, fontWeight: 500, color: s.accuracy >= 80 ? COLORS.green : COLORS.amber }}>{s.accuracy}%</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* INPUT */}
      {tab === "input" && (
        <div>
          <div style={{ background: "var(--color-background-primary)", border: "0.5px solid var(--color-border-tertiary)", borderRadius: "var(--border-radius-lg)", padding: "1.25rem" }}>
            <div style={{ fontSize: 14, fontWeight: 500, marginBottom: 16 }}>添加学习记录</div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 12 }}>
              <div>
                <label style={{ fontSize: 12, color: "var(--color-text-secondary)", display: "block", marginBottom: 4 }}>科目</label>
                <select value={form.subject} onChange={e => setForm(f => ({ ...f, subject: e.target.value }))} style={{ width: "100%" }}>
                  {SUBJECTS.map(s => <option key={s}>{s}</option>)}
                </select>
              </div>
              <div>
                <label style={{ fontSize: 12, color: "var(--color-text-secondary)", display: "block", marginBottom: 4 }}>学习类型</label>
                <select value={form.type} onChange={e => setForm(f => ({ ...f, type: e.target.value }))} style={{ width: "100%" }}>
                  {["练习", "刷题", "复习", "背诵", "阅读", "听力", "写作"].map(t => <option key={t}>{t}</option>)}
                </select>
              </div>
              <div>
                <label style={{ fontSize: 12, color: "var(--color-text-secondary)", display: "block", marginBottom: 4 }}>学习时长（分钟）</label>
                <input type="number" value={form.duration} onChange={e => setForm(f => ({ ...f, duration: e.target.value }))} placeholder="例如：60" style={{ width: "100%" }} />
              </div>
              <div>
                <label style={{ fontSize: 12, color: "var(--color-text-secondary)", display: "block", marginBottom: 4 }}>正确率（%）</label>
                <input type="number" value={form.accuracy} onChange={e => setForm(f => ({ ...f, accuracy: e.target.value }))} placeholder="0-100" min={0} max={100} style={{ width: "100%" }} />
              </div>
              <div>
                <label style={{ fontSize: 12, color: "var(--color-text-secondary)", display: "block", marginBottom: 4 }}>日期</label>
                <input type="date" value={form.date} onChange={e => setForm(f => ({ ...f, date: e.target.value }))} style={{ width: "100%" }} />
              </div>
              <div>
                <label style={{ fontSize: 12, color: "var(--color-text-secondary)", display: "block", marginBottom: 4 }}>学习笔记（可选）</label>
                <input type="text" value={form.notes} onChange={e => setForm(f => ({ ...f, notes: e.target.value }))} placeholder="知识点、备注..." style={{ width: "100%" }} />
              </div>
            </div>
            <button onClick={addSession} style={{ width: "100%", padding: "8px", fontSize: 13, background: COLORS.blue, color: "#fff", border: "none", borderRadius: "var(--border-radius-md)", cursor: "pointer", fontWeight: 500 }}>
              <i className="ti ti-plus" style={{ marginRight: 4 }} aria-hidden /> 添加记录
            </button>
          </div>

          <div style={{ background: "var(--color-background-primary)", border: "0.5px solid var(--color-border-tertiary)", borderRadius: "var(--border-radius-lg)", padding: "1.25rem", marginTop: 12 }}>
            <div style={{ fontSize: 14, fontWeight: 500, marginBottom: 12 }}>历史记录（共 {sessions.length} 条）</div>
            <div style={{ maxHeight: 320, overflowY: "auto" }}>
              {sessions.slice().reverse().map(s => (
                <div key={s.id} style={{ display: "flex", alignItems: "center", gap: 10, padding: "8px 0", borderBottom: "0.5px solid var(--color-border-tertiary)" }}>
                  <SubjectTag subject={s.subject} />
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 12, color: "var(--color-text-primary)" }}>{s.type} · {s.notes || "-"}</div>
                    <div style={{ fontSize: 11, color: "var(--color-text-tertiary)" }}>{s.date}</div>
                  </div>
                  <div style={{ fontSize: 12, color: "var(--color-text-secondary)" }}>{s.duration}分</div>
                  <div style={{ fontSize: 13, fontWeight: 500, color: s.accuracy >= 80 ? COLORS.green : COLORS.amber }}>{s.accuracy}%</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ANALYSIS */}
      {tab === "analysis" && (
        <div>
          <div style={{ background: "var(--color-background-primary)", border: "0.5px solid var(--color-border-tertiary)", borderRadius: "var(--border-radius-lg)", padding: "1rem 1.25rem", marginBottom: 12 }}>
            <div style={{ fontSize: 13, fontWeight: 500, marginBottom: 10 }}>各科目平均正确率</div>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={subjectStats} layout="vertical" margin={{ top: 0, right: 16, bottom: 0, left: 8 }}>
                <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 10, fill: "#888" }} />
                <YAxis type="category" dataKey="name" tick={{ fontSize: 11, fill: "#888" }} width={36} />
                <Tooltip formatter={v => [`${v}%`, "正确率"]} contentStyle={{ fontSize: 12, borderRadius: 8 }} />
                <Bar dataKey="avg" radius={[0, 4, 4, 0]}>
                  {subjectStats.map((s, i) => <Cell key={i} fill={s.avg < 75 ? COLORS.coral : s.avg < 85 ? COLORS.amber : COLORS.teal} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div style={{ background: "var(--color-background-primary)", border: "0.5px solid var(--color-border-tertiary)", borderRadius: "var(--border-radius-lg)", padding: "1rem 1.25rem", marginBottom: 12 }}>
            <div style={{ fontSize: 13, fontWeight: 500, marginBottom: 10 }}>科目能力雷达图</div>
            <ResponsiveContainer width="100%" height={200}>
              <RadarChart data={radarData}>
                <PolarGrid stroke="var(--color-border-tertiary)" />
                <PolarAngleAxis dataKey="subject" tick={{ fontSize: 11 }} />
                <Radar dataKey="accuracy" stroke={COLORS.blue} fill={COLORS.blue} fillOpacity={0.2} />
              </RadarChart>
            </ResponsiveContainer>
          </div>

          <div style={{ background: "var(--color-background-primary)", border: "0.5px solid var(--color-border-tertiary)", borderRadius: "var(--border-radius-lg)", padding: "1rem 1.25rem" }}>
            <div style={{ fontSize: 13, fontWeight: 500, marginBottom: 12 }}>学习时长分配</div>
            <ResponsiveContainer width="100%" height={160}>
              <BarChart data={subjectStats.slice().sort((a, b) => b.total - a.total)}>
                <XAxis dataKey="name" tick={{ fontSize: 11, fill: "#888" }} />
                <YAxis tick={{ fontSize: 10, fill: "#888" }} />
                <Tooltip formatter={v => [`${v}分钟`, "学习时长"]} contentStyle={{ fontSize: 12, borderRadius: 8 }} />
                <Bar dataKey="total" fill={COLORS.purple} radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div style={{ background: "var(--color-background-primary)", border: "0.5px solid var(--color-border-tertiary)", borderRadius: "var(--border-radius-lg)", padding: "1rem 1.25rem", marginTop: 12 }}>
            <div style={{ fontSize: 13, fontWeight: 500, marginBottom: 10 }}>薄弱点诊断报告</div>
            {subjectStats.filter(s => s.avg < 80).map(s => (
              <div key={s.name} style={{ padding: "10px 12px", borderRadius: "var(--border-radius-md)", background: COLORS.coral + "12", border: `0.5px solid ${COLORS.coral}44`, marginBottom: 8 }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <SubjectTag subject={s.name} />
                  <span style={{ fontSize: 13, fontWeight: 500, color: COLORS.coral }}>{s.avg}%</span>
                </div>
                <div style={{ fontSize: 12, color: "var(--color-text-secondary)", marginTop: 4 }}>
                  已学习 {s.count} 次，共 {s.total} 分钟。正确率低于平均水平，建议增加针对性练习，重点攻克薄弱知识点。
                </div>
              </div>
            ))}
            {subjectStats.filter(s => s.avg >= 80).map(s => (
              <div key={s.name} style={{ padding: "10px 12px", borderRadius: "var(--border-radius-md)", background: COLORS.green + "12", border: `0.5px solid ${COLORS.green}44`, marginBottom: 8 }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <SubjectTag subject={s.name} />
                  <span style={{ fontSize: 13, fontWeight: 500, color: COLORS.green }}>{s.avg}% ✓</span>
                </div>
                <div style={{ fontSize: 12, color: "var(--color-text-secondary)", marginTop: 4 }}>
                  表现良好，保持当前学习节奏即可。
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* AI REPORT */}
      {tab === "report" && (
        <div>
          <div style={{ background: "var(--color-background-primary)", border: "0.5px solid var(--color-border-tertiary)", borderRadius: "var(--border-radius-lg)", padding: "1.25rem", marginBottom: 12 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
              <i className="ti ti-sparkles" style={{ fontSize: 18, color: COLORS.purple }} aria-hidden />
              <div style={{ fontSize: 14, fontWeight: 500 }}>AI 学习周报生成</div>
            </div>
            <div style={{ fontSize: 13, color: "var(--color-text-secondary)", marginBottom: 16, lineHeight: 1.7 }}>
              AI 将基于你的 {sessions.length} 条学习记录，自动生成包含学习总结、薄弱点诊断、学习习惯分析和下周计划建议的个性化周报。
            </div>
            <div style={{ display: "flex", gap: 10, marginBottom: 12 }}>
              <StatCard label="分析记录" value={sessions.length} color={COLORS.blue} />
              <StatCard label="覆盖科目" value={Object.keys(subjectMap).length} color={COLORS.teal} />
              <StatCard label="综合正确率" value={`${avgAccuracy}%`} color={avgAccuracy >= 80 ? COLORS.green : COLORS.amber} />
            </div>
            <button onClick={generateReport} disabled={reportLoading} style={{
              width: "100%", padding: "9px", fontSize: 13, fontWeight: 500,
              background: reportLoading ? "var(--color-background-secondary)" : COLORS.purple,
              color: reportLoading ? "var(--color-text-secondary)" : "#fff",
              border: "none", borderRadius: "var(--border-radius-md)", cursor: reportLoading ? "default" : "pointer"
            }}>
              {reportLoading ? <><i className="ti ti-loader-2" style={{ marginRight: 4 }} aria-hidden /> 生成中...</> : <><i className="ti ti-sparkles" style={{ marginRight: 4 }} aria-hidden /> 生成本周AI学习周报</>}
            </button>
          </div>

          {report && (
            <div style={{ background: "var(--color-background-primary)", border: "0.5px solid var(--color-border-tertiary)", borderRadius: "var(--border-radius-lg)", padding: "1.25rem" }}>
              <div style={{ fontSize: 13, color: "var(--color-text-primary)", lineHeight: 1.9, whiteSpace: "pre-wrap" }}>{report}</div>
            </div>
          )}
        </div>
      )}

      {/* CHAT */}
      {tab === "chat" && (
        <div>
          <div style={{ background: "var(--color-background-primary)", border: "0.5px solid var(--color-border-tertiary)", borderRadius: "var(--border-radius-lg)", overflow: "hidden" }}>
            <div style={{ padding: "10px 14px", borderBottom: "0.5px solid var(--color-border-tertiary)", display: "flex", alignItems: "center", gap: 6 }}>
              <i className="ti ti-robot" style={{ fontSize: 15, color: COLORS.teal }} aria-hidden />
              <span style={{ fontSize: 13, fontWeight: 500 }}>学习档案AI问答</span>
              <span style={{ fontSize: 11, color: "var(--color-text-tertiary)", marginLeft: 4 }}>基于你的真实学习数据</span>
            </div>

            <div style={{ height: 340, overflowY: "auto", padding: "12px 14px", display: "flex", flexDirection: "column", gap: 12 }}>
              {chatMessages.map((m, i) => (
                <div key={i} style={{ display: "flex", justifyContent: m.role === "user" ? "flex-end" : "flex-start" }}>
                  <div style={{
                    maxWidth: "80%", padding: "8px 12px", borderRadius: m.role === "user" ? "12px 12px 2px 12px" : "12px 12px 12px 2px",
                    background: m.role === "user" ? COLORS.blue : "var(--color-background-secondary)",
                    color: m.role === "user" ? "#fff" : "var(--color-text-primary)",
                    fontSize: 13, lineHeight: 1.6
                  }}>
                    {m.content}
                  </div>
                </div>
              ))}
              {chatLoading && (
                <div style={{ display: "flex", justifyContent: "flex-start" }}>
                  <div style={{ padding: "8px 12px", borderRadius: "12px 12px 12px 2px", background: "var(--color-background-secondary)", fontSize: 13, color: "var(--color-text-secondary)" }}>
                    <i className="ti ti-dots" aria-hidden /> 思考中...
                  </div>
                </div>
              )}
              <div ref={chatEndRef} />
            </div>

            <div style={{ padding: "0 12px 8px", borderTop: "0.5px solid var(--color-border-tertiary)", marginTop: 4 }}>
              <div style={{ display: "flex", gap: 6, marginBottom: 8, marginTop: 8, flexWrap: "wrap" }}>
                {["我的薄弱科目是哪些？", "本周学习效率如何？", "给我制定下周计划"].map(q => (
                  <button key={q} onClick={() => setChatInput(q)} style={{
                    fontSize: 11, padding: "3px 10px", borderRadius: 20,
                    border: "0.5px solid var(--color-border-secondary)", background: "transparent",
                    color: "var(--color-text-secondary)", cursor: "pointer"
                  }}>{q}</button>
                ))}
              </div>
              <div style={{ display: "flex", gap: 8 }}>
                <input
                  value={chatInput}
                  onChange={e => setChatInput(e.target.value)}
                  onKeyDown={e => e.key === "Enter" && sendChat()}
                  placeholder="问我关于你的学习情况..."
                  style={{ flex: 1, fontSize: 13 }}
                />
                <button onClick={sendChat} disabled={chatLoading || !chatInput.trim()} style={{
                  padding: "7px 14px", fontSize: 13, fontWeight: 500,
                  background: chatInput.trim() ? COLORS.teal : "var(--color-background-secondary)",
                  color: chatInput.trim() ? "#fff" : "var(--color-text-tertiary)",
                  border: "none", borderRadius: "var(--border-radius-md)", cursor: "pointer"
                }}>
                  发送
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
