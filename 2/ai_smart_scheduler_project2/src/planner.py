from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Iterable

import pandas as pd

from .models import PlanItem, Task, TimeSlot
from .utils import combine, daterange, minutes_between, parse_clock, week_start


def rows_to_tasks(df: pd.DataFrame) -> list[Task]:
    tasks: list[Task] = []
    if df is None or df.empty:
        return tasks
    for _, row in df.iterrows():
        if pd.isna(row.get("task_name", None)):
            continue
        tasks.append(
            Task(
                task_name=str(row.get("task_name", "未命名任务")),
                course=str(row.get("course", "未分类")),
                deadline=pd.to_datetime(row.get("deadline")).to_pydatetime(),
                estimated_hours=float(row.get("estimated_hours", 2)),
                priority=int(row.get("priority", 3)),
                task_type=str(row.get("task_type", "作业")),
                description=str(row.get("description", "")),
            )
        )
    return tasks


def build_busy_slots(course_df: pd.DataFrame, start_day: date, days: int = 7) -> list[TimeSlot]:
    """把每周固定课程展开成具体日期的占用时间段。"""
    busy: list[TimeSlot] = []
    if course_df is None or course_df.empty:
        return busy
    for current in daterange(start_day, days):
        weekday = current.weekday()
        rows = course_df[course_df["weekday"].astype(int) == weekday]
        for _, row in rows.iterrows():
            busy.append(
                TimeSlot(
                    start=combine(current, str(row["start_time"])),
                    end=combine(current, str(row["end_time"])),
                    source="course",
                    note=str(row.get("course_name", "")),
                )
            )
    return sorted(busy, key=lambda s: s.start)


def build_free_slots(free_df: pd.DataFrame, start_day: date, days: int = 7) -> list[TimeSlot]:
    """把每周空闲时间展开成具体日期时间段。"""
    slots: list[TimeSlot] = []
    if free_df is None or free_df.empty:
        # 如果用户没给空闲时间，给一个保守默认值。
        free_df = pd.DataFrame([
            {"weekday": i, "start_time": "19:00", "end_time": "22:00", "energy_level": "medium"}
            for i in range(7)
        ])
    for current in daterange(start_day, days):
        weekday = current.weekday()
        rows = free_df[free_df["weekday"].astype(int) == weekday]
        for _, row in rows.iterrows():
            slots.append(
                TimeSlot(
                    start=combine(current, str(row["start_time"])),
                    end=combine(current, str(row["end_time"])),
                    source="free",
                    note=str(row.get("energy_level", "")),
                )
            )
    return sorted(slots, key=lambda s: s.start)


def subtract_busy_from_free(free_slots: list[TimeSlot], busy_slots: list[TimeSlot]) -> list[TimeSlot]:
    """从空闲时间中扣掉课程/固定事务占用时间。"""
    result: list[TimeSlot] = []
    for slot in free_slots:
        fragments = [(slot.start, slot.end)]
        for busy in busy_slots:
            new_fragments = []
            for s, e in fragments:
                # 无交集
                if busy.end <= s or busy.start >= e:
                    new_fragments.append((s, e))
                    continue
                # 左侧剩余
                if busy.start > s:
                    new_fragments.append((s, min(busy.start, e)))
                # 右侧剩余
                if busy.end < e:
                    new_fragments.append((max(busy.end, s), e))
            fragments = new_fragments
        for s, e in fragments:
            if minutes_between(s, e) >= 30:
                result.append(TimeSlot(s, e, source=slot.source, note=slot.note))
    return sorted(result, key=lambda x: x.start)


def task_score(task: Task, now: datetime) -> float:
    """优先级评分：越紧急、越重要，分数越高。"""
    hours_left = max(1.0, (task.deadline - now).total_seconds() / 3600)
    urgency = 1 / hours_left
    return task.priority * 10 + urgency * 100


def split_minutes(total: int, max_chunk: int = 120, min_chunk: int = 30) -> list[int]:
    """把大任务拆成 30-120 分钟的学习块，防止计划过长难执行。"""
    chunks: list[int] = []
    remaining = total
    while remaining > 0:
        chunk = min(max_chunk, remaining)
        if remaining - chunk < min_chunk and remaining - chunk > 0:
            chunk = remaining
        chunks.append(chunk)
        remaining -= chunk
    return chunks


def generate_plan(
    tasks: list[Task],
    course_df: pd.DataFrame,
    free_df: pd.DataFrame,
    start_day: date | None = None,
    days: int = 7,
) -> tuple[list[PlanItem], list[dict]]:
    """核心规划 Agent：基于 DDL、优先级、课程约束和空闲时间生成一周计划。

    返回：
    - plan_items：可执行的计划项
    - warnings：无法完全安排的任务说明
    """
    start_day = start_day or week_start(date.today())
    now = datetime.now()

    busy = build_busy_slots(course_df, start_day, days)
    free = build_free_slots(free_df, start_day, days)
    available = subtract_busy_from_free(free, busy)

    # 只保留当前之后、DDL之前的槽位
    available = [s for s in available if s.end > now]

    # 任务排序：先按智能评分，再按截止时间
    task_queue = sorted(tasks, key=lambda t: (-task_score(t, now), t.deadline))

    plan: list[PlanItem] = []
    warnings: list[dict] = []

    # 用列表维护剩余可用槽
    slots = available[:]

    for task in task_queue:
        remaining = task.total_minutes
        allocated = 0

        # 持续寻找可用槽，直到任务分钟数全部安排完。
        while remaining > 0:
            placed = False
            target_chunk = min(120, remaining)

            # 尽量安排在 DDL 前，且越早越好；允许使用 30 分钟以上的短碎片。
            candidate_indices = [
                i for i, slot in enumerate(slots)
                if slot.start < task.deadline and min(slot.minutes, minutes_between(slot.start, task.deadline)) >= 30
            ]
            candidate_indices.sort(key=lambda i: (slots[i].start, abs(slots[i].minutes - target_chunk)))

            for idx in candidate_indices:
                slot = slots[idx]
                available_minutes = min(slot.minutes, minutes_between(slot.start, task.deadline))
                chunk_minutes = min(target_chunk, available_minutes)

                if chunk_minutes < 30:
                    continue

                item_start = slot.start
                item_end = item_start + timedelta(minutes=chunk_minutes)

                plan.append(
                    PlanItem(
                        start=item_start,
                        end=item_end,
                        task_name=task.task_name,
                        course=task.course,
                        priority=task.priority,
                        task_type=task.task_type,
                        note=f"DDL: {task.deadline.strftime('%m-%d %H:%M')}",
                    )
                )

                allocated += chunk_minutes
                remaining -= chunk_minutes
                placed = True

                # 更新槽位：已经使用的部分从槽位开头扣除。
                if item_end < slot.end:
                    slots[idx] = TimeSlot(item_end, slot.end, source=slot.source, note=slot.note)
                else:
                    slots.pop(idx)
                break

            if not placed:
                break

        if allocated < task.total_minutes:
            warnings.append(
                {
                    "task_name": task.task_name,
                    "need_hours": round(task.total_minutes / 60, 1),
                    "allocated_hours": round(allocated / 60, 1),
                    "reason": "可用时间不足或任务截止时间过近",
                }
            )

    return sorted(plan, key=lambda p: p.start), warnings


def plan_to_dataframe(plan: Iterable[PlanItem]) -> pd.DataFrame:
    rows = []
    for item in plan:
        rows.append(
            {
                "日期": item.start.strftime("%Y-%m-%d"),
                "开始": item.start.strftime("%H:%M"),
                "结束": item.end.strftime("%H:%M"),
                "任务": item.task_name,
                "课程": item.course,
                "类型": item.task_type,
                "优先级": item.priority,
                "备注": item.note,
                "学习时长(小时)": round((item.end - item.start).total_seconds() / 3600, 2),
            }
        )
    return pd.DataFrame(rows)


def daily_summary(plan_df: pd.DataFrame) -> pd.DataFrame:
    if plan_df.empty:
        return pd.DataFrame(columns=["日期", "学习时长(小时)"])
    return plan_df.groupby("日期", as_index=False)["学习时长(小时)"].sum()
