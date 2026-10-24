"""
SQLite-backed feedback store for ShopEase customer support responses.
Records user ratings (thumbs up / thumbs down) for assistant messages.
Strictly prevents duplicate votes on the same message.
"""

import logging
from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

DEFAULT_FEEDBACK_DB_PATH = Path(__file__).resolve().parent.parent.parent / "feedback.db"


def _get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """Connect to SQLite and ensure feedback table and indexes exist."""
    target_path = db_path or DEFAULT_FEEDBACK_DB_PATH
    conn = sqlite3.connect(str(target_path), check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS message_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            message_id TEXT NOT NULL UNIQUE,
            rating TEXT NOT NULL,
            query TEXT,
            answer TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_feedback_msg_id ON message_feedback(message_id);
    """)
    conn.commit()
    return conn


def save_feedback(
    session_id: str,
    message_id: str,
    rating: str,
    query: str = "",
    answer: str = "",
    db_path: Optional[Path] = None
) -> bool:
    """
    Save user feedback ('up' or 'down') for an assistant message.
    Enforces uniqueness on message_id to prevent duplicate votes.
    Returns True if successfully saved, False if already voted.
    """
    clean_rating = rating.strip().lower()
    if clean_rating not in {"up", "down"}:
        logger.warning("Invalid feedback rating '%s'. Expected 'up' or 'down'.", rating)
        return False

    try:
        with _get_connection(db_path) as conn:
            conn.execute(
                """
                INSERT INTO message_feedback (session_id, message_id, rating, query, answer)
                VALUES (?, ?, ?, ?, ?)
                """,
                (session_id, message_id, clean_rating, query, answer)
            )
            conn.commit()
        logger.info("Feedback '%s' recorded for message %s", clean_rating, message_id)
        return True
    except sqlite3.IntegrityError:
        logger.info("Duplicate vote blocked for message %s (already rated)", message_id)
        return False
    except Exception as exc:
        logger.error("Error saving feedback for message %s: %s", message_id, exc)
        return False


def has_voted(message_id: str, db_path: Optional[Path] = None) -> Optional[str]:
    """
    Check if a message has already been rated.
    Returns the rating string ('up' or 'down') if voted, or None if not yet voted.
    """
    if not message_id:
        return None

    try:
        with _get_connection(db_path) as conn:
            cursor = conn.execute(
                "SELECT rating FROM message_feedback WHERE message_id = ?",
                (message_id,)
            )
            row = cursor.fetchone()
            return row[0] if row else None
    except Exception as exc:
        logger.error("Error checking vote status for message %s: %s", message_id, exc)
        return None


def get_feedback_counts(db_path: Optional[Path] = None) -> Dict[str, int]:
    """
    Aggregate positive, negative, and total feedback counts.
    Returns: {"up": count, "down": count, "total": count}
    """
    try:
        with _get_connection(db_path) as conn:
            cursor = conn.execute("""
                SELECT rating, COUNT(*)
                FROM message_feedback
                GROUP BY rating
            """)
            counts = {row[0]: row[1] for row in cursor.fetchall()}

        up = counts.get("up", 0)
        down = counts.get("down", 0)
        return {"up": up, "down": down, "total": up + down}
    except Exception as exc:
        logger.error("Error aggregating feedback counts: %s", exc)
        return {"up": 0, "down": 0, "total": 0}
