from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


DEFAULT_DB = Path(__file__).resolve().parents[1] / "emotion_treehole.db"


def get_connection(db_path: Path | str = DEFAULT_DB) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Path | str = DEFAULT_DB) -> None:
    conn = get_connection(db_path)
    with conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS emotion_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                nickname TEXT,
                text TEXT NOT NULL,
                emotion TEXT NOT NULL,
                confidence REAL NOT NULL,
                intensity TEXT NOT NULL,
                is_crisis INTEGER NOT NULL DEFAULT 0,
                reply TEXT NOT NULL
            )
            """
        )
    conn.close()


def save_record(
    text: str,
    analysis: Dict[str, object],
    reply: str,
    nickname: str = "匿名用户",
    is_crisis: bool = False,
    db_path: Path | str = DEFAULT_DB,
) -> None:
    init_db(db_path)
    conn = get_connection(db_path)
    with conn:
        conn.execute(
            """
            INSERT INTO emotion_records
            (created_at, nickname, text, emotion, confidence, intensity, is_crisis, reply)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                nickname or "匿名用户",
                text,
                str(analysis.get("emotion", "平静")),
                float(analysis.get("confidence", 0.0)),
                str(analysis.get("intensity", "低")),
                1 if is_crisis else 0,
                reply,
            ),
        )
    conn.close()


def list_records(limit: int = 100, db_path: Path | str = DEFAULT_DB) -> List[Dict[str, object]]:
    init_db(db_path)
    conn = get_connection(db_path)
    rows = conn.execute(
        """
        SELECT id, created_at, nickname, text, emotion, confidence, intensity, is_crisis, reply
        FROM emotion_records
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows][::-1]


def clear_records(db_path: Path | str = DEFAULT_DB) -> None:
    init_db(db_path)
    conn = get_connection(db_path)
    with conn:
        conn.execute("DELETE FROM emotion_records")
    conn.close()
