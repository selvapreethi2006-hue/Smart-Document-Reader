"""Frontend client to communicate with the FastAPI backend."""

import requests
import streamlit as st

API_BASE_URL = "http://127.0.0.1:8000/api"


def _handle_error(prefix, exc):
    """Show a friendly error message for failed API calls."""
    if isinstance(exc, requests.exceptions.ConnectionError):
        st.error(
            f"{prefix}: cannot reach the backend. "
            "Is `uvicorn backend.main:app --reload` running?"
        )
    elif isinstance(exc, requests.exceptions.Timeout):
        st.error(f"{prefix}: request timed out.")
    else:
        st.error(f"{prefix}: {exc}")


def api_get_documents():
    """Fetch all documents from the backend."""
    try:
        r = requests.get(f"{API_BASE_URL}/documents", timeout=10)
        r.raise_for_status()
        return r.json().get("data", [])
    except requests.exceptions.RequestException as exc:
        _handle_error("Fetch failed", exc)
        return []


def api_get_document(doc_id):
    """Fetch a single document (with full text) by ID."""
    try:
        r = requests.get(f"{API_BASE_URL}/documents/{doc_id}", timeout=10)
        r.raise_for_status()
        return r.json().get("data")
    except requests.exceptions.RequestException as exc:
        _handle_error("Load failed", exc)
        return None


def api_save_document(filename, text, summary, info, stats):
    """Send a new document to the backend."""
    payload = {
        "filename": filename,
        "text": text,
        "summary": summary,
        "info": info,
        "stats": stats,
    }
    try:
        r = requests.post(f"{API_BASE_URL}/documents", json=payload, timeout=15)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.RequestException as exc:
        _handle_error("Save failed", exc)
        return None


def api_delete_document(doc_id):
    """Delete a document via the backend."""
    try:
        r = requests.delete(f"{API_BASE_URL}/documents/{doc_id}", timeout=10)
        r.raise_for_status()
        return True
    except requests.exceptions.RequestException as exc:
        _handle_error("Delete failed", exc)
        return False


def api_health_check():
    """Return True if the backend is reachable."""
    try:
        r = requests.get("http://127.0.0.1:8000/", timeout=3)
        return r.status_code == 200
    except requests.exceptions.RequestException:
        return False