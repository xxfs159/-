from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Dict, List, Tuple


DATA_DIR = Path(__file__).resolve().parents[1] / "data"

EMOTION_COLORS = {
    "焦虑": "#FFB020",
    "低落": "#6B7FD7",
    "愤怒": "#F25F5C",
    "孤独": "#7B61FF",
    "压力": "#FF8C42",
    "平静": "#6FCF97",
    "积极": "#2D9CDB",
}

EMOTION_SUGGESTIONS = {
    "焦虑": ["先把担心写成清单", "把最近24小时最小可做的一步圈出来", "做3轮慢呼吸"],
    "低落": ["降低今日目标", "完成一件很小的事", "给自己安排一次短休息"],
    "愤怒": ["先暂停回应", "用纸写下事实和感受", "等情绪下降后再沟通"],
    "孤独": ["找一个可信任的人发一句问候", "去公共空间坐一会儿", "尝试加入一个低压力活动"],
    "压力": ["按紧急/重要拆分任务", "给DDL任务设置番茄钟", "先完成可提交的最小版本"],
    "平静": ["保持当前节奏", "记录一个今天做得不错的地方", "适度休息"],
    "积极": ["记录有效经验", "把好状态延续到明天", "给自己一个小奖励"],
}


def load_lexicon(path: Path | None = None) -> Dict[str, List[str]]:
    path = path or DATA_DIR / "emotion_lexicon.json"
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_text(text: str) -> str:
    text = (text or "").strip().lower()
    text = re.sub(r"\s+", "", text)
    return text


def keyword_scores(text: str, lexicon: Dict[str, List[str]] | None = None) -> Dict[str, float]:
    """基于关键词词典的透明情绪打分。

    设计原因：
    1. 不依赖大型模型，本地即可运行；
    2. 结果可解释，适合课程海报展示；
    3. 后续可替换为 BERT/ERNIE/大模型分类器。
    """
    lexicon = lexicon or load_lexicon()
    normalized = normalize_text(text)
    scores = {emotion: 0.0 for emotion in lexicon}

    for emotion, words in lexicon.items():
        for word in words:
            w = normalize_text(word)
            if not w:
                continue
            count = normalized.count(w)
            if count:
                # 较长关键词通常更有判别力，因此给予轻微长度加权。
                scores[emotion] += count * (1.0 + min(len(w), 8) / 10.0)

    # 一些常见符号/语气词会提示情绪强度。
    if "！" in text or "!" in text:
        scores["愤怒"] = scores.get("愤怒", 0) + 0.3
        scores["压力"] = scores.get("压力", 0) + 0.2
    if "睡不着" in normalized or "失眠" in normalized:
        scores["焦虑"] = scores.get("焦虑", 0) + 0.8
    if "ddl" in normalized or "deadline" in normalized:
        scores["压力"] = scores.get("压力", 0) + 1.0

    return scores


def analyze_emotion(text: str) -> Dict[str, object]:
    """输出情绪标签、置信度和解释。"""
    if not text or not text.strip():
        return {
            "emotion": "平静",
            "confidence": 0.0,
            "scores": {},
            "reason": "输入为空，默认标记为平静。",
            "suggestions": EMOTION_SUGGESTIONS["平静"],
            "intensity": "低",
        }

    scores = keyword_scores(text)
    if not any(v > 0 for v in scores.values()):
        # 默认将未知内容归为平静，避免强行贴负面标签。
        emotion = "平静"
        confidence = 0.45
        reason = "未命中明显负面或正向关键词，因此暂按平静/中性处理。"
    else:
        emotion = max(scores, key=scores.get)
        total = sum(max(v, 0) for v in scores.values()) + 1e-9
        confidence = min(0.95, 0.50 + scores[emotion] / total * 0.45)
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]
        reason = "主要依据关键词/语气打分判断；前三类得分为：" + "，".join(
            f"{name}:{score:.1f}" for name, score in sorted_scores if score > 0
        )

    strength = scores.get(emotion, 0)
    if strength >= 4:
        intensity = "高"
    elif strength >= 1.5:
        intensity = "中"
    else:
        intensity = "低"

    return {
        "emotion": emotion,
        "confidence": round(float(confidence), 2),
        "scores": scores,
        "reason": reason,
        "suggestions": EMOTION_SUGGESTIONS.get(emotion, EMOTION_SUGGESTIONS["平静"]),
        "intensity": intensity,
    }


def summarize_trend(records: List[Dict[str, object]]) -> str:
    """根据历史记录生成简短趋势说明。"""
    if not records:
        return "暂无历史记录。连续记录几天后，系统会生成情绪趋势总结。"

    emotions = [r.get("emotion", "平静") for r in records]
    last = emotions[-1]
    counts = {e: emotions.count(e) for e in set(emotions)}
    main = max(counts, key=counts.get)

    if len(records) < 3:
        return f"目前记录较少，最近一次主要情绪为“{last}”。建议继续记录，观察是否持续出现同类情绪。"

    negative = sum(1 for e in emotions[-3:] if e in {"焦虑", "低落", "愤怒", "孤独", "压力"})
    if negative >= 3:
        return f"最近3次记录均偏负面，主要集中在“{main}”。建议减少独自承受，联系朋友、辅导员或学校心理中心获得支持。"
    return f"近期最常出现的情绪是“{main}”，最近一次为“{last}”。整体没有连续高风险趋势。"
