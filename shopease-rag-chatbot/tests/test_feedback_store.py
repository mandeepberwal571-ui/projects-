"""
Unit tests for feedback_store.py.
Verifies feedback persistence, duplicate vote prevention, and count aggregation.
Uses temporary SQLite databases to guarantee isolation.
"""

from pathlib import Path
import pytest
from src.ui.feedback_store import get_feedback_counts, has_voted, save_feedback


@pytest.fixture
def temp_db(tmp_path: Path):
    """Temporary SQLite database file path."""
    return tmp_path / "test_feedback.db"


def test_save_and_has_voted(temp_db):
    """Verify saving a rating records successfully and has_voted detects it."""
    session_id = "sess_001"
    message_id = "msg_001"

    assert has_voted(message_id, db_path=temp_db) is None

    # Save thumbs up
    saved = save_feedback(
        session_id=session_id,
        message_id=message_id,
        rating="up",
        query="What is the return window?",
        answer="30 days.",
        db_path=temp_db
    )
    assert saved is True
    assert has_voted(message_id, db_path=temp_db) == "up"


def test_prevent_duplicate_votes(temp_db):
    """Verify voting again on the same message_id is blocked."""
    session_id = "sess_002"
    message_id = "msg_002"

    first_vote = save_feedback(session_id, message_id, "up", db_path=temp_db)
    assert first_vote is True

    # Second vote attempt on same message_id
    second_vote = save_feedback(session_id, message_id, "down", db_path=temp_db)
    assert second_vote is False

    # Rating remains the original 'up'
    assert has_voted(message_id, db_path=temp_db) == "up"


def test_feedback_counts_aggregation(temp_db):
    """Verify aggregated counts match recorded feedback."""
    save_feedback("s1", "m1", "up", db_path=temp_db)
    save_feedback("s1", "m2", "up", db_path=temp_db)
    save_feedback("s2", "m3", "down", db_path=temp_db)

    counts = get_feedback_counts(db_path=temp_db)
    assert counts["up"] == 2
    assert counts["down"] == 1
    assert counts["total"] == 3


def test_invalid_rating_rejected(temp_db):
    """Verify invalid rating strings are rejected."""
    result = save_feedback("s1", "m4", "maybe", db_path=temp_db)
    assert result is False
    assert has_voted("m4", db_path=temp_db) is None
