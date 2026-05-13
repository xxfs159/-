from __future__ import annotations

import random
from datetime import datetime, timedelta

from .database import get_connection, init_db, upsert_course, insert_note, insert_problem, insert_study_session

COURSES = [
    ("人工智能引论", "专业课", 2.5),
    ("数据结构", "专业基础课", 3.0),
    ("高等数学", "公共基础课", 4.0),
]

KNOWLEDGE = {
    "人工智能引论": ["搜索算法", "机器学习基础", "神经网络", "知识表示", "智能体"],
    "数据结构": ["栈和队列", "二叉树", "图搜索", "排序算法", "哈希表"],
    "高等数学": ["极限", "导数", "积分", "多元函数", "级数"],
}


def has_data(conn) -> bool:
    row = conn.execute("SELECT COUNT(*) AS c FROM problem_records").fetchone()
    return bool(row and row["c"] > 0)


def seed_sample_data(force: bool = False) -> None:
    """写入演示数据。默认只在空库时写入，避免覆盖用户自己的数据。"""
    conn = get_connection()
    init_db(conn)
    if has_data(conn) and not force:
        conn.close()
        return

    if force:
        conn.executescript(
            """
            DELETE FROM review_reports;
            DELETE FROM study_sessions;
            DELETE FROM notes;
            DELETE FROM problem_records;
            DELETE FROM exam_scores;
            DELETE FROM courses;
            """
        )
        conn.commit()

    for name, category, credit in COURSES:
        course_id = upsert_course(conn, name, category, credit)
        # 期中 / 单元测验成绩
        base_score = {"人工智能引论": 82, "数据结构": 76, "高等数学": 71}[name]
        for i, exam_name in enumerate(["第1次测验", "期中测验", "第2次测验"]):
            score = max(45, min(98, base_score + random.randint(-8, 8) + i * random.randint(0, 3)))
            exam_date = (datetime.now() - timedelta(days=35 - i * 11)).date().isoformat()
            conn.execute(
                "INSERT INTO exam_scores(course_id, exam_name, score, max_score, exam_date) VALUES (?, ?, ?, 100, ?)",
                (course_id, exam_name, score, exam_date),
            )

    platforms = ["LeetCode", "牛客", "课堂练习", "自建题库"]
    difficulties = ["易", "中", "难"]
    wrong_reasons = ["概念不熟", "审题不清", "边界条件遗漏", "公式记忆不牢", "时间分配不合理", ""]
    today = datetime.now().date()

    for day_offset in range(28):
        date = today - timedelta(days=day_offset)
        for course, _, _ in COURSES:
            # 练习记录：薄弱点特意设置为高数积分、数据结构图搜索、AI搜索算法
            for _ in range(random.randint(1, 3)):
                kp = random.choice(KNOWLEDGE[course])
                if kp in ["积分", "图搜索", "搜索算法"]:
                    correct_prob = 0.48
                    difficulty = random.choice(["中", "难"])
                else:
                    correct_prob = 0.78
                    difficulty = random.choice(difficulties)
                insert_problem(
                    conn,
                    course_name=course,
                    knowledge_point=kp,
                    question_title=f"{kp} 练习题 {random.randint(1, 80)}",
                    is_correct=random.random() < correct_prob,
                    difficulty=difficulty,
                    platform=random.choice(platforms),
                    practice_date=date.isoformat(),
                    time_spent_minutes=random.randint(6, 28),
                    wrong_reason=random.choice(wrong_reasons),
                )

        # 学习时长：工作日略多，周末略少
        for course, _, _ in random.sample(COURSES, k=random.randint(1, 3)):
            duration = random.randint(25, 90)
            focus = random.choices([2, 3, 4, 5], weights=[1, 3, 5, 2])[0]
            start_dt = datetime.combine(date, datetime.min.time()).replace(hour=random.randint(18, 22), minute=random.choice([0, 15, 30]))
            insert_study_session(
                conn,
                course_name=course,
                start_time=start_dt.isoformat(timespec="minutes"),
                duration_minutes=duration,
                activity_type=random.choice(["刷题", "复习", "整理笔记", "预习"]),
                focus_score=focus,
                remark=random.choice(["状态稳定", "中途分心", "效率较高", "需要二刷", ""]),
            )

    # 笔记
    for course, _, _ in COURSES:
        for kp in KNOWLEDGE[course]:
            insert_note(
                conn,
                course_name=course,
                knowledge_point=kp,
                title=f"{kp} 核心概念整理",
                content=f"记录 {kp} 的定义、常见题型、易错点和例题。后续复盘时优先检查错题原因。",
                note_date=(today - timedelta(days=random.randint(1, 20))).isoformat(),
            )

    conn.close()


if __name__ == "__main__":
    seed_sample_data(force=True)
    print("示例学习档案数据库已生成：data/study_profile.db")
