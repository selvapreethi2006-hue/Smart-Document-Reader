"""Smart Document Reader & Data Extractor — Streamlit app."""

import os
import streamlit as st

from modules.extractor import extract_text
from modules.info_extractor import extract_info
from modules.summarizer import summarize
from modules.exporter import text_to_txt_bytes, info_to_csv_bytes, info_to_json_bytes

ALLOWED_TYPES = ["pdf", "jpg", "jpeg", "png"]
MAX_MB = 25

st.set_page_config(
    page_title="Smart Document Reader & Data Extractor",
    page_icon="📄",
    layout="wide",
)


def init_state():
    defaults = {
        "extracted_text": "",
        "pages": [],
        "meta": {},
        "info": {},
        "summary": {},
        "filename": "",
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def reset_state():
    for key in ("extracted_text", "pages", "meta", "info", "summary", "filename"):
        st.session_state[key] = "" if key in ("extracted_text", "filename") else (
            [] if key == "pages" else {}
        )


def render_upload():
    st.subheader("1. Upload a document")
    uploaded = st.file_uploader(
        "Supported: PDF, JPG, JPEG, PNG",
        type=ALLOWED_TYPES,
        accept_multiple_files=False,
    )
    if uploaded is None:
        return None

    size_mb = len(uploaded.getvalue()) / (1024 * 1024)
    if size_mb > MAX_MB:
        st.error(f"File is {size_mb:.1f} MB — max allowed is {MAX_MB} MB.")
        return None

    ext = os.path.splitext(uploaded.name)[1].lower().lstrip(".")
    if ext not in ALLOWED_TYPES:
        st.error(f"Unsupported file type: .{ext}")
        return None

    return uploaded


def run_extraction(uploaded):
    with st.spinner("Reading document and extracting text…"):
        try:
            result = extract_text(uploaded.getvalue(), uploaded.name)
        except Exception as exc:
            st.error(f"Extraction failed: {exc}")
            return

    if not result["text"].strip():
        st.warning(
            "No text could be extracted. The file may be blank, "
            "low-quality, or Tesseract OCR may not be installed."
        )

    st.session_state.extracted_text = result["text"]
    st.session_state.pages = result["pages"]
    st.session_state.meta = {
        "page_count": result["page_count"],
        "ocr_pages": result["ocr_pages"],
        "filename": uploaded.name,
        "size_mb": round(len(uploaded.getvalue()) / (1024 * 1024), 2),
    }
    st.session_state.filename = uploaded.name
    st.session_state.info = extract_info(result["text"])
    st.session_state.summary = summarize(result["text"])


def render_details():
    meta = st.session_state.meta
    if not meta:
        return
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("File", meta.get("filename", "—"))
    c2.metric("Pages", meta.get("page_count", 0))
    c3.metric("OCR pages", meta.get("ocr_pages", 0))
    c4.metric("Size (MB)", meta.get("size_mb", 0))


def render_tabs():
    tab_text, tab_summary, tab_info, tab_search, tab_export = st.tabs(
        ["📄 Extracted Text", "🧠 Summary", "🔎 Structured Info",
         "🔍 Search", "⬇️ Download"]
    )

    with tab_text:
        if st.session_state.pages:
            if len(st.session_state.pages) > 1:
                for page in st.session_state.pages:
                    with st.expander(f"Page {page['page']}",
                                     expanded=page["page"] == 1):
                        st.text(page["text"] or "— no text on this page —")
            else:
                st.text_area(
                    "Full text",
                    st.session_state.extracted_text,
                    height=400,
                )
        else:
            st.info("Upload and extract a document first.")

    with tab_summary:
        summary = st.session_state.summary
        if summary.get("summary"):
            st.markdown("**Summary**")
            st.write(summary["summary"])
            if summary.get("key_points"):
                st.markdown("**Key points**")
                for point in summary["key_points"]:
                    st.markdown(f"- {point}")
        else:
            st.info("No summary available yet.")

    with tab_info:
        info = st.session_state.info or {}
        if not any(info.get(k) for k in
                   ("names", "emails", "phones", "dates", "addresses")):
            st.info("No structured information detected.")
        else:
            cols = st.columns(2)
            sections = [
                ("👤 Names", "names"),
                ("✉️ Emails", "emails"),
                ("📞 Phones", "phones"),
                ("📅 Dates", "dates"),
                ("🏠 Addresses", "addresses"),
            ]
            for i, (label, key) in enumerate(sections):
                with cols[i % 2]:
                    st.markdown(f"**{label}**")
                    values = info.get(key, [])
                    if values:
                        for v in values:
                            st.markdown(f"- {v}")
                    else:
                        st.caption("Not found")

    with tab_search:
        query = st.text_input("Search keyword(s) in extracted text")
        text = st.session_state.extracted_text
        if query and text:
            import re
            pattern = re.compile(re.escape(query), re.IGNORECASE)
            matches = list(pattern.finditer(text))
            st.write(f"**{len(matches)} match(es) found**")
            if matches:
                snippet_pad = 60
                for i, m in enumerate(matches[:50], start=1):
                    start = max(0, m.start() - snippet_pad)
                    end = min(len(text), m.end() + snippet_pad)
                    snippet = text[start:end].replace("\n", " ")
                    highlighted = pattern.sub(
                        lambda mm: f"**{mm.group(0)}**", snippet
                    )
                    st.markdown(f"{i}. …{highlighted}…")
        elif query:
            st.info("No text available to search.")

    with tab_export:
        text = st.session_state.extracted_text
        info = st.session_state.info or {}
        if not text:
            st.info("Nothing to export yet.")
            return

        base = os.path.splitext(st.session_state.filename or "document")[0]

        st.download_button(
            "Download text (.txt)",
            data=text_to_txt_bytes(text),
            file_name=f"{base}.txt",
            mime="text/plain",
        )
        st.download_button(
            "Download structured info (.json)",
            data=info_to_json_bytes(info),
            file_name=f"{base}_info.json",
            mime="application/json",
        )
        st.download_button(
            "Download structured info (.csv)",
            data=info_to_csv_bytes(info),
            file_name=f"{base}_info.csv",
            mime="text/csv",
        )


def main():
    init_state()

    st.title("📄 Smart Document Reader & Data Extractor")
    st.caption(
        "Upload a PDF or image → extract text (OCR when needed) → "
        "get a summary, structured fields, search, and downloads."
    )

    uploaded = render_upload()
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("🚀 Extract", type="primary", disabled=uploaded is None):
            run_extraction(uploaded)
    with col2:
        if st.button("♻️ Reset"):
            reset_state()
            st.rerun()

    render_details()
    st.divider()
    render_tabs()


if __name__ == "__main__":
    main()