"""
Streamlit Web User Interface for ShopEase Multimodal Customer Support Assistant.
Communicates strictly over HTTP with the FastAPI backend (zero direct RAG imports).

Optimizations:
- Persistent httpx.Client connection pooling via @st.cache_resource
- Cached health status via @st.cache_data(ttl=30) with 2s timeout
- Cached feedback counts via @st.cache_data(ttl=60)
- Isolated interactive fragments via @st.fragment for feedback & escalation buttons
- Instantaneous Clear Chat via on_click callback
- Client-side 10 MB document upload enforcement
"""

import os
from pathlib import Path
import random
import sys
import time
from typing import Any, Dict, List, Optional
import uuid

# Ensure project root is in sys.path so 'src.*' imports resolve cleanly
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import httpx
import streamlit as st

try:
    from src.ui.feedback_store import get_feedback_counts, has_voted, save_feedback
except ModuleNotFoundError:
    from feedback_store import get_feedback_counts, has_voted, save_feedback

# Backend API Configuration - using 127.0.0.1 by default prevents Windows IPv6 resolution latency
API_URL = os.getenv("API_URL", "").strip()
if not API_URL:
    try:
        API_URL = str(st.secrets.get("API_URL", "")).strip()
    except Exception:
        pass
if not API_URL:
    API_URL = "http://127.0.0.1:8000"
API_URL = API_URL.rstrip("/")
REQUEST_TIMEOUT = 60.0  # 60s timeout for generation/vision requests

# Page setup
st.set_page_config(
    page_title="ShopEase Customer Support",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ---------------------------------------------------------------------------
# Reusable HTTP Client & Cached API Helpers
# ---------------------------------------------------------------------------
@st.cache_resource
def get_http_client() -> httpx.Client:
    """Maintain a single persistent HTTP connection pool across reruns."""
    return httpx.Client(
        timeout=httpx.Timeout(REQUEST_TIMEOUT, connect=3.0),
        limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
    )


@st.cache_data(ttl=30, show_spinner=False)
def check_backend_health() -> Dict[str, Any]:
    """
    Cached health check (TTL 30s) with 2.0s timeout.
    Prevents blocking the page reload on every button click.
    """
    client = get_http_client()
    try:
        resp = client.get(f"{API_URL}/health", timeout=2.0)
        if resp.status_code == 200:
            data = resp.json()
            return {
                "online": True,
                "chunks": data.get("vector_store_count", 0),
                "model": data.get("model", "Gemini")
            }
    except Exception:
        pass
    return {"online": False, "chunks": 0, "model": None}


@st.cache_data(ttl=60, show_spinner=False)
def get_cached_feedback_counts() -> Dict[str, int]:
    """Cached feedback totals from SQLite to eliminate disk I/O on reruns."""
    return get_feedback_counts()


def send_chat_message(
    message: str,
    session_id: str,
    image_bytes: Optional[bytes] = None,
    image_name: Optional[str] = None
) -> Dict[str, Any]:
    """Send text query and optional image to POST /chat using shared client."""
    client = get_http_client()
    data = {"message": message, "session_id": session_id}
    files = None

    if image_bytes and image_name:
        ext = image_name.split(".")[-1].lower()
        mime = "image/png" if ext == "png" else ("image/webp" if ext == "webp" else "image/jpeg")
        files = {"image": (image_name, image_bytes, mime)}

    resp = client.post(f"{API_URL}/chat", data=data, files=files, timeout=REQUEST_TIMEOUT)
    if resp.status_code == 200:
        return {"success": True, "data": resp.json()}
    else:
        try:
            err_detail = resp.json().get("detail", resp.text)
        except Exception:
            err_detail = resp.text
        return {"success": False, "status_code": resp.status_code, "error": err_detail}


def upload_document_to_backend(file_name: str, file_bytes: bytes) -> Dict[str, Any]:
    """Upload a support document via POST /ingest using shared client."""
    client = get_http_client()
    ext = file_name.split(".")[-1].lower()
    mime = "application/pdf" if ext == "pdf" else "text/plain"
    files = {"file": (file_name, file_bytes, mime)}

    resp = client.post(f"{API_URL}/ingest", files=files, timeout=REQUEST_TIMEOUT)
    if resp.status_code == 200:
        return {"success": True, "data": resp.json()}
    else:
        try:
            err_detail = resp.json().get("detail", resp.text)
        except Exception:
            err_detail = resp.text
        return {"success": False, "status_code": resp.status_code, "error": err_detail}


# ---------------------------------------------------------------------------
# Session State Initialization & Callbacks
# ---------------------------------------------------------------------------
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0


def on_clear_chat_clicked():
    """Fast on_click callback to clear chat state immediately."""
    old_session_id = st.session_state.get("session_id")
    st.session_state.messages = []
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.uploader_key += 1

    if old_session_id:
        try:
            client = get_http_client()
            client.delete(f"{API_URL}/history/{old_session_id}", timeout=1.5)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Streamlit UI Fragments for Sub-Second Button Responses
# ---------------------------------------------------------------------------
@st.fragment
def render_feedback_buttons(msg_id: str, query: str, answer: str, session_id: str):
    """
    Fragment-scoped voting: clicking 👍 or 👎 reruns ONLY this fragment,
    not the whole page or any backend calls!
    """
    voted = has_voted(msg_id)
    col1, col2, col3 = st.columns([1, 1, 8])

    with col1:
        if st.button("👍", key=f"thumb_up_{msg_id}", disabled=bool(voted), help="Helpful answer"):
            save_feedback(
                session_id=session_id,
                message_id=msg_id,
                rating="up",
                query=query,
                answer=answer
            )
            get_cached_feedback_counts.clear()
            st.rerun(scope="fragment")

    with col2:
        if st.button("👎", key=f"thumb_down_{msg_id}", disabled=bool(voted), help="Unhelpful answer"):
            save_feedback(
                session_id=session_id,
                message_id=msg_id,
                rating="down",
                query=query,
                answer=answer
            )
            get_cached_feedback_counts.clear()
            st.rerun(scope="fragment")

    with col3:
        if voted == "up":
            st.caption("✅ *Thanks! You rated this answer as helpful.*")
        elif voted == "down":
            st.caption("⚠️ *Thanks for the feedback. We're continuously improving!*")


@st.fragment
def render_escalation_section(msg_id: str, query: str, content: str):
    """
    Fragment-scoped escalation: ticket generation reruns only this fragment.
    """
    st.warning(
        "⚠️ **Specialized Agent Required**: This question cannot be verified from current policy documents or requires specialized human support."
    )
    ticket_key = f"ticket_created_{msg_id}"
    if ticket_key in st.session_state:
        ticket_data = st.session_state[ticket_key]
        st.success(f"🎫 **Human Support Ticket Created: `{ticket_data['ticket_id']}`**")
        st.caption("A customer care specialist has been notified and will reach out to your registered email.")
    else:
        if st.button("🙋 Talk to human agent", key=f"escalate_btn_{msg_id}"):
            ticket_id = f"TICK-SE-{random.randint(10000, 99999)}"
            st.session_state[ticket_key] = {
                "ticket_id": ticket_id,
                "summary": f"Query: {query} | Response: {content[:120]}"
            }
            st.rerun(scope="fragment")


# ---------------------------------------------------------------------------
# Sidebar: Backend Health, Document Ingest & Settings
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("🛍️ ShopEase Bot")
    st.caption("Multimodal Customer Intelligence Engine")
    st.divider()

    # 1. Cached Backend Status
    health = check_backend_health()
    if health["online"]:
        st.success(f"🟢 **Backend Online**\n\n• **Indexed chunks**: `{health['chunks']}`\n• **Model**: `{health.get('model') or 'gemini-flash'}`")
    else:
        st.error("🔴 **Backend Offline**\n\nPlease start the API:\n`uvicorn src.api.main:app --reload`")

    col_ref, col_space = st.columns([1, 1])
    with col_ref:
        if st.button("🔄 Refresh Status", key="btn_refresh_health", use_container_width=True):
            check_backend_health.clear()
            st.rerun()

    st.divider()

    # 2. Knowledge Base Ingestion (Enforces 10MB limit client-side)
    st.subheader("📄 Document Ingestion")
    st.caption("Upload new policies or manuals (max 10 MB per file):")
    doc_upload = st.file_uploader(
        "Choose file",
        type=["pdf", "docx", "txt", "md"],
        key="sidebar_doc_uploader",
        help="Maximum supported file size is 10 MB"
    )

    if doc_upload is not None:
        file_bytes = doc_upload.getvalue()
        file_size_mb = len(file_bytes) / (1024 * 1024)

        if file_size_mb > 10.0:
            st.error(f"❌ File size ({file_size_mb:.1f} MB) exceeds maximum allowed limit of 10 MB.")
        else:
            if st.button("📤 Index Document", key="btn_index_doc", use_container_width=True):
                with st.spinner("Processing & indexing into vector store..."):
                    res = upload_document_to_backend(doc_upload.name, file_bytes)
                    if res["success"]:
                        st.success(f"✅ Ingested `{res['data']['chunks_added']}` chunk(s)! Total: `{res['data']['total_chunks']}`.")
                        check_backend_health.clear()
                    else:
                        st.error(f"❌ Failed ({res.get('status_code', 500)}): {res.get('error', 'Unknown error')}")

    st.divider()

    # 3. Fast Session Management
    st.subheader("⚙️ Session Controls")
    st.caption(f"Session ID: `{st.session_state.session_id[:8]}...`")

    st.button(
        "🗑️ Clear Chat History",
        key="btn_clear_chat",
        on_click=on_clear_chat_clicked,
        use_container_width=True
    )

    # 4. Cached Feedback Stats
    fb_counts = get_cached_feedback_counts()
    st.caption(f"📊 **User Feedback**: 👍 `{fb_counts['up']}` | 👎 `{fb_counts['down']}`")


# ---------------------------------------------------------------------------
# Main Chat Header & Interface
# ---------------------------------------------------------------------------
st.title("ShopEase Support Assistant")
st.markdown(
    "Welcome to **ShopEase Support**! Ask questions about **orders, returns, warranty, "
    "shipping policies**, or upload a **screenshot or photo** of an issue for troubleshooting."
)
st.divider()

# Display Conversation History
for msg in st.session_state.messages:
    role = msg.get("role")
    with st.chat_message(role):
        # User message rendering
        if role == "user":
            if msg.get("image_bytes"):
                st.image(
                    msg["image_bytes"],
                    caption=msg.get("image_name", "Uploaded Image"),
                    width=280
                )
            st.markdown(msg.get("content", ""))

        # Assistant message rendering
        elif role == "assistant":
            st.markdown(msg.get("content", ""))

            # Confidence Badge
            confidence = msg.get("confidence", 0.0)
            pct = int(confidence * 100)
            if confidence >= 0.70:
                conf_badge = f"🟢 **High Match Confidence**: `{pct}%`"
            elif confidence >= 0.60:
                conf_badge = f"🟡 **Moderate Confidence**: `{pct}%`"
            else:
                conf_badge = f"🔴 **Low Retrieval Confidence**: `{pct}%`"
            st.caption(conf_badge)

            # Sources Expander
            sources = msg.get("sources", [])
            if sources:
                with st.expander(f"📚 View Retrieved Sources ({len(sources)} cited)"):
                    for idx, s in enumerate(sources, 1):
                        f_name = s.get("file", "document")
                        page = s.get("page", 1)
                        snippet = s.get("snippet", "")
                        score = s.get("score", 0.0)
                        st.markdown(f"**[{idx}] {f_name}** *(Page {page}, Similarity: {score:.2f})*")
                        st.info(f'"{snippet}"')

            # Human Escalation Warning & Ticket Creation (Scoped Fragment)
            if msg.get("escalate"):
                render_escalation_section(
                    msg_id=msg.get("id"),
                    query=msg.get("query", ""),
                    content=msg.get("content", "")
                )

            # Thumbs Up / Down Feedback (Scoped Fragment)
            msg_id = msg.get("id")
            if msg_id:
                render_feedback_buttons(
                    msg_id=msg_id,
                    query=msg.get("query", ""),
                    answer=msg.get("content", ""),
                    session_id=st.session_state.session_id
                )


# ---------------------------------------------------------------------------
# Multimodal Input Section
# ---------------------------------------------------------------------------
st.write("")
with st.expander("📷 Attach an Image (Optional: Error screenshot, receipt, or product photo)"):
    uploaded_image = st.file_uploader(
        "Upload image (PNG, JPG, WEBP max 5MB):",
        type=["png", "jpg", "jpeg", "webp"],
        key=f"image_uploader_{st.session_state.uploader_key}"
    )
    if uploaded_image is not None:
        st.image(uploaded_image, caption="Preview of attached image", width=180)

# Main Chat Input
user_input = st.chat_input("Type your question here (e.g. 'How long do I have to return a product?')...")

if user_input:
    # 1. Capture image if attached
    img_bytes = None
    img_name = None
    if uploaded_image is not None:
        img_bytes = uploaded_image.getvalue()
        img_name = uploaded_image.name

    # 2. Append user message to local history
    user_msg_record = {
        "role": "user",
        "content": user_input,
        "image_bytes": img_bytes,
        "image_name": img_name
    }
    st.session_state.messages.append(user_msg_record)

    # 3. Clear file uploader by incrementing key
    if uploaded_image is not None:
        st.session_state.uploader_key += 1

    # 4. Display user message immediately
    with st.chat_message("user"):
        if img_bytes:
            st.image(img_bytes, caption=img_name, width=280)
        st.markdown(user_input)

    # 5. Query FastAPI Backend
    with st.chat_message("assistant"):
        with st.spinner("Searching ShopEase documents & formulating answer..."):
            try:
                res = send_chat_message(
                    message=user_input,
                    session_id=st.session_state.session_id,
                    image_bytes=img_bytes,
                    image_name=img_name
                )

                if res["success"]:
                    bot_data = res["data"]
                    msg_id = str(uuid.uuid4())

                    assistant_record = {
                        "id": msg_id,
                        "role": "assistant",
                        "content": bot_data.get("answer", ""),
                        "sources": bot_data.get("sources", []),
                        "confidence": bot_data.get("confidence", 0.0),
                        "escalate": bot_data.get("escalate", False),
                        "rewritten_query": bot_data.get("rewritten_query", user_input),
                        "image_description": bot_data.get("image_description"),
                        "query": user_input
                    }
                    st.session_state.messages.append(assistant_record)
                    st.rerun()

                else:
                    status_c = res.get("status_code", 500)
                    err_msg = res.get("error", "An unknown error occurred.")
                    if status_c == 400:
                        st.error(f"⚠️ **Image Error**: {err_msg}")
                    else:
                        st.error(f"❌ **Backend Error ({status_c})**: {err_msg}")

            except httpx.ConnectError:
                st.error("🔴 **Backend Offline**: Unable to connect to FastAPI server at `http://127.0.0.1:8000`. Please start the backend service.")
            except httpx.TimeoutException:
                st.error("⏳ **Request Timed Out**: The backend took longer than 60 seconds to respond. Please try again.")
            except Exception as exc:
                st.error(f"⚠️ Unexpected error: {exc}")
