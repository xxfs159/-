from __future__ import annotations

import re
from typing import Iterable


def normalize_text(text: str) -> str:
    """基础文本清洗：去除多余空白，统一大小写保留原语义。"""
    if not text:
        return ""
    text = text.replace("\u3000", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def split_items(value: str) -> list[str]:
    """将逗号/顿号/斜杠分隔的技能字段拆成列表。"""
    if not value:
        return []
    parts = re.split(r"[,，、/|;；\s]+", str(value))
    return [p.strip() for p in parts if p.strip()]


def unique_keep_order(items: Iterable[str]) -> list[str]:
    """去重并保持原顺序。"""
    seen = set()
    result = []
    for item in items:
        key = item.lower()
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result
