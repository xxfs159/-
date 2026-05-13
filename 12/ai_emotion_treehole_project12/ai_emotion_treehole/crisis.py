from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Tuple


DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def load_crisis_keywords(path: Path | None = None) -> Dict[str, List[str]]:
    """读取危机词表。

    课程展示时可以把词表扩展为更完整的安全分类器；这里保持透明、可解释，
    便于答辩时说明“为什么会报警”。
    """
    path = path or DATA_DIR / "crisis_keywords.json"
    return json.loads(path.read_text(encoding="utf-8"))


def detect_crisis(text: str, keywords: Dict[str, List[str]] | None = None) -> Tuple[bool, str, List[str]]:
    """检测是否出现高风险表达。

    返回：
        is_crisis: 是否触发危机提示
        category: 触发类别
        hits: 命中的关键词
    """
    clean_text = (text or "").lower().replace(" ", "")
    keywords = keywords or load_crisis_keywords()

    hits_by_category: Dict[str, List[str]] = {}
    for category, words in keywords.items():
        hits = [w for w in words if w.lower().replace(" ", "") in clean_text]
        if hits:
            hits_by_category[category] = hits

    if not hits_by_category:
        return False, "none", []

    # 自伤/自杀类风险优先级最高。
    priority = ["self_harm", "violence", "extreme_hopeless"]
    for category in priority:
        if category in hits_by_category:
            return True, category, hits_by_category[category]

    category = next(iter(hits_by_category))
    return True, category, hits_by_category[category]


def build_crisis_message() -> str:
    """生成危机状态下的安全回应模板。"""
    return (
        "我很重视你刚才表达出的危险信号。此刻最重要的是先保证你的现实安全："
        "请尽快离开可能伤害自己的物品或地点，联系身边可信任的人陪你待一会儿。"
        "如果你已经有具体计划、工具，或觉得自己马上可能失控，请立即拨打 120/110，"
        "或联系学校心理中心、辅导员、家人朋友。你不需要一个人扛过去。"
    )
