const assert = require("node:assert/strict");
const engine = require("../engine.js");

const profileA = engine.parsePreferenceText("我预算 80 以内，喜欢奶油熊或者星旅兔，可爱治愈、粉色，想送朋友，不接受高溢价。");
assert.deepEqual(profileA.ips.sort(), ["奶油熊", "星旅兔"].sort());
assert.ok(profileA.styles.includes("可爱"));
assert.ok(profileA.styles.includes("治愈"));
assert.ok(profileA.colors.includes("粉色"));
assert.ok(profileA.purpose.includes("送朋友"));
assert.equal(profileA.budget.max, 80);
assert.equal(profileA.hiddenPremium, "low");

const matchesA = engine.recommend(profileA, { limit: 3 });
assert.equal(matchesA[0].product.id, "cream-bear-01");
assert.ok(matchesA[0].score >= 80);
assert.ok(matchesA[0].reasons.join("").includes("奶油熊"));

let profileB = engine.emptyProfile();
let response = engine.answerUser(profileB, "我喜欢酷一点的赛博机甲风，预算 100 左右，自留做桌面摆件。");
profileB = response.profile;
assert.ok(profileB.styles.includes("酷"));
assert.ok(profileB.styles.includes("科技"));
assert.ok(profileB.ips.includes("机甲猫"));
assert.ok(response.matches[0].product.id.startsWith("mecha-cat"));

const report = engine.exportMarkdown(profileA, matchesA);
assert.match(report, /# 盲盒 AI 推荐报告/);
assert.match(report, /奶油熊·草莓烘焙日/);
assert.match(report, /真实购买前应核对价格/);

console.log("blind box engine tests passed");
