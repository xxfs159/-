from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Dict, List

import pandas as pd

DIFFICULTY_SCORE = {"易": 1, "中": 2, "难": 3}


def _read_sql(conn, sql: str) -> pd.DataFrame:
    return pd.read_sql_query(sql, conn)


def load_all_data(conn) -> Dict[str, pd.DataFrame]:
    """从 SQLite 读取所有分析所需数据。"""
    return {
        "courses": _read_sql(conn, "SELECT * FROM courses"),
        "scores": _read_sql(
            conn,
            """
            SELECT s.*, c.name AS course_name, c.category
            FROM exam_scores s
            JOIN courses c ON c.id = s.course_id
            """,
        ),
        "problems": _read_sql(
            conn,
            """
            SELECT p.*, c.name AS course_name
            FROM problem_records p
            JOIN courses c ON c.id = p.course_id
            """,
        ),
        "notes": _read_sql(
            conn,
            """
            SELECT n.*, c.name AS course_name
            FROM notes n
            JOIN courses c ON c.id = n.course_id
            """,
        ),
        "sessions": _read_sql(
            conn,
            """
            SELECT ss.*, c.name AS course_name
            FROM study_sessions ss
            JOIN courses c ON c.id = ss.course_id
            """,
        ),
    }


def course_summary(data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """按课程聚合成绩、刷题、学习时长等核心指标。"""
    courses = data["courses"][["id", "name", "category"]].rename(columns={"id": "course_id", "name": "course_name"})
    scores = data["scores"].copy()
    problems = data["problems"].copy()
    sessions = data["sessions"].copy()

    if not scores.empty:
        scores["score_rate"] = scores["score"] / scores["max_score"]
        score_summary = scores.groupby("course_name", as_index=False).agg(
            avg_score=("score_rate", "mean"),
            latest_score=("score", "last"),
        )
    else:
        score_summary = pd.DataFrame(columns=["course_name", "avg_score", "latest_score"])

    if not problems.empty:
        problem_summary = problems.groupby("course_name", as_index=False).agg(
            practice_count=("id", "count"),
            correct_count=("is_correct", "sum"),
            avg_time_per_problem=("time_spent_minutes", "mean"),
        )
        problem_summary["accuracy"] = problem_summary["correct_count"] / problem_summary["practice_count"]
    else:
        problem_summary = pd.DataFrame(columns=["course_name", "practice_count", "correct_count", "avg_time_per_problem", "accuracy"])

    if not sessions.empty:
        session_summary = sessions.groupby("course_name", as_index=False).agg(
            study_minutes=("duration_minutes", "sum"),
            avg_focus=("focus_score", "mean"),
            session_count=("id", "count"),
        )
        session_summary["study_hours"] = session_summary["study_minutes"] / 60
    else:
        session_summary = pd.DataFrame(columns=["course_name", "study_minutes", "avg_focus", "session_count", "study_hours"])

    result = courses.merge(score_summary, on="course_name", how="left")
    result = result.merge(problem_summary, on="course_name", how="left")
    result = result.merge(session_summary, on="course_name", how="left")
    numeric_cols = ["avg_score", "latest_score", "practice_count", "correct_count", "avg_time_per_problem", "accuracy", "study_minutes", "avg_focus", "session_count", "study_hours"]
    for col in numeric_cols:
        if col in result.columns:
            result[col] = result[col].fillna(0)
    return result.sort_values(["accuracy", "avg_score"], ascending=True)


def knowledge_summary(data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """按知识点统计刷题正确率、难度、错因和笔记数量。"""
    problems = data["problems"].copy()
    notes = data["notes"].copy()

    if problems.empty:
        return pd.DataFrame(columns=["course_name", "knowledge_point", "practice_count", "wrong_count", "accuracy", "avg_difficulty", "main_wrong_reason", "note_count"])

    problems["difficulty_value"] = problems["difficulty"].map(DIFFICULTY_SCORE).fillna(2)
    wrong = problems[problems["is_correct"] == 0].copy()
    wrong_reason = (
        wrong[wrong["wrong_reason"].str.len() > 0]
        .groupby(["course_name", "knowledge_point"])["wrong_reason"]
        .agg(lambda x: x.value_counts().index[0] if len(x) else "")
        .reset_index(name="main_wrong_reason")
    )

    grouped = problems.groupby(["course_name", "knowledge_point"], as_index=False).agg(
        practice_count=("id", "count"),
        correct_count=("is_correct", "sum"),
        avg_difficulty=("difficulty_value", "mean"),
        avg_time=("time_spent_minutes", "mean"),
    )
    grouped["wrong_count"] = grouped["practice_count"] - grouped["correct_count"]
    grouped["accuracy"] = grouped["correct_count"] / grouped["practice_count"]

    if not notes.empty:
        note_count = notes.groupby(["course_name", "knowledge_point"], as_index=False).agg(note_count=("id", "count"))
    else:
        note_count = pd.DataFrame(columns=["course_name", "knowledge_point", "note_count"])

    grouped = grouped.merge(wrong_reason, on=["course_name", "knowledge_point"], how="left")
    grouped = grouped.merge(note_count, on=["course_name", "knowledge_point"], how="left")
    grouped["main_wrong_reason"] = grouped["main_wrong_reason"].fillna("暂无集中错因")
    grouped["note_count"] = grouped["note_count"].fillna(0).astype(int)
    return grouped.sort_values(["accuracy", "wrong_count", "avg_difficulty"], ascending=[True, False, False])


def identify_weak_points(data: Dict[str, pd.DataFrame], top_n: int = 5) -> pd.DataFrame:
    """
    识别薄弱知识点。
    评分设计：正确率低、错题数量多、难度高、笔记少，都会提高薄弱程度。
    """
    ks = knowledge_summary(data)
    if ks.empty:
        return ks

    def normalize(series: pd.Series) -> pd.Series:
        min_v, max_v = series.min(), series.max()
        if max_v == min_v:
            return pd.Series([0.5] * len(series), index=series.index)
        return (series - min_v) / (max_v - min_v)

    ks = ks.copy()
    ks["wrong_norm"] = normalize(ks["wrong_count"])
    ks["difficulty_norm"] = normalize(ks["avg_difficulty"])
    ks["note_shortage"] = 1 - normalize(ks["note_count"])
    ks["weakness_score"] = (
        0.45 * (1 - ks["accuracy"]) +
        0.25 * ks["wrong_norm"] +
        0.20 * ks["difficulty_norm"] +
        0.10 * ks["note_shortage"]
    )
    return ks.sort_values("weakness_score", ascending=False).head(top_n)


def weekly_review(data: Dict[str, pd.DataFrame], today: date | None = None) -> Dict[str, object]:
    """生成近 7 天复盘指标。"""
    today = today or date.today()
    start = today - timedelta(days=6)

    problems = data["problems"].copy()
    sessions = data["sessions"].copy()

    if not problems.empty:
        problems["practice_date"] = pd.to_datetime(problems["practice_date"]).dt.date
        week_problems = problems[(problems["practice_date"] >= start) & (problems["practice_date"] <= today)]
    else:
        week_problems = problems

    if not sessions.empty:
        sessions["start_date"] = pd.to_datetime(sessions["start_time"]).dt.date
        week_sessions = sessions[(sessions["start_date"] >= start) & (sessions["start_date"] <= today)]
    else:
        week_sessions = sessions

    total_problems = int(len(week_problems))
    correct = int(week_problems["is_correct"].sum()) if total_problems else 0
    accuracy = correct / total_problems if total_problems else 0

    study_minutes = int(week_sessions["duration_minutes"].sum()) if not week_sessions.empty else 0
    avg_focus = float(week_sessions["focus_score"].mean()) if not week_sessions.empty else 0

    if not week_problems.empty:
        kp_stats = week_problems.groupby(["course_name", "knowledge_point"], as_index=False).agg(
            practice_count=("id", "count"), correct_count=("is_correct", "sum")
        )
        kp_stats["accuracy"] = kp_stats["correct_count"] / kp_stats["practice_count"]
        week_weak = kp_stats.sort_values(["accuracy", "practice_count"], ascending=[True, False]).head(3)
    else:
        week_weak = pd.DataFrame(columns=["course_name", "knowledge_point", "practice_count", "accuracy"])

    return {
        "week_start": start.isoformat(),
        "week_end": today.isoformat(),
        "study_hours": round(study_minutes / 60, 2),
        "total_problems": total_problems,
        "accuracy": round(accuracy, 3),
        "avg_focus": round(avg_focus, 2),
        "weak_points": week_weak,
    }


def learning_habit_summary(data: Dict[str, pd.DataFrame]) -> Dict[str, object]:
    """分析学习习惯：学习频率、专注度、单次时长。"""
    sessions = data["sessions"].copy()
    if sessions.empty:
        return {
            "active_days": 0,
            "avg_session_minutes": 0,
            "avg_focus": 0,
            "suggestion": "暂无学习时长记录，建议先记录至少一周数据。",
        }

    sessions["start_date"] = pd.to_datetime(sessions["start_time"]).dt.date
    active_days = sessions["start_date"].nunique()
    avg_minutes = sessions["duration_minutes"].mean()
    avg_focus = sessions["focus_score"].mean()

    if avg_minutes < 25:
        suggestion = "单次学习时间偏短，可以尝试 25 分钟番茄钟。"
    elif avg_focus < 3.5:
        suggestion = "专注度偏低，建议减少手机干扰并设置固定复习时间。"
    elif active_days < 5:
        suggestion = "学习频率不足，建议每周至少安排 5 天短时复习。"
    else:
        suggestion = "学习习惯较稳定，可以继续保持并增加针对薄弱点的训练。"

    return {
        "active_days": int(active_days),
        "avg_session_minutes": round(float(avg_minutes), 1),
        "avg_focus": round(float(avg_focus), 2),
        "suggestion": suggestion,
    }


def generate_next_week_plan(data: Dict[str, pd.DataFrame]) -> List[Dict[str, str]]:
    """根据薄弱点自动生成下一周学习计划。"""
    weak = identify_weak_points(data, top_n=5)
    plan = []
    weekdays = ["周一", "周二", "周三", "周四", "周五"]
    for idx, row in weak.reset_index(drop=True).iterrows():
        day = weekdays[idx % len(weekdays)]
        kp = row["knowledge_point"]
        course = row["course_name"]
        plan.append(
            {
                "day": day,
                "course": course,
                "task": f"复盘 {kp}：重读笔记 20 分钟 + 完成 5 道同类题 + 整理 1 条错因。",
                "reason": f"该知识点正确率为 {row['accuracy']:.0%}，薄弱分为 {row['weakness_score']:.2f}。",
            }
        )

    plan.append(
        {
            "day": "周六",
            "course": "综合复盘",
            "task": "汇总本周错题，按“概念错误/审题错误/边界遗漏/时间问题”分类。",
            "reason": "通过错因分类定位学习习惯问题。",
        }
    )
    plan.append(
        {
            "day": "周日",
            "course": "综合测试",
            "task": "完成一次 45 分钟综合小测，并把结果录入系统生成下周复盘。",
            "reason": "闭环验证计划是否有效。",
        }
    )
    return plan
