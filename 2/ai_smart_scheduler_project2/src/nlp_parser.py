from __future__ import annotations

import re
from datetime import date, datetime, timedelta

from .models import Task

WEEKDAY_MAP = {
    "一": 0, "1": 0, "二": 1, "2": 1, "三": 2, "3": 2, "四": 3, "4": 3,
    "五": 4, "5": 4, "六": 5, "6": 5, "日": 6, "天": 6, "7": 6,
}


def _next_weekday(base: date, weekday: int) -> date:
    delta = (weekday - base.weekday()) % 7
    if delta == 0:
        delta = 7
    return base + timedelta(days=delta)


def parse_datetime_cn(text: str, base: date | None = None) -> datetime | None:
    """从中文/数字文本中解析截止时间。

    支持示例：
    - 2026-05-20 23:59
    - 5月20日 22:00
    - 明天晚上10点
    - 下周三 23:59
    - 周五 18:00
    """
    base = base or date.today()
    text = text.strip()

    # 1) ISO 日期
    m = re.search(r"(20\d{2})[-/年.](\d{1,2})[-/月.](\d{1,2})[日号]?\s*(\d{1,2})?[:：点时]?(\d{1,2})?", text)
    if m:
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        hh = int(m.group(4) or 23)
        mm = int(m.group(5) or 59)
        return datetime(y, mo, d, hh, mm)

    # 2) 月日
    m = re.search(r"(\d{1,2})月(\d{1,2})[日号]?\s*(\d{1,2})?[:：点时]?(\d{1,2})?", text)
    if m:
        y = base.year
        mo, d = int(m.group(1)), int(m.group(2))
        hh = int(m.group(3) or 23)
        mm = int(m.group(4) or 59)
        dt = datetime(y, mo, d, hh, mm)
        if dt.date() < base:
            dt = datetime(y + 1, mo, d, hh, mm)
        return dt

    # 3) 明天/后天/今天
    if "后天" in text:
        day = base + timedelta(days=2)
    elif "明天" in text:
        day = base + timedelta(days=1)
    elif "今天" in text:
        day = base
    else:
        day = None

    # 4) 周几/下周几
    wm = re.search(r"(下周|本周|这周|周|星期)([一二三四五六日天1234567])", text)
    if wm:
        weekday = WEEKDAY_MAP[wm.group(2)]
        prefix = wm.group(1)
        if prefix == "下周":
            start_next_week = base + timedelta(days=(7 - base.weekday()))
            day = start_next_week + timedelta(days=weekday)
        elif prefix in ("本周", "这周"):
            day = base - timedelta(days=base.weekday()) + timedelta(days=weekday)
            if day < base:
                day = _next_weekday(base, weekday)
        else:
            day = _next_weekday(base, weekday)

    if day is None:
        return None

    # 5) 时间
    tm = re.search(r"(\d{1,2})[:：](\d{1,2})", text)
    if tm:
        hh, mm = int(tm.group(1)), int(tm.group(2))
    else:
        hm = re.search(r"(\d{1,2})[点时]", text)
        hh = int(hm.group(1)) if hm else 23
        mm = 0 if hm else 59
        if ("晚上" in text or "晚" in text) and hh < 12:
            hh += 12
    return datetime.combine(day, datetime.min.time()).replace(hour=hh, minute=mm)


def parse_estimated_hours(text: str) -> float:
    m = re.search(r"(预计|大概|约|需要|耗时)?\s*(\d+(?:\.\d+)?)\s*(小时|h|H)", text)
    if m:
        return float(m.group(2))
    m = re.search(r"(\d+(?:\.\d+)?)\s*(分钟|min)", text)
    if m:
        return max(0.5, float(m.group(1)) / 60)
    return 2.0


def parse_priority(text: str) -> int:
    if any(w in text for w in ["非常重要", "很重要", "紧急", "必须", "高优先级"]):
        return 5
    if any(w in text for w in ["重要", "尽快", "考试", "DDL", "截止"]):
        return 4
    if any(w in text for w in ["一般", "普通"]):
        return 3
    if any(w in text for w in ["不急", "低优先级"]):
        return 2
    return 3


def parse_task_type(text: str) -> str:
    if "考试" in text or "测验" in text:
        return "复习"
    if "项目" in text or "大作业" in text:
        return "项目"
    if "报告" in text:
        return "报告"
    if "展示" in text or "汇报" in text:
        return "展示"
    return "作业"


def clean_task_name(text: str) -> str:
    # 去掉常见时间、耗时、优先级表达，保留最像任务名的部分。
    t = text.strip()

    # 去掉“课程：任务”中的课程前缀，课程名由 parse_tasks_from_text 单独保存。
    t = re.sub(r"^([^:：\-—]{2,12})[:：\-—]\s*", "", t)

    # 去掉日期、星期、相对时间。注意先匹配“下周三”整体，避免留下“三”。
    t = re.sub(r"((下周|本周|这周|周|星期)[一二三四五六日天1234567]|今天|明天|后天)", "", t)
    t = re.sub(r"(20\d{2}[-/年.]\d{1,2}[-/月.]\d{1,2}[日号]?)", "", t)
    t = re.sub(r"\d{1,2}月\d{1,2}[日号]?", "", t)
    t = re.sub(r"\d{1,2}[:：]\d{1,2}", "", t)
    t = re.sub(r"\d{1,2}[点时]", "", t)

    # 去掉耗时和状态词。
    t = re.sub(r"(预计|大概|约|需要|耗时)?\s*\d+(?:\.\d+)?\s*(小时|h|H|分钟|min)", "", t)
    t = re.sub(r"(截止|DDL|之前|前|提交|完成|非常|很|较|重要|紧急|一般|普通|不急|高优先级|低优先级)", "", t)

    # 去掉多余符号。
    t = re.sub(r"[，,。；;、]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t[:30] if t else "未命名任务"


def parse_tasks_from_text(text: str, base: date | None = None) -> list[Task]:
    """把自然语言多行输入转为任务列表。每行识别为一个任务。"""
    base = base or date.today()
    tasks: list[Task] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        deadline = parse_datetime_cn(line, base=base)
        if deadline is None:
            # 没有识别出 DDL 时，默认安排到 7 天后晚上 23:59，避免丢任务。
            deadline = datetime.combine(base + timedelta(days=7), datetime.min.time()).replace(hour=23, minute=59)

        # 课程名提取：支持“人工智能：完成xxx”或“人工智能-完成xxx”
        course = "未分类"
        cm = re.match(r"^([^:：\-—]{2,12})[:：\-—]", line)
        if cm:
            course = cm.group(1).strip()

        task = Task(
            task_name=clean_task_name(line),
            course=course,
            deadline=deadline,
            estimated_hours=parse_estimated_hours(line),
            priority=parse_priority(line),
            task_type=parse_task_type(line),
            description=line,
        )
        tasks.append(task)
    return tasks
