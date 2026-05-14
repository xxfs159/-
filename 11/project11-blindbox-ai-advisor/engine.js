(function attachBlindBoxEngine(root, factory) {
  const engine = factory();
  if (typeof module === "object" && module.exports) {
    module.exports = engine;
  }
  root.BlindBoxEngine = engine;
})(typeof globalThis !== "undefined" ? globalThis : this, function createBlindBoxEngine() {
  const catalog = [
    {
      id: "starlit-rabbit-01",
      name: "星旅兔·月光邮差",
      series: "星旅兔宇宙来信",
      ip: "星旅兔",
      price: 69,
      rarity: "常规款",
      hiddenPremium: "low",
      colors: ["蓝色", "银色", "白色"],
      styles: ["治愈", "梦幻", "可爱"],
      traits: ["温柔", "安静", "陪伴感"],
      purpose: ["自留", "送朋友", "桌面摆件"],
      tags: ["星空", "礼物", "低溢价", "入门"],
      stock: 42,
      description: "蓝银色邮差造型，适合第一次入坑或送给喜欢安静治愈风的朋友。",
    },
    {
      id: "starlit-rabbit-02",
      name: "星旅兔·银河隐藏款",
      series: "星旅兔宇宙来信",
      ip: "星旅兔",
      price: 189,
      rarity: "隐藏款",
      hiddenPremium: "high",
      colors: ["紫色", "银色", "黑色"],
      styles: ["梦幻", "收藏", "酷"],
      traits: ["稀有", "闪粉", "展示感"],
      purpose: ["收藏", "拍照", "补全系列"],
      tags: ["隐藏款", "高溢价", "星空", "稀有"],
      stock: 5,
      description: "银河透明件和闪粉底座，适合明确接受隐藏款溢价的收藏型用户。",
    },
    {
      id: "cream-bear-01",
      name: "奶油熊·草莓烘焙日",
      series: "奶油熊甜品店",
      ip: "奶油熊",
      price: 59,
      rarity: "常规款",
      hiddenPremium: "low",
      colors: ["粉色", "奶油色", "红色"],
      styles: ["可爱", "甜美", "治愈"],
      traits: ["软萌", "温暖", "元气"],
      purpose: ["送朋友", "自留", "生日礼物"],
      tags: ["甜品", "低预算", "礼物", "少女感"],
      stock: 58,
      description: "草莓蛋糕帽和奶油围裙，礼物属性强，预算友好。",
    },
    {
      id: "cream-bear-02",
      name: "奶油熊·焦糖店长",
      series: "奶油熊甜品店",
      ip: "奶油熊",
      price: 79,
      rarity: "常规款",
      hiddenPremium: "medium",
      colors: ["棕色", "奶油色", "金色"],
      styles: ["复古", "可爱", "暖色"],
      traits: ["成熟", "温暖", "耐看"],
      purpose: ["桌面摆件", "自留", "搭配陈列"],
      tags: ["甜品", "复古", "暖色", "咖啡"],
      stock: 31,
      description: "焦糖和金色细节更耐看，适合喜欢暖色复古桌搭的人。",
    },
    {
      id: "mecha-cat-01",
      name: "机甲猫·霓虹巡航",
      series: "机甲猫城市计划",
      ip: "机甲猫",
      price: 89,
      rarity: "常规款",
      hiddenPremium: "medium",
      colors: ["黑色", "蓝色", "荧光绿"],
      styles: ["酷", "赛博", "科技"],
      traits: ["机械", "利落", "个性"],
      purpose: ["自留", "桌面摆件", "男生礼物"],
      tags: ["赛博朋克", "机甲", "科技感", "桌搭"],
      stock: 24,
      description: "机械猫耳、透明护目镜和霓虹线条，适合酷感桌搭。",
    },
    {
      id: "mecha-cat-02",
      name: "机甲猫·维修工程师",
      series: "机甲猫城市计划",
      ip: "机甲猫",
      price: 72,
      rarity: "常规款",
      hiddenPremium: "low",
      colors: ["黄色", "灰色", "黑色"],
      styles: ["科技", "街头", "趣味"],
      traits: ["工具感", "活泼", "实用"],
      purpose: ["送朋友", "桌面摆件", "开箱视频"],
      tags: ["机甲", "低溢价", "工程", "反差萌"],
      stock: 37,
      description: "工程服造型更有故事感，适合想要趣味但不追高溢价的人。",
    },
    {
      id: "forest-elf-01",
      name: "森眠精灵·苔藓午后",
      series: "森眠精灵花园",
      ip: "森眠精灵",
      price: 76,
      rarity: "常规款",
      hiddenPremium: "low",
      colors: ["绿色", "米色", "棕色"],
      styles: ["自然", "治愈", "文艺"],
      traits: ["安静", "清新", "植物感"],
      purpose: ["桌面摆件", "自留", "拍照"],
      tags: ["植物", "自然", "低溢价", "文艺"],
      stock: 46,
      description: "苔藓斗篷与小蘑菇配件，适合植物系和文艺风桌面。",
    },
    {
      id: "forest-elf-02",
      name: "森眠精灵·夜光鹿角",
      series: "森眠精灵花园",
      ip: "森眠精灵",
      price: 128,
      rarity: "稀有款",
      hiddenPremium: "medium",
      colors: ["绿色", "银色", "白色"],
      styles: ["梦幻", "自然", "收藏"],
      traits: ["夜光", "精致", "仪式感"],
      purpose: ["收藏", "送朋友", "拍照"],
      tags: ["夜光", "稀有", "植物", "礼物"],
      stock: 12,
      description: "鹿角夜光涂层和透明叶片，预算略高但展示效果强。",
    },
    {
      id: "jellyfish-01",
      name: "海盐水母·透明蓝岛",
      series: "海盐水母漂流瓶",
      ip: "海盐水母",
      price: 85,
      rarity: "常规款",
      hiddenPremium: "medium",
      colors: ["蓝色", "透明", "白色"],
      styles: ["清爽", "梦幻", "治愈"],
      traits: ["通透", "夏天", "轻盈"],
      purpose: ["拍照", "自留", "桌面摆件"],
      tags: ["透明件", "夏日", "蓝色", "拍照"],
      stock: 28,
      description: "透明材质和海盐蓝渐变，适合喜欢清爽梦幻风的用户。",
    },
    {
      id: "jellyfish-02",
      name: "海盐水母·日落漂流",
      series: "海盐水母漂流瓶",
      ip: "海盐水母",
      price: 66,
      rarity: "常规款",
      hiddenPremium: "low",
      colors: ["橙色", "粉色", "透明"],
      styles: ["清爽", "甜美", "度假"],
      traits: ["轻盈", "明亮", "放松"],
      purpose: ["送朋友", "拍照", "自留"],
      tags: ["透明件", "低预算", "夏日", "礼物"],
      stock: 40,
      description: "日落渐变色更活泼，适合预算中等、喜欢拍照的人。",
    },
    {
      id: "retro-toy-01",
      name: "复古玩具·像素游戏机",
      series: "复古玩具杂货铺",
      ip: "复古玩具",
      price: 62,
      rarity: "常规款",
      hiddenPremium: "low",
      colors: ["红色", "黄色", "蓝色"],
      styles: ["复古", "街头", "趣味"],
      traits: ["怀旧", "明快", "玩具感"],
      purpose: ["男生礼物", "桌面摆件", "开箱视频"],
      tags: ["复古", "低预算", "游戏", "礼物"],
      stock: 53,
      description: "像素屏和按键细节，适合作为轻松有梗的礼物。",
    },
    {
      id: "retro-toy-02",
      name: "复古玩具·磁带舞会",
      series: "复古玩具杂货铺",
      ip: "复古玩具",
      price: 92,
      rarity: "常规款",
      hiddenPremium: "medium",
      colors: ["紫色", "橙色", "黑色"],
      styles: ["复古", "潮流", "街头"],
      traits: ["音乐", "个性", "强色彩"],
      purpose: ["收藏", "自留", "开箱视频"],
      tags: ["复古", "音乐", "潮流", "强视觉"],
      stock: 19,
      description: "磁带头饰和撞色服装，适合喜欢潮流复古的人。",
    },
  ];

  const lexicon = {
    ips: {
      星旅兔: ["星旅兔", "兔", "兔子", "宇宙", "星空"],
      奶油熊: ["奶油熊", "熊", "甜品", "草莓", "奶油"],
      机甲猫: ["机甲猫", "猫", "机甲", "赛博", "科技"],
      森眠精灵: ["森眠", "精灵", "森林", "植物", "自然"],
      海盐水母: ["海盐", "水母", "海", "夏天", "透明"],
      复古玩具: ["复古", "游戏机", "磁带", "玩具", "怀旧"],
    },
    styles: {
      可爱: ["可爱", "萌", "软萌", "少女", "甜"],
      治愈: ["治愈", "温柔", "安静", "陪伴", "舒服"],
      梦幻: ["梦幻", "星空", "闪", "透明", "仙"],
      酷: ["酷", "帅", "机甲", "赛博", "黑色", "科技"],
      科技: ["科技", "机甲", "赛博", "机械", "霓虹", "工程"],
      复古: ["复古", "怀旧", "街头", "像素", "磁带"],
      自然: ["自然", "植物", "森林", "绿色", "清新"],
      清爽: ["清爽", "夏天", "蓝色", "海", "透明"],
      甜美: ["甜美", "草莓", "粉色", "奶油", "生日"],
      收藏: ["收藏", "隐藏", "稀有", "补全", "端盒"],
    },
    colors: {
      粉色: ["粉", "粉色", "粉红"],
      蓝色: ["蓝", "蓝色", "海蓝"],
      绿色: ["绿", "绿色", "森林"],
      黑色: ["黑", "黑色"],
      白色: ["白", "白色", "奶白"],
      紫色: ["紫", "紫色"],
      黄色: ["黄", "黄色"],
      橙色: ["橙", "橙色"],
      棕色: ["棕", "咖啡", "焦糖"],
      银色: ["银", "银色", "金属"],
      红色: ["红", "红色"],
      透明: ["透明", "通透", "亚克力"],
    },
    purpose: {
      自留: ["自留", "自己", "我自己", "自用"],
      送朋友: ["送朋友", "送人", "礼物", "生日", "同学"],
      收藏: ["收藏", "补全", "端盒", "稀有"],
      拍照: ["拍照", "晒图", "出片", "开箱"],
      桌面摆件: ["桌面", "摆件", "工位", "书桌", "宿舍"],
      男生礼物: ["男生", "男朋友", "兄弟", "室友"],
    },
    traits: {
      低预算: ["便宜", "低预算", "性价比", "别太贵", "学生党"],
      高展示感: ["展示", "出片", "显眼", "特别", "高级"],
      低溢价: ["不接受溢价", "不想加价", "原价", "别炒"],
      接受溢价: ["接受溢价", "可以加价", "隐藏款", "稀有", "贵一点"],
    },
  };

  const questionFlow = [
    {
      key: "style",
      text: "你更喜欢哪种风格？例如可爱、治愈、梦幻、酷感、复古、自然。",
      missing: (profile) => profile.styles.length === 0,
    },
    {
      key: "budget",
      text: "预算大概是多少？可以说“80 以内”“100 左右”“可以接受 150”。",
      missing: (profile) => !profile.budget.max,
    },
    {
      key: "purpose",
      text: "这次是自留、送朋友、收藏，还是想做桌面摆件/拍照？",
      missing: (profile) => profile.purpose.length === 0,
    },
    {
      key: "premium",
      text: "你能接受隐藏款溢价吗？比如只买原价、可小幅加价、愿意冲隐藏款。",
      missing: (profile) => profile.hiddenPremium === "unknown",
    },
  ];

  function emptyProfile() {
    return {
      ips: [],
      styles: [],
      colors: [],
      purpose: [],
      traits: [],
      budget: { min: 0, max: null, raw: "" },
      hiddenPremium: "unknown",
      notes: [],
    };
  }

  function normalizeText(text) {
    return String(text || "")
      .replace(/\s+/g, " ")
      .trim();
  }

  function includesAny(text, words) {
    const lower = text.toLowerCase();
    return words.some((word) => lower.includes(String(word).toLowerCase()));
  }

  function detectFromLexicon(text, group) {
    return Object.entries(group)
      .filter(([, words]) => includesAny(text, words))
      .map(([label]) => label);
  }

  function parseBudget(text) {
    const normalized = normalizeText(text);
    const numbers = (normalized.match(/\d+(\.\d+)?/g) || []).map(Number);
    const budget = { min: 0, max: null, raw: "" };
    if (numbers.length === 0) return budget;

    const value = Math.max(...numbers);
    budget.raw = normalized;
    if (/以内|以下|不超过|低于|封顶|最多|小于|别超过/.test(normalized)) {
      budget.max = value;
    } else if (/左右|附近|上下|大概|约|预算/.test(normalized)) {
      budget.min = Math.max(0, Math.round(value * 0.7));
      budget.max = Math.round(value * 1.25);
    } else if (/以上|起|至少|可以接受|能接受/.test(normalized)) {
      budget.min = Math.round(value * 0.8);
      budget.max = Math.round(value * 1.5);
    } else {
      budget.max = value;
    }
    return budget;
  }

  function parsePremium(text) {
    if (/不接受.*溢价|不想加价|原价|别炒|不买隐藏|不要隐藏|别太贵/.test(text)) return "low";
    if (/隐藏款|稀有|可以加价|接受溢价|冲隐藏|贵一点|收藏/.test(text)) return "high";
    if (/小幅|一点点|适当|看情况/.test(text)) return "medium";
    return "unknown";
  }

  function parsePreferenceText(text) {
    const normalized = normalizeText(text);
    const profile = emptyProfile();
    if (!normalized) return profile;

    profile.ips = detectFromLexicon(normalized, lexicon.ips);
    profile.styles = detectFromLexicon(normalized, lexicon.styles);
    profile.colors = detectFromLexicon(normalized, lexicon.colors);
    profile.purpose = detectFromLexicon(normalized, lexicon.purpose);
    profile.traits = detectFromLexicon(normalized, lexicon.traits);
    profile.budget = parseBudget(normalized);
    profile.hiddenPremium = parsePremium(normalized);
    profile.notes = normalized
      .split(/[，,。；;！!？?]/)
      .map((item) => item.trim())
      .filter(Boolean)
      .slice(0, 5);
    return profile;
  }

  function mergeUnique(a, b) {
    return Array.from(new Set([...(a || []), ...(b || [])])).filter(Boolean);
  }

  function mergeProfiles(base, update) {
    const next = {
      ips: mergeUnique(base.ips, update.ips),
      styles: mergeUnique(base.styles, update.styles),
      colors: mergeUnique(base.colors, update.colors),
      purpose: mergeUnique(base.purpose, update.purpose),
      traits: mergeUnique(base.traits, update.traits),
      budget: update.budget.max ? update.budget : base.budget,
      hiddenPremium: update.hiddenPremium !== "unknown" ? update.hiddenPremium : base.hiddenPremium,
      notes: mergeUnique(base.notes, update.notes).slice(-8),
    };
    return next;
  }

  function overlapCount(a, b) {
    const set = new Set(a || []);
    return (b || []).filter((item) => set.has(item)).length;
  }

  function budgetFit(profile, product) {
    if (!profile.budget.max) return { points: 8, label: "预算未声明", ok: true };
    const { min, max } = profile.budget;
    if (product.price <= max && product.price >= min) {
      return { points: 18, label: `价格 ${product.price} 元落在预算内`, ok: true };
    }
    if (product.price <= max + 20) {
      return { points: 8, label: `价格 ${product.price} 元略高于预算`, ok: false };
    }
    return { points: -12, label: `价格 ${product.price} 元明显超预算`, ok: false };
  }

  function premiumFit(profile, product) {
    if (profile.hiddenPremium === "unknown") return { points: 5, label: "溢价偏好未声明", ok: true };
    if (profile.hiddenPremium === "low" && product.hiddenPremium === "low") {
      return { points: 12, label: "低溢价，适合稳妥购买", ok: true };
    }
    if (profile.hiddenPremium === "low" && product.hiddenPremium === "high") {
      return { points: -18, label: "隐藏款溢价高，不符合原价偏好", ok: false };
    }
    if (profile.hiddenPremium === "high" && ["high", "medium"].includes(product.hiddenPremium)) {
      return { points: 12, label: "稀有度和收藏诉求匹配", ok: true };
    }
    if (profile.hiddenPremium === "medium" && product.hiddenPremium !== "high") {
      return { points: 10, label: "溢价风险适中", ok: true };
    }
    return { points: 3, label: "溢价偏好基本可接受", ok: true };
  }

  function scoreProduct(profile, product) {
    const reasons = [];
    const cautions = [];
    let score = 28;

    const ipHits = overlapCount(profile.ips, [product.ip]);
    if (profile.ips.length > 0) {
      if (ipHits > 0) {
        score += 22;
        reasons.push(`命中偏好 IP：${product.ip}`);
      } else {
        score -= 8;
        cautions.push(`不是你明确提到的 ${profile.ips.join("、")} 系列`);
      }
    }

    const styleHits = overlapCount(profile.styles, product.styles);
    score += Math.min(styleHits * 12, 30);
    if (styleHits > 0) reasons.push(`风格匹配：${product.styles.filter((item) => profile.styles.includes(item)).join("、")}`);

    const colorHits = overlapCount(profile.colors, product.colors);
    score += Math.min(colorHits * 7, 18);
    if (colorHits > 0) reasons.push(`颜色匹配：${product.colors.filter((item) => profile.colors.includes(item)).join("、")}`);

    const purposeHits = overlapCount(profile.purpose, product.purpose);
    score += Math.min(purposeHits * 8, 18);
    if (purposeHits > 0) reasons.push(`用途匹配：${product.purpose.filter((item) => profile.purpose.includes(item)).join("、")}`);

    const traitHits = overlapCount(profile.traits, product.tags);
    score += Math.min(traitHits * 5, 12);

    const budget = budgetFit(profile, product);
    score += budget.points;
    (budget.ok ? reasons : cautions).push(budget.label);

    const premium = premiumFit(profile, product);
    score += premium.points;
    (premium.ok ? reasons : cautions).push(premium.label);

    if (product.stock < 10) cautions.push("库存偏少，建议确认是否能原价入手");
    if (product.stock > 35) score += 4;

    return {
      product,
      score: Math.max(0, Math.min(100, Math.round(score))),
      reasons: reasons.slice(0, 4),
      cautions: cautions.slice(0, 3),
      dimensions: {
        styleHits,
        colorHits,
        purposeHits,
        ipHits,
        budgetOk: budget.ok,
        premiumOk: premium.ok,
      },
    };
  }

  function recommend(profile, options = {}) {
    const limit = options.limit || 5;
    return catalog
      .map((product) => scoreProduct(profile, product))
      .sort((a, b) => b.score - a.score || a.product.price - b.product.price)
      .slice(0, limit);
  }

  function profileCompleteness(profile) {
    const fields = [
      profile.styles.length > 0,
      Boolean(profile.budget.max),
      profile.purpose.length > 0,
      profile.hiddenPremium !== "unknown",
      profile.colors.length > 0 || profile.ips.length > 0,
    ];
    return Math.round((fields.filter(Boolean).length / fields.length) * 100);
  }

  function nextQuestion(profile) {
    const next = questionFlow.find((item) => item.missing(profile));
    if (next) return next.text;
    return "信息已经够推荐了。还可以继续告诉我讨厌的颜色、是否想端盒、或者有没有指定系列。";
  }

  function summarizeProfile(profile) {
    const chunks = [];
    if (profile.ips.length) chunks.push(`偏好 IP：${profile.ips.join("、")}`);
    if (profile.styles.length) chunks.push(`风格：${profile.styles.join("、")}`);
    if (profile.colors.length) chunks.push(`颜色：${profile.colors.join("、")}`);
    if (profile.purpose.length) chunks.push(`用途：${profile.purpose.join("、")}`);
    if (profile.budget.max) chunks.push(`预算：${profile.budget.min || 0}-${profile.budget.max} 元`);
    if (profile.hiddenPremium !== "unknown") {
      const labels = { low: "不接受高溢价", medium: "可接受小幅溢价", high: "愿意冲稀有/隐藏款" };
      chunks.push(`溢价：${labels[profile.hiddenPremium]}`);
    }
    return chunks.length ? chunks.join("；") : "还没有形成明确画像";
  }

  function answerUser(currentProfile, userText) {
    const extracted = parsePreferenceText(userText);
    const profile = mergeProfiles(currentProfile, extracted);
    const matches = recommend(profile, { limit: 5 });
    const top = matches[0];
    const acknowledgement = extracted.notes.length
      ? `我记录到了：${extracted.notes.join("、")}。`
      : "我还没有识别到新的偏好，可以换一种说法描述风格、预算或用途。";
    const reply = [
      acknowledgement,
      top
        ? `当前最推荐「${top.product.name}」，匹配度 ${top.score}%。${top.reasons.slice(0, 2).join("；")}。`
        : "",
      nextQuestion(profile),
    ]
      .filter(Boolean)
      .join("\n");

    return { profile, matches, reply, extracted };
  }

  function exportMarkdown(profile, matches) {
    const rows = matches
      .slice(0, 5)
      .map(
        (match, index) =>
          `| ${index + 1} | ${match.product.name} | ${match.product.price} 元 | ${match.score}% | ${match.reasons.join("；")} | ${match.cautions.join("；") || "无明显风险"} |`,
      )
      .join("\n");
    return [
      "# 盲盒 AI 推荐报告",
      "",
      `## 用户兴趣画像`,
      summarizeProfile(profile),
      "",
      "## 推荐清单",
      "| 排名 | 款式 | 价格 | 匹配度 | 推荐理由 | 购买提醒 |",
      "| --- | --- | ---: | ---: | --- | --- |",
      rows || "| - | 暂无 | - | - | 请先输入偏好 | - |",
      "",
      "## 解释口径",
      "- 匹配度综合考虑 IP、风格、颜色、用途、预算与隐藏款溢价接受度。",
      "- 商品库为课程演示用离线样例数据，真实购买前应核对价格、库存与正版渠道。",
    ].join("\n");
  }

  return {
    answerUser,
    catalog,
    emptyProfile,
    exportMarkdown,
    mergeProfiles,
    nextQuestion,
    parsePreferenceText,
    profileCompleteness,
    recommend,
    scoreProduct,
    summarizeProfile,
  };
});
