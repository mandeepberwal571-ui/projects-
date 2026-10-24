"""
SQLite-backed conversation session store for ShopEase.
Stores text-only conversational turns per session_id.
Image bytes are NEVER stored in the database.
"""

import logging
from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent.parent / "sessions.db"


def _get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """Open an SQLite database connection and ensure the schema exists."""
    target_path = db_path or DEFAULT_DB_PATH
    conn = sqlite3.connect(str(target_path), check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS conversation_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_session_id ON conversation_history(session_id);
    """)
    conn.commit()
    return conn


def add_turn(
    session_id: str,
    role: str,
    content: str,
    db_path: Optional[Path] = None
) -> None:
    """
    Append a conversational turn (user or assistant) for a session.
    Only stores textual content; binary image bytes are never persisted.
    """
    if not session_id or not content:
        return

    clean_content = str(content).strip()
    clean_role = str(role).strip().lower()

    with _get_connection(db_path) as conn:
        conn.execute(
            """
            INSERT INTO conversation_history (session_id, role, content)
            VALUES (?, ?, ?)
            """,
            (session_id, clean_role, clean_content)
        )
        conn.commit()
    logger.debug("Added turn for session %s [%s]: %s...", session_id, clean_role, clean_content[:50])


def get_history(
    session_id: str,
    last_n: int = 5,
    db_path: Optional[Path] = None
) -> List[Dict[str, str]]:
    """
    Retrieve the most recent `last_n` conversational turns for a session in chronological order.
    Returns: [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
    """
    if not session_id or last_n <= 0:
        return []

    with _get_connection(db_path) as conn:
        cursor = conn.execute(
            """
            SELECT role, content
            FROM conversation_history
            WHERE session_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (session_id, last_n)
        )
        rows = cursor.fetchall()

    # Reverse to return in chronological order (earliest to latest)
    chronological = rows[::-1]
    return [{"role": r[0], "content": r[1]} for r in chronological]


def get_history_detailed(
    session_id: str,
    last_n: int = 50,
    db_path: Optional[Path] = None
) -> List[Dict[str, Any]]:
    """
    Retrieve detailed turns including timestamp for the /history/{session_id} API endpoint.
    """
    if not session_id or last_n <= 0:
        return []

    with _get_connection(db_path) as conn:
        cursor = conn.execute(
            """
            SELECT role, content, created_at
            FROM conversation_history
            WHERE session_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (session_id, last_n)
        )
        rows = cursor.fetchall()

    chronological = rows[::-1]
    return [{"role": r[0], "content": r[1], "created_at": str(r[2])} for r in chronological]


def clear_session(
    session_id: str,
    db_path: Optional[Path] = None
) -> bool:
    """Delete all conversation turns for the given session_id."""
    if not session_id:
        return False

    with _get_connection(db_path) as conn:
        conn.execute(
            "DELETE FROM conversation_history WHERE session_id = ?",
            (session_id,)
        )
        conn.commit()
    logger.info("Cleared conversation history for session %s", session_id)
    return True
