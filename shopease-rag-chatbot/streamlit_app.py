"""
Streamlit Cloud Entry Point for ShopEase Multimodal RAG Assistant.
Automatically bridges Streamlit Cloud secrets, starts the local FastAPI backend
if needed, and executes the main Streamlit UI.
"""

import os
from pathlib import Path
import runpy
import subprocess
import sys
import time
import httpx
import streamlit as st

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Propagate Streamlit Secrets into os.environ for backend and embedding services
try:
    if hasattr(st, "secrets"):
        for key in ["GEMINI_API_KEY", "API_URL"]:
            if key in st.secrets and key not in os.environ:
                os.environ[key] = str(st.secrets[key]).strip()
except Exception:
    pass

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000").rstrip("/")

# Auto-start backend if running self-contained on localhost (e.g. Streamlit Community Cloud)
if "127.0.0.1" in API_URL or "localhost" in API_URL:
    backend_ready = False
    try:
        resp = httpx.get(f"{API_URL}/health", timeout=1.5)
        if resp.status_code == 200:
            backend_ready = True
    except Exception:
        backend_ready = False

    if not backend_ready:
        # Spawn backend in background
        subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "src.api.main:app", "--host", "127.0.0.1", "--port", "8000"],
            cwd=str(PROJECT_ROOT)
        )
        # Wait up to 15 seconds for startup
        for _ in range(15):
            time.sleep(1.0)
            try:
                check = httpx.get(f"{API_URL}/health", timeout=1.5)
                if check.status_code == 200:
                    break
            except Exception:
                pass

# Execute the primary Streamlit application UI
app_path = PROJECT_ROOT / "src" / "ui" / "app.py"
runpy.run_path(str(app_path), run_name="__main__")
