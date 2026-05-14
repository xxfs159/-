const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => Array.from(document.querySelectorAll(selector));

const state = {
  profile: BlindBoxEngine.emptyProfile(),
  matches: [],
  activeStyle: "全部",
};

const welcomeMessage =
  "你好，我是盲盒 AI 推荐员。你可以直接说预算、喜欢的风格、颜色、用途和是否接受隐藏款溢价，我会生成兴趣画像并推荐款式。";

function init() {
  state.matches = BlindBoxEngine.recommend(state.profile, { limit: 5 });
  bindEvents();
  renderStyleFilter();
  addMessage("bot", welcomeMessage);
  addMessage("bot", BlindBoxEngine.nextQuestion(state.profile));
  renderAll();
}

function bindEvents() {
  $("#chatForm").addEventListener("submit", (event) => {
    event.preventDefault();
    handleUserInput($("#userInput").value);
  });

  $$(".quick-chips button").forEach((button) => {
    button.addEventListener("click", () => handleUserInput(button.dataset.chip));
  });

  $("#sampleBtn").addEventListener("click", () => {
    handleUserInput("我预算 80 以内，喜欢奶油熊或者星旅兔，可爱治愈、粉色，想送朋友，不接受高溢价。");
  });

  $("#resetBtn").addEventListener("click", resetApp);
  $("#exportBtn").addEventListener("click", exportReport);
}

function handleUserInput(text) {
  const value = String(text || "").trim();
  if (!value) return;
  addMessage("user", value);
  const result = BlindBoxEngine.answerUser(state.profile, value);
  state.profile = result.profile;
  state.matches = result.matches;
  addMessage("bot", result.reply);
  $("#userInput").value = "";
  renderAll();
}

function resetApp() {
  state.profile = BlindBoxEngine.emptyProfile();
  state.matches = BlindBoxEngine.recommend(state.profile, { limit: 5 });
  $("#chatLog").innerHTML = "";
  addMessage("bot", welcomeMessage);
  addMessage("bot", BlindBoxEngine.nextQuestion(state.profile));
  renderAll();
}

function addMessage(role, text) {
  const message = document.createElement("div");
  message.className = `message ${role}`;
  message.innerHTML = text
    .split("\n")
    .map((line) => `<p>${escapeHtml(line)}</p>`)
    .join("");
  $("#chatLog").appendChild(message);
  $("#chatLog").scrollTop = $("#chatLog").scrollHeight;
}

function renderAll() {
  renderProfile();
  renderTopRecommendation();
  renderRecommendationList();
  renderCompareTable();
  renderCatalog();
}

function renderProfile() {
  const completeness = BlindBoxEngine.profileCompleteness(state.profile);
  $("#profileScore").textContent = `画像完整度 ${completeness}%`;
  $("#nextHint").textContent = BlindBoxEngine.nextQuestion(state.profile);
  $("#profileSummary").textContent = BlindBoxEngine.summarizeProfile(state.profile);

  const tags = [
    ...state.profile.ips.map((item) => ["IP", item]),
    ...state.profile.styles.map((item) => ["风格", item]),
    ...state.profile.colors.map((item) => ["颜色", item]),
    ...state.profile.purpose.map((item) => ["用途", item]),
    state.profile.budget.max ? ["预算", `${state.profile.budget.min || 0}-${state.profile.budget.max} 元`] : null,
    state.profile.hiddenPremium !== "unknown" ? ["溢价", premiumText(state.profile.hiddenPremium)] : null,
  ].filter(Boolean);

  $("#profileTags").innerHTML = tags.length
    ? tags.map(([type, value]) => `<span><b>${type}</b>${value}</span>`).join("")
    : `<span><b>待采集</b>先输入风格、预算或用途</span>`;
}

function renderTopRecommendation() {
  const top = state.matches[0];
  if (!top) {
    $("#topScore").textContent = "0%";
    $("#topRecommendation").innerHTML = "";
    return;
  }
  $("#topScore").textContent = `${top.score}%`;
  $("#topRecommendation").innerHTML = `
    <div class="top-content">
      ${toyVisual(top.product, "large")}
      <div>
        <p class="series">${top.product.series}</p>
        <h3>${top.product.name}</h3>
        <p class="desc">${top.product.description}</p>
        <div class="reason-list">
          ${top.reasons.map((reason) => `<span>${reason}</span>`).join("")}
        </div>
        <div class="warning-list">
          ${top.cautions.map((item) => `<span>${item}</span>`).join("") || "<span>无明显购买风险</span>"}
        </div>
      </div>
    </div>
  `;
}

function renderRecommendationList() {
  $("#recommendationList").innerHTML = state.matches
    .map(
      (match) => `
        <article class="product-card">
          ${toyVisual(match.product)}
          <div class="product-body">
            <div class="product-title">
              <strong>${match.product.name}</strong>
              <span>${match.score}%</span>
            </div>
            <p>${match.product.ip} · ${match.product.rarity} · ${match.product.price} 元</p>
            <div class="mini-tags">
              ${[...match.product.styles.slice(0, 2), ...match.product.colors.slice(0, 1)].map((tag) => `<i>${tag}</i>`).join("")}
            </div>
          </div>
        </article>
      `,
    )
    .join("");
}

function renderCompareTable() {
  $("#compareTable").innerHTML = `
    <table>
      <thead>
        <tr>
          <th>款式</th>
          <th>价格</th>
          <th>匹配度</th>
          <th>溢价</th>
          <th>核心理由</th>
        </tr>
      </thead>
      <tbody>
        ${state.matches
          .map(
            (match) => `
              <tr>
                <td>${match.product.name}</td>
                <td>${match.product.price} 元</td>
                <td>${match.score}%</td>
                <td>${premiumText(match.product.hiddenPremium)}</td>
                <td>${match.reasons[0] || "等待更多偏好"}</td>
              </tr>
            `,
          )
          .join("")}
      </tbody>
    </table>
  `;
}

function renderStyleFilter() {
  const styles = ["全部", ...new Set(BlindBoxEngine.catalog.flatMap((item) => item.styles))];
  $("#styleFilter").innerHTML = styles.map((style) => `<button type="button" data-style="${style}">${style}</button>`).join("");
  $$("#styleFilter button").forEach((button) => {
    button.addEventListener("click", () => {
      state.activeStyle = button.dataset.style;
      renderStyleFilter();
      renderCatalog();
    });
  });
}

function renderCatalog() {
  const products =
    state.activeStyle === "全部"
      ? BlindBoxEngine.catalog
      : BlindBoxEngine.catalog.filter((product) => product.styles.includes(state.activeStyle));
  $$("#styleFilter button").forEach((button) => button.classList.toggle("active", button.dataset.style === state.activeStyle));
  $("#catalogList").innerHTML = products
    .map(
      (product) => `
        <article>
          ${toyVisual(product)}
          <div>
            <strong>${product.name}</strong>
            <p>${product.description}</p>
            <small>${product.series} · ${product.price} 元 · 库存 ${product.stock}</small>
          </div>
        </article>
      `,
    )
    .join("");
}

function toyVisual(product, size = "normal") {
  const palette = product.colors.map(colorToHex);
  const [a, b, c] = [palette[0] || "#7aa6c2", palette[1] || "#f1d06f", palette[2] || "#ffffff"];
  const className = size === "large" ? "toy-visual large" : "toy-visual";
  return `
    <svg class="${className}" viewBox="0 0 120 120" role="img" aria-label="${product.name}">
      <rect x="12" y="12" width="96" height="96" rx="18" fill="${c}" opacity="0.72"></rect>
      <path d="M34 58c0-20 12-35 27-35s27 15 27 35v20c0 16-11 27-27 27S34 94 34 78V58z" fill="${a}"></path>
      <circle cx="48" cy="62" r="5" fill="#211f1c"></circle>
      <circle cx="74" cy="62" r="5" fill="#211f1c"></circle>
      <path d="M51 78c7 6 14 6 21 0" fill="none" stroke="#211f1c" stroke-width="4" stroke-linecap="round"></path>
      <path d="M37 39l-13-15M83 39l13-15" stroke="${b}" stroke-width="9" stroke-linecap="round"></path>
      <rect x="42" y="88" width="38" height="13" rx="6" fill="${b}"></rect>
      <circle cx="90" cy="30" r="10" fill="${b}" opacity="0.86"></circle>
      <circle cx="28" cy="92" r="7" fill="${a}" opacity="0.52"></circle>
    </svg>
  `;
}

function colorToHex(color) {
  const map = {
    蓝色: "#5aa6d6",
    银色: "#bec7cf",
    白色: "#fffaf0",
    紫色: "#8d78c8",
    黑色: "#24242b",
    粉色: "#f3a8bd",
    奶油色: "#f6e5bc",
    红色: "#d95854",
    棕色: "#9c6a42",
    金色: "#d6a64c",
    荧光绿: "#89d76d",
    黄色: "#e8c64d",
    灰色: "#9fa4aa",
    绿色: "#6fab73",
    米色: "#e5d2ac",
    透明: "#b7e5ee",
    橙色: "#e89049",
  };
  return map[color] || "#7aa6c2";
}

function premiumText(value) {
  return {
    low: "低溢价",
    medium: "适中",
    high: "高溢价",
    unknown: "未声明",
  }[value];
}

function exportReport() {
  const markdown = BlindBoxEngine.exportMarkdown(state.profile, state.matches);
  const blob = new Blob([markdown], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "blindbox-recommendation-report.md";
  link.click();
  URL.revokeObjectURL(url);
}

function escapeHtml(text) {
  return String(text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

document.addEventListener("DOMContentLoaded", init);
