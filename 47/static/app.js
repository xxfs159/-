const CODE_EXTENSIONS = new Set([
  ".py",
  ".js",
  ".jsx",
  ".ts",
  ".tsx",
  ".java",
  ".go",
  ".php",
  ".rb",
  ".cs",
  ".cpp",
  ".cc",
  ".c",
  ".h",
  ".hpp",
]);

const sampleFiles = [
  {
    path: "app.py",
    content: `from flask import Flask, request
import hashlib
import pickle
import subprocess

app = Flask(__name__)
api_key = "prod-7aA9superSecretToken"

@app.route("/user")
def user():
    user_id = request.args.get("id")
    sql = f"SELECT * FROM users WHERE id = {user_id}"
    cursor.execute(sql)
    return "ok"

@app.route("/run")
def run():
    cmd = request.args.get("cmd")
    return subprocess.check_output(cmd, shell=True)

def load_payload(raw):
    return pickle.loads(raw)

def digest(value):
    return hashlib.md5(value).hexdigest()

app.run(debug=True)
`,
  },
];

const state = {
  files: [],
  audit: null,
};

const elements = {
  fileInput: document.querySelector("#fileInput"),
  githubUrl: document.querySelector("#githubUrl"),
  fileCount: document.querySelector("#fileCount"),
  auditButton: document.querySelector("#auditButton"),
  loadSampleButton: document.querySelector("#loadSampleButton"),
  message: document.querySelector("#message"),
  useLlm: document.querySelector("#useLlm"),
  llmStatus: document.querySelector("#llmStatus"),
  riskScore: document.querySelector("#riskScore"),
  findingCount: document.querySelector("#findingCount"),
  fixableCount: document.querySelector("#fixableCount"),
  scannedCount: document.querySelector("#scannedCount"),
  criticalCount: document.querySelector("#criticalCount"),
  highCount: document.querySelector("#highCount"),
  mediumCount: document.querySelector("#mediumCount"),
  lowCount: document.querySelector("#lowCount"),
  findingList: document.querySelector("#findingList"),
  patchView: document.querySelector("#patchView"),
  llmView: document.querySelector("#llmView"),
  copyPatchButton: document.querySelector("#copyPatchButton"),
  createIssueButton: document.querySelector("#createIssueButton"),
  createPrButton: document.querySelector("#createPrButton"),
};

window.addEventListener("DOMContentLoaded", () => {
  if (window.lucide) {
    window.lucide.createIcons();
  }
});

elements.fileInput.addEventListener("change", async (event) => {
  const files = Array.from(event.target.files || []).filter(shouldReadFile);
  state.files = await Promise.all(
    files.slice(0, 350).map(async (file) => ({
      path: file.webkitRelativePath || file.name,
      content: await file.text(),
    })),
  );
  elements.fileCount.textContent = `${state.files.length} 个代码文件`;
  setMessage("本地文件已载入");
});

elements.loadSampleButton.addEventListener("click", () => {
  state.files = sampleFiles;
  elements.githubUrl.value = "";
  elements.fileCount.textContent = "1 个示例文件";
  setMessage("示例代码已载入");
});

elements.auditButton.addEventListener("click", runAudit);
elements.copyPatchButton.addEventListener("click", copyPatch);
elements.createIssueButton.addEventListener("click", createIssue);
elements.createPrButton.addEventListener("click", createPullRequest);

document.querySelectorAll(".tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((item) => item.classList.remove("active"));
    document.querySelectorAll(".tab-page").forEach((page) => page.classList.remove("active"));
    tab.classList.add("active");
    document.querySelector(`#${tab.dataset.tab}Tab`).classList.add("active");
  });
});

async function runAudit() {
  const githubUrl = elements.githubUrl.value.trim();
  if (!githubUrl && state.files.length === 0) {
    setMessage("请先选择代码目录或填写 GitHub 仓库");
    return;
  }

  elements.auditButton.disabled = true;
  setMessage("审计中...");
  elements.llmStatus.textContent = elements.useLlm.checked ? "大模型分析中" : "规则引擎运行中";

  try {
    const response = await fetch("/api/audit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        github_url: githubUrl,
        files: githubUrl ? [] : state.files,
        use_llm: elements.useLlm.checked,
      }),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "审计失败");
    }
    state.audit = data;
    renderAudit(data);
    setMessage("审计完成");
    elements.llmStatus.textContent = data.llm?.enabled ? "AI 分析完成" : "规则引擎完成";
  } catch (error) {
    setMessage(error.message);
    elements.llmStatus.textContent = "需要处理";
  } finally {
    elements.auditButton.disabled = false;
  }
}

function renderAudit(data) {
  const summary = data.summary || {};
  const counts = summary.severity_counts || {};
  const findings = data.findings || [];
  const fixable = findings.filter((item) => item.fixable).length;

  elements.riskScore.textContent = summary.risk_score ?? 0;
  elements.findingCount.textContent = findings.length;
  elements.fixableCount.textContent = fixable;
  elements.scannedCount.textContent = summary.files_scanned ?? 0;
  elements.criticalCount.textContent = counts.critical || 0;
  elements.highCount.textContent = counts.high || 0;
  elements.mediumCount.textContent = counts.medium || 0;
  elements.lowCount.textContent = counts.low || 0;
  elements.findingList.innerHTML = findings.length ? findings.map(renderFinding).join("") : renderEmpty();
  elements.patchView.textContent = data.patch || "暂无自动补丁，仍可根据漏洞列表手动修复。";
  elements.llmView.textContent = renderLlm(data.llm);

  elements.copyPatchButton.disabled = !data.patch;
  const hasGithub = Boolean(elements.githubUrl.value.trim());
  elements.createIssueButton.disabled = !hasGithub || !findings.length;
  elements.createPrButton.disabled = !hasGithub || !(data.changed_files || []).length;

  if (window.lucide) {
    window.lucide.createIcons();
  }
}

function renderFinding(finding) {
  return `<article class="finding ${escapeHtml(finding.severity)}">
    <div class="finding-head">
      <h3>${escapeHtml(finding.title)}</h3>
      <span class="badge">${escapeHtml(finding.severity)}</span>
    </div>
    <div class="meta">${escapeHtml(finding.file_path)}:${finding.line} · ${escapeHtml(finding.category)} · ${escapeHtml(finding.cwe || "CWE")}</div>
    <code>${escapeHtml(finding.evidence)}</code>
    <p>${escapeHtml(finding.recommendation)}</p>
  </article>`;
}

function renderEmpty() {
  return `<article class="finding low">
    <div class="finding-head">
      <h3>未发现规则命中的高风险问题</h3>
      <span class="badge">clean</span>
    </div>
    <p>可继续启用大模型复核业务逻辑与跨文件风险。</p>
  </article>`;
}

function renderLlm(llm) {
  if (!llm || !llm.enabled) {
    return llm?.message ? `${llm.message}\n\nPrompt preview:\n${llm.prompt_preview || ""}` : "未启用大模型";
  }
  if (llm.error) {
    return llm.error;
  }
  return llm.content || JSON.stringify(llm.raw, null, 2);
}

async function copyPatch() {
  if (!state.audit?.patch) {
    return;
  }
  await navigator.clipboard.writeText(state.audit.patch);
  setMessage("补丁已复制");
}

async function createIssue() {
  await postGithubAction("/api/github/issue", {
    github_url: elements.githubUrl.value.trim(),
    title: "AI vulnerability audit report",
    body: state.audit.issue_body,
  });
}

async function createPullRequest() {
  await postGithubAction("/api/github/pr", {
    github_url: elements.githubUrl.value.trim(),
    title: "fix: apply AI vulnerability audit repairs",
    body: state.audit.pull_request_body,
    changed_files: state.audit.changed_files,
  });
}

async function postGithubAction(url, payload) {
  setMessage("提交 GitHub API 请求...");
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await response.json();
  if (!response.ok) {
    setMessage(data.error || "GitHub API 请求失败");
    return;
  }
  const link = data.issue?.html_url || data.pull_request?.html_url;
  setMessage(link ? `已创建：${link}` : "已创建");
}

function shouldReadFile(file) {
  const name = file.name.toLowerCase();
  const extension = name.slice(name.lastIndexOf("."));
  return CODE_EXTENSIONS.has(extension) && file.size <= 350000;
}

function setMessage(text) {
  elements.message.textContent = text;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
