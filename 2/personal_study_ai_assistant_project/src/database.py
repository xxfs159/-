from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "study_profile.db"


def get_connection(db_path: Optional[str | Path] = None) -> sqlite3.Connection:
    """创建 SQLite 连接，并打开外键约束。"""
    path = Path(db_path) if db_path else DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    """初始化数据库表结构。重复执行不会删除已有数据。"""
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            category TEXT DEFAULT '专业课',
            credit REAL DEFAULT 2.0
        );

        CREATE TABLE IF NOT EXISTS exam_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER NOT NULL,
            exam_name TEXT NOT NULL,
            score REAL NOT NULL,
            max_score REAL DEFAULT 100,
            exam_date TEXT NOT NULL,
            FOREIGN KEY(course_id) REFERENCES courses(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS problem_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER NOT NULL,
            knowledge_point TEXT NOT NULL,
            question_title TEXT NOT NULL,
            is_correct INTEGER NOT NULL CHECK(is_correct IN (0, 1)),
            difficulty TEXT DEFAULT '中',
            platform TEXT DEFAULT '自建题库',
            practice_date TEXT NOT NULL,
            time_spent_minutes INTEGER DEFAULT 10,
            wrong_reason TEXT DEFAULT '',
            FOREIGN KEY(course_id) REFERENCES courses(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER NOT NULL,
            knowledge_point TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            note_date TEXT NOT NULL,
            FOREIGN KEY(course_id) REFERENCES courses(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS study_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER NOT NULL,
            start_time TEXT NOT NULL,
            duration_minutes INTEGER NOT NULL,
            activity_type TEXT DEFAULT '复习',
            focus_score INTEGER DEFAULT 4 CHECK(focus_score BETWEEN 1 AND 5),
            remark TEXT DEFAULT '',
            FOREIGN KEY(course_id) REFERENCES courses(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS review_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_week TEXT NOT NULL,
            markdown TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        """
    )
    conn.commit()


def upsert_course(conn: sqlite3.Connection, name: str, category: str = "专业课", credit: float = 2.0) -> int:
    """新增或获取课程 ID。"""
    conn.execute(
        "INSERT OR IGNORE INTO courses(name, category, credit) VALUES (?, ?, ?)",
        (name.strip(), category.strip(), credit),
    )
    conn.commit()
    row = conn.execute("SELECT id FROM courses WHERE name = ?", (name.strip(),)).fetchone()
    if row is None:
        raise ValueError(f"课程创建失败：{name}")
    return int(row["id"])


def insert_problem(
    conn: sqlite3.Connection,
    course_name: str,
    knowledge_point: str,
    question_title: str,
    is_correct: bool,
    difficulty: str,
    platform: str,
    practice_date: str,
    time_spent_minutes: int,
    wrong_reason: str = "",
) -> None:
    course_id = upsert_course(conn, course_name)
    conn.execute(
        """
        INSERT INTO problem_records(
            course_id, knowledge_point, question_title, is_correct, difficulty,
            platform, practice_date, time_spent_minutes, wrong_reason
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            course_id,
            knowledge_point.strip(),
            question_title.strip(),
            int(is_correct),
            difficulty,
            platform,
            practice_date,
            int(time_spent_minutes),
            wrong_reason.strip(),
        ),
    )
    conn.commit()


def insert_study_session(
    conn: sqlite3.Connection,
    course_name: str,
    start_time: str,
    duration_minutes: int,
    activity_type: str,
    focus_score: int,
    remark: str = "",
) -> None:
    course_id = upsert_course(conn, course_name)
    conn.execute(
        """
        INSERT INTO study_sessions(course_id, start_time, duration_minutes, activity_type, focus_score, remark)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (course_id, start_time, int(duration_minutes), activity_type, int(focus_score), remark.strip()),
    )
    conn.commit()


def insert_note(
    conn: sqlite3.Connection,
    course_name: str,
    knowledge_point: str,
    title: str,
    content: str,
    note_date: str,
) -> None:
    course_id = upsert_course(conn, course_name)
    conn.execute(
        """
        INSERT INTO notes(course_id, knowledge_point, title, content, note_date)
        VALUES (?, ?, ?, ?, ?)
        """,
        (course_id, knowledge_point.strip(), title.strip(), content.strip(), note_date),
    )
    conn.commit()


def save_report(conn: sqlite3.Connection, report_week: str, markdown: str, created_at: str) -> None:
    conn.execute(
        "INSERT INTO review_reports(report_week, markdown, created_at) VALUES (?, ?, ?)",
        (report_week, markdown, created_at),
    )
    conn.commit()
