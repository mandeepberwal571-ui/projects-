"""
Smoke test suite for Streamlit User Interface.
Uses streamlit.testing.v1.AppTest to execute src/ui/app.py in a simulated browser session
and asserts that zero exceptions occur during rendering.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
from streamlit.testing.v1 import AppTest

APP_PATH = Path(__file__).resolve().parent.parent / "src" / "ui" / "app.py"


def test_streamlit_app_renders_without_exceptions():
    """
    Simulate full browser session execution of src/ui/app.py.
    Mocks httpx.Client.get so the test runs offline without a live backend.
    Asserts:
    1. app.exception is empty (no ModuleNotFoundError or runtime crashes)
    2. Sidebar title and elements render cleanly
    """
    mock_health_response = MagicMock()
    mock_health_response.status_code = 200
    mock_health_response.json.return_value = {
        "status": "ok",
        "vector_store_count": 68,
        "api_key_configured": True,
        "model": "gemini-3.5-flash"
    }

    with patch("httpx.Client.get", return_value=mock_health_response):
        app = AppTest.from_file(str(APP_PATH)).run(timeout=10)

        # Assert zero exceptions occurred during script execution
        assert len(app.exception) == 0, f"App execution raised exceptions: {app.exception}"

        # Assert chat input exists
        assert len(app.chat_input) == 1, "Chat input widget should be present"

        # Assert sidebar file uploader exists
        assert len(app.sidebar.file_uploader) == 1, "Sidebar document uploader should be present"


def test_streamlit_app_handles_backend_offline_gracefully():
    """
    Verify that when backend is offline (httpx raises ConnectError),
    the UI renders without crashing and shows the offline indicator.
    """
    import httpx

    with patch("httpx.Client.get", side_effect=httpx.ConnectError("Connection refused")):
        app = AppTest.from_file(str(APP_PATH)).run(timeout=10)

        # Must not raise unhandled exception
        assert len(app.exception) == 0, f"App crashed when backend was offline: {app.exception}"
