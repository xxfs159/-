from __future__ import annotations

from datetime import date, datetime, time, timedelta
from typing import Iterable

WEEKDAY_CN = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]


def parse_clock(value: str) -> time:
    """把 08:30 这样的字符串转为 time。"""
    value = str(value).strip()
    hour, minute = value.split(":")[:2]
    return time(int(hour), int(minute))


def combine(day: date, clock: str | time) -> datetime:
    if isinstance(clock, str):
        clock = parse_clock(clock)
    return datetime.combine(day, clock)


def week_start(day: date | None = None) -> date:
    """返回指定日期所在周的周一。"""
    day = day or date.today()
    return day - timedelta(days=day.weekday())


def daterange(start: date, days: int) -> Iterable[date]:
    for i in range(days):
        yield start + timedelta(days=i)


def weekday_name(idx: int) -> str:
    return WEEKDAY_CN[int(idx) % 7]


def minutes_between(start: datetime, end: datetime) -> int:
    return max(0, int((end - start).total_seconds() // 60))


def format_dt(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M")
