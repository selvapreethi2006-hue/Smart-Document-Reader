"""Smart Document Reader & Data Extractor — Streamlit app (v2).
Adds: batch upload, tables, chat Q&A, language detection, stats, word chart."""

import os
import re
import streamlit as st
import pandas as pd

from modules.extractor import extract_text
from modules.info_extractor import extract_info
from modules.summarizer import summarize
from modules.exporter import text_to_txt_bytes, info_to_csv_bytes, info_to_json_bytes
from modules.language_detector import detect_language
from modules.stats import document_stats
from modules.qa_engine import answer_question

ALLOWED_TYPES = ["pdf", "jpg", "jpeg", "png"]
MAX_MB = 25

st.set_page_config(
    page_title="Smart Document Reader & Data Extractor",
    page_icon="📄",
    layout="wide",
)


def init_state():
    defaults = {
        "extracted_text": "", "pages": [], "tables": [], "meta": {},
        "info": {}, "summary": {}, "stats": {}, "language": {},
        "filename": "", "batch": [],
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def reset_state():
    for key in ("extracted_text", "filename"):
        st.session_state[key] = ""
    for key in ("pages", "tables", "batch"):
        st.session_state[key] = []
    for key in ("meta", "info", "summary", "stats", "language"):
        st.session_state[key] = {}


def _apply_result(name, result):
    st.session_state.extracted_text = result["text"]
    st.session_state.pages = result["pages"]
    st.session_state.tables = result.get("tables", [])
    st.session_state.meta = {
        "page_count": result["page_count"],
        "ocr_pages": result["ocr_pages"],
        "filename": name,
    }
    st.session_state.filename = name
    st.session_state.info = extract_info(result["text"])
    st.session_state.summary = summarize(result["text"])
    st.session_state.stats = document_stats(result["text"])
    st.session_state.language = detect_language(result["text"])


def render_upload():
    st.subheader("1. Upload a document")
    mode = st.radio(
        "Upload mode",
        ["Single file", "Multiple files (batch)"],
        horizontal=True,
    )
    if mode == "Single file":
        uploaded = st.file_uploader(
            "Supported: PDF, JPG, JPEG, PNG",
            type=ALLOWED_TYPES,
            accept_multiple_files=False,
        )
        if uploaded is None:
            return None, None
        size_mb = len(uploaded.getvalue()) / (1024 * 1024)
        if size_mb > MAX_MB:
            st.error(f"File is {size_mb:.1f} MB — max allowed is {MAX_MB} MB.")
            return None, None
        return "single", uploaded

    uploaded_list = st.file_uploader(
        "Upload up to 5 files (PDF, JPG, JPEG, PNG)",
        type=ALLOWED_TYPES,
        accept_multiple_files=True,
    )
    if not uploaded_list:
        return None, None
    if len(uploaded_list) > 5:
        st.error("Please upload 5 or fewer files per batch.")
        return None, None
    return "batch", uploaded_list


def run_single(uploaded):
    with st.spinner("Extracting text…"):
        try:
            result = extract_text(uploaded.getvalue(), uploaded.name)
        except Exception as exc:
            st.error(f"Extraction failed: {exc}")
            return
    if not result["text"].strip():
        st.warning("No text was extracted. The file may be blank or low-quality.")
    _apply_result(uploaded.name, result)


def run_batch(uploaded_list):
    st.session_state.batch = []
    for uploaded in uploaded_list:
        try:
            result = extract_text(uploaded.getvalue(), uploaded.name)
            _apply_result(uploaded.name, result)
            st.session_state.batch.append({
                "filename": uploaded.name,
                "text": result["text"],
                "word_count": document_stats(result["text"])["words"],
                "language": detect_language(result["text"]).get("name", "—"),
                "error": None,
            })
        except Exception as exc:
            st.session_state.batch.append({
                "filename": uploaded.name, "text": "", "word_count": 0,
                "language": "—", "error": str(exc),
            })


def render_details():
    meta = st.session_state.meta
    if not meta:
        return
    lang = st.session_state.language
    stats = st.session_state.stats
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("File", meta.get("filename", "—"))
    c2.metric("Pages", meta.get("page_count", 0))
    c3.metric("OCR pages", meta.get("ocr_pages", 0))
    c4.metric("Words", stats.get("words", 0))
    c5.metric("Language", f"{lang.get('name', '—')} ({lang.get('confidence', 0)})")


def _safe_df(rows):
    """Build a DataFrame with guaranteed-unique column names."""
    if not rows:
        return pd.DataFrame()
    max_len = max(len(r) for r in rows)
    normalised = [
        [("" if cell is None else str(cell)).strip() for cell in r]
        + [""] * (max_len - len(r))
        for r in rows
    ]
    raw_header = normalised[0]
    header, seen = [], {}
    for col_idx, name in enumerate(raw_header):
        base = name if name else f"Column {col_idx + 1}"
        if base in seen:
            seen[base] += 1
            base = f"{base} ({seen[base]})"
        else:
            seen[base] = 0
        header.append(base)
    body = normalised[1:]
    if not body:
        body = [header]
        header = [f"Field {j + 1}" for j in range(max_len)]
    df = pd.DataFrame(body, columns=header)
    # Final safety: dedupe any duplicate column names pandas picked up
    final_cols, seen_cols = [], {}
    for c in df.columns:
        if c in seen_cols:
            seen_cols[c] += 1
            final_cols.append(f"{c} ({seen_cols[c]})")
        else:
            seen_cols[c] = 0
            final_cols.append(c)
    df.columns = final_cols
    return df


def tab_text():
    if st.session_state.pages:
        if len(st.session_state.pages) > 1:
            for page in st.session_state.pages:
                with st.expander(f"Page {page['page']}",
                                 expanded=page["page"] == 1):
                    st.text(page["text"] or "— no text on this page —")
        else:
            st.text_area("Full text", st.session_state.extracted_text, height=400)
    else:
        st.info("Upload and extract a document first.")


def tab_summary():
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


def tab_info():
    info = st.session_state.info or {}
    keys = ("names", "emails", "phones", "dates", "addresses")
    if not any(info.get(k) for k in keys):
        st.info("No structured information detected.")
        return
    cols = st.columns(2)
    sections = [
        ("👤 Names", "names"), ("✉️ Emails", "emails"),
        ("📞 Phones", "phones"), ("📅 Dates", "dates"),
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


def tab_tables():
    tables = st.session_state.tables
    if not tables:
        st.info("No tables detected in this document.")
        return
    for i, t in enumerate(tables, start=1):
        st.markdown(f"**Table {i} (page {t['page']})**")
        df = _safe_df(t.get("rows") or [])
        if df.empty:
            st.caption("Empty table.")
            continue
        st.dataframe(df, width="stretch")
        st.download_button(
            f"Download Table {i} (CSV)",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name=f"table_{i}.csv",
            mime="text/csv",
            key=f"tbl_dl_{i}",
        )


def tab_chat():
    st.markdown("Ask a question about the document. "
                "The app finds the most relevant sentences — no internet, no LLM.")
    question = st.text_input("Your question", key="qa_question")
    if not question:
        st.caption("Example: 'What is the invoice number?' or 'Who is the sender?'")
        return
    results = answer_question(st.session_state.extracted_text, question)
    if not results:
        st.warning("No relevant sentences found for that question.")
        return
    for i, (score, sentence) in enumerate(results, start=1):
        st.markdown(f"**Answer {i}** (match score: {score:.2f})")
        st.write(sentence)
        st.divider()


def tab_stats():
    stats = st.session_state.stats
    if not stats or stats.get("words", 0) == 0:
        st.info("No statistics available yet.")
        return
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Characters", stats["characters"])
    c2.metric("Words", stats["words"])
    c3.metric("Sentences", stats["sentences"])
    c4.metric("Unique words", stats["unique_words"])
    c5, c6, c7 = st.columns(3)
    c5.metric("Paragraphs", stats["paragraphs"])
    c6.metric("Reading time", f"{stats['reading_time_min']} min")

    readability = stats.get("readability") or {}
    if readability:
        c7.metric("Reading ease", f"{readability['flesch_ease']} / 100",
                  readability["flesch_label"])
        st.caption(f"Flesch-Kincaid Grade Level: {readability['fk_grade']}")

    top = stats.get("top_words") or []
    if top:
        st.markdown("**Top 10 most frequent words**")
        df = pd.DataFrame(top)
        st.bar_chart(df.set_index("word")["count"])


def tab_search():
    query = st.text_input("Search keyword(s) in extracted text")
    text = st.session_state.extracted_text
    if query and text:
        pattern = re.compile(re.escape(query), re.IGNORECASE)
        matches = list(pattern.finditer(text))
        st.write(f"**{len(matches)} match(es) found**")
        if matches:
            for i, m in enumerate(matches[:50], start=1):
                start = max(0, m.start() - 60)
                end = min(len(text), m.end() + 60)
                snippet = text[start:end].replace("\n", " ")
                highlighted = pattern.sub(lambda mm: f"**{mm.group(0)}**", snippet)
                st.markdown(f"{i}. …{highlighted}…")
    elif query:
        st.info("No text available to search.")


def tab_batch():
    batch = st.session_state.batch
    if not batch:
        st.info("Upload multiple files and click Extract to see batch results here.")
        return
    df = pd.DataFrame([
        {
            "File": b["filename"],
            "Words": b["word_count"],
            "Language": b["language"],
            "Status": "✅ OK" if not b["error"] else f"❌ {b['error']}",
        }
        for b in batch
    ])
    st.dataframe(df, width="stretch")
    st.download_button(
        "Download batch summary (CSV)",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name="batch_summary.csv",
        mime="text/csv",
    )


def tab_export():
    text = st.session_state.extracted_text
    info = st.session_state.info or {}
    if not text:
        st.info("Nothing to export yet.")
        return
    base = os.path.splitext(st.session_state.filename or "document")[0]
    st.download_button("Download text (.txt)",
                       data=text_to_txt_bytes(text),
                       file_name=f"{base}.txt", mime="text/plain")
    st.download_button("Download structured info (.json)",
                       data=info_to_json_bytes(info),
                       file_name=f"{base}_info.json", mime="application/json")
    st.download_button("Download structured info (.csv)",
                       data=info_to_csv_bytes(info),
                       file_name=f"{base}_info.csv", mime="text/csv")


def render_tabs():
    tabs = st.tabs([
        "📄 Text", "🧠 Summary", "🔎 Info", "📊 Tables",
        "💬 Chat", "📈 Stats", "🔍 Search", "📦 Batch", "⬇️ Download",
    ])
    renderers = [
        tab_text, tab_summary, tab_info, tab_tables,
        tab_chat, tab_stats, tab_search, tab_batch, tab_export,
    ]
    for tab, fn in zip(tabs, renderers):
        with tab:
            fn()


def main():
    init_state()
    st.title("📄 Smart Document Reader & Data Extractor")
    st.caption("Upload → Extract → Summarize → Chat → Export.")

    mode, uploaded = render_upload()
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚀 Extract", type="primary", disabled=uploaded is None):
            if mode == "single":
                run_single(uploaded)
            else:
                run_batch(uploaded)
    with col2:
        if st.button("♻️ Reset"):
            reset_state()
            st.rerun()

    render_details()
    st.divider()
    render_tabs()


if __name__ == "__main__":
    main()