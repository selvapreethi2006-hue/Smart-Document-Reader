"""Smart Document Reader & Data Extractor — Streamlit app (final)."""

import os
import re
import json
import streamlit as st
import pandas as pd

from modules.extractor import extract_text
from modules.info_extractor import extract_info
from modules.summarizer import summarize
from modules.exporter import text_to_txt_bytes, info_to_csv_bytes, info_to_json_bytes
from modules.language_detector import detect_language
from modules.stats import document_stats
from modules.report_gen import generate_report
from modules.entity_extractor import extract_entities
from modules.keyword_extractor import extract_keywords, extract_phrases
from modules.sentiment import analyse_sentiment
from modules.doc_compare import compare_documents
from modules.redactor import redact_text
from modules.timeline import build_timeline, timeline_to_csv
from modules.contact_card import build_contacts, card_to_vcard
from modules.anomaly_alerts import detect_anomalies
from modules.duplicate_check import similarity as doc_similarity
from modules.ai_chat import answer_with_context
from modules.tts import synthesize as tts_synthesize
from modules.smart_highlights import find_highlights, highlights_to_csv
from modules.doc_registry import add_to_registry, find_duplicates, clear_registry
from modules.regex_playground import run_regex, COMMON_PATTERNS
from modules.toc_detector import detect_toc

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
        "entities": {}, "keywords": [], "phrases": [],
        "sentiment": {}, "redacted": {}, "timeline": [],
        "contacts": [], "alerts": [],
        "highlights": [], "toc": [],
        "filename": "", "batch": [],
        "chat_messages": [], "chat_history_questions": [],
        "registry": [],
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def reset_state():
    for key in ("extracted_text", "filename"):
        st.session_state[key] = ""
    for key in ("pages", "tables", "batch", "keywords", "phrases",
                "timeline", "contacts", "alerts", "highlights", "toc"):
        st.session_state[key] = []
    for key in ("meta", "info", "summary", "stats", "language",
                "entities", "sentiment", "redacted"):
        st.session_state[key] = {}


def _apply_result(name, result):
    text = result["text"]
    st.session_state.extracted_text = text
    st.session_state.pages = result["pages"]
    st.session_state.tables = result.get("tables", [])
    st.session_state.meta = {
        "page_count": result["page_count"],
        "ocr_pages": result["ocr_pages"],
        "filename": name,
    }
    st.session_state.filename = name
    st.session_state.info = extract_info(text)
    st.session_state.summary = summarize(text)
    st.session_state.stats = document_stats(text)
    st.session_state.language = detect_language(text)
    st.session_state.entities = extract_entities(text)
    st.session_state.keywords = extract_keywords(text)
    st.session_state.phrases = extract_phrases(text)
    st.session_state.sentiment = analyse_sentiment(text)
    st.session_state.redacted = redact_text(text)
    st.session_state.timeline = build_timeline(text)
    st.session_state.contacts = build_contacts(text)
    st.session_state.alerts = detect_anomalies(text, st.session_state.info,
                                                st.session_state.stats)
    st.session_state.highlights = find_highlights(text)
    st.session_state.toc = detect_toc(text)

    st.session_state.registry = add_to_registry(
        st.session_state.registry,
        name, text,
        st.session_state.stats.get("words", 0),
        st.session_state.language.get("name", "—"),
    )
    dups = find_duplicates(st.session_state.registry, text)
    st.session_state.meta["duplicate_count"] = len(dups) if dups else 0


def render_upload():
    st.subheader("1. Upload a document")
    mode = st.radio("Upload mode",
                    ["Single file", "Multiple files (batch)"],
                    horizontal=True)
    if mode == "Single file":
        uploaded = st.file_uploader("Supported: PDF, JPG, JPEG, PNG",
                                    type=ALLOWED_TYPES,
                                    accept_multiple_files=False)
        if uploaded is None:
            return None, None
        size_mb = len(uploaded.getvalue()) / (1024 * 1024)
        if size_mb > MAX_MB:
            st.error(f"File is {size_mb:.1f} MB — max allowed is {MAX_MB} MB.")
            return None, None
        return "single", uploaded

    uploaded_list = st.file_uploader("Upload up to 5 files",
                                     type=ALLOWED_TYPES,
                                     accept_multiple_files=True)
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
        st.warning("No text was extracted. The file may be blank.")
    _apply_result(uploaded.name, result)


def run_batch(uploaded_list):
    st.session_state.batch = []
    for uploaded in uploaded_list:
        try:
            result = extract_text(uploaded.getvalue(), uploaded.name)
            _apply_result(uploaded.name, result)
            st.session_state.batch.append({
                "filename": uploaded.name,
                "word_count": document_stats(result["text"])["words"],
                "language": detect_language(result["text"]).get("name", "—"),
                "error": None,
            })
        except Exception as exc:
            st.session_state.batch.append({
                "filename": uploaded.name, "word_count": 0,
                "language": "—", "error": str(exc),
            })


def render_details():
    meta = st.session_state.meta
    if not meta:
        return
    lang = st.session_state.language
    stats = st.session_state.stats
    senti = st.session_state.sentiment.get("overall") or {}
    alerts = st.session_state.alerts
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("File", meta.get("filename", "—"))
    c2.metric("Pages", meta.get("page_count", 0))
    c3.metric("OCR pages", meta.get("ocr_pages", 0))
    c4.metric("Words", stats.get("words", 0))
    c5.metric("Language", f"{lang.get('name', '—')} ({lang.get('confidence', 0)})")
    if senti:
        c6.metric("Mood", senti.get("label", "—"))
    if alerts:
        st.warning(f"⚠️ {len(alerts)} alert(s) — see **🚨 Alerts** tab")


# ------------------- TABS -------------------

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
            vals = info.get(key, [])
            if vals:
                for v in vals:
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
        rows = t.get("rows") or []
        if not rows:
            st.caption("Empty table.")
            continue
        max_len = max(len(r) for r in rows)
        normalised = [
            [("" if c is None else str(c)).strip() for c in r]
            + [""] * (max_len - len(r))
            for r in rows
        ]
        raw_header = normalised[0]
        header, seen = [], {}
        for ci, name in enumerate(raw_header):
            base = name or f"Column {ci + 1}"
            if base in seen:
                seen[base] += 1
                base = f"{base} ({seen[base]})"
            else:
                seen[base] = 0
            header.append(base)
        body = normalised[1:] or [header]
        df = pd.DataFrame(body, columns=header)
        df.columns = pd.io.common.dedup_names(df.columns,
                                              is_potential_multiindex=False)
        st.dataframe(df, width="stretch")
        st.download_button(f"Download Table {i} (CSV)",
                           data=df.to_csv(index=False).encode("utf-8"),
                           file_name=f"table_{i}.csv",
                           mime="text/csv", key=f"tbl_dl_{i}")


def tab_chat():
    st.markdown("Ask about your document. Follow-ups supported. "
                "Every answer shows source evidence.")
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []
    if "chat_history_questions" not in st.session_state:
        st.session_state.chat_history_questions = []

    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("evidence"):
                with st.expander(f"📑 Source evidence ({len(msg['evidence'])})"):
                    for ev in msg["evidence"]:
                        page = f"Page {ev['page']}" if ev.get("page") else "Page ?"
                        st.markdown(f"**{page}** — score {ev['score']}")
                        st.caption(ev["snippet"])

    question = st.chat_input("Ask a question…")
    if question:
        st.session_state.chat_messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)
        result = answer_with_context(
            st.session_state.extracted_text, question,
            st.session_state.chat_history_questions,
            pages=st.session_state.pages, top_k=3,
        )
        if not result["answers"]:
            content, evidence = "No relevant sentences found.", []
        else:
            tag = " 🔁 *(follow-up)*" if result["is_followup"] else ""
            lines = [f"Here's what I found{tag}:"]
            for i, a in enumerate(result["answers"], 1):
                pg = f" (page {a['page']})" if a["page"] else ""
                lines.append(f"\n**{i}.**{pg} {a['sentence']}")
            content = "\n".join(lines)
            evidence = result["answers"]
            st.session_state.chat_history_questions.append({
                "question": question,
                "answers": [(a["score"], a["sentence"]) for a in evidence],
            })
        st.session_state.chat_messages.append({
            "role": "assistant", "content": content, "evidence": evidence,
        })
        with st.chat_message("assistant"):
            st.markdown(content)
            if evidence:
                with st.expander(f"📑 Source evidence ({len(evidence)})"):
                    for ev in evidence:
                        page = f"Page {ev['page']}" if ev.get("page") else "Page ?"
                        st.markdown(f"**{page}** — score {ev['score']}")
                        st.caption(ev["snippet"])

    if st.session_state.chat_messages:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Clear chat"):
                st.session_state.chat_messages = []
                st.session_state.chat_history_questions = []
                st.rerun()
        with col2:
            if st.session_state.chat_history_questions:
                st.download_button(
                    "⬇️ Q&A history (.json)",
                    data=json.dumps(st.session_state.chat_history_questions,
                                    indent=2, default=str).encode("utf-8"),
                    file_name="qa_history.json", mime="application/json",
                )


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
    top = stats.get("top_words") or []
    if top:
        st.markdown("**Top 10 words**")
        st.bar_chart(pd.DataFrame(top).set_index("word")["count"])


def tab_search():
    query = st.text_input("Search keyword(s)")
    text = st.session_state.extracted_text
    if query and text:
        pat = re.compile(re.escape(query), re.IGNORECASE)
        matches = list(pat.finditer(text))
        st.write(f"**{len(matches)} match(es)**")
        for i, m in enumerate(matches[:50], 1):
            s, e = max(0, m.start()-60), min(len(text), m.end()+60)
            snippet = text[s:e].replace("\n", " ")
            hl = pat.sub(lambda x: f"**{x.group(0)}**", snippet)
            st.markdown(f"{i}. …{hl}…")
    elif query:
        st.info("No text to search.")


def tab_batch():
    batch = st.session_state.batch
    if not batch:
        st.info("Upload multiple files.")
        return
    df = pd.DataFrame([
        {"File": b["filename"], "Words": b["word_count"],
         "Language": b["language"],
         "Status": "✅ OK" if not b["error"] else f"❌ {b['error']}"}
        for b in batch
    ])
    st.dataframe(df, width="stretch")
    st.download_button("⬇️ Batch summary (CSV)",
                       data=df.to_csv(index=False).encode("utf-8"),
                       file_name="batch_summary.csv", mime="text/csv")


def tab_report():
    meta = st.session_state.meta
    if not meta:
        st.info("Upload first.")
        return
    if st.button("📄 Generate PDF report"):
        try:
            pdf_bytes = generate_report(
                meta=meta, summary=st.session_state.summary,
                info=st.session_state.info, stats=st.session_state.stats,
                language=st.session_state.language,
                tables=st.session_state.tables,
                filename=st.session_state.filename,
            )
            st.download_button(
                "⬇️ Download report.pdf", data=pdf_bytes,
                file_name=f"report_{os.path.splitext(st.session_state.filename)[0]}.pdf",
                mime="application/pdf",
            )
        except Exception as exc:
            st.error(f"Report failed: {exc}")


def tab_entities():
    ents = st.session_state.entities
    if not ents or not any(ents.values()):
        st.info("No business entities detected.")
        return
    labels = {
        "invoice_numbers": "🧾 Invoice #", "gst_numbers": "🏛️ GST",
        "pan_numbers": "🪪 PAN", "aadhaar_numbers": "🆔 Aadhaar",
        "ifsc_codes": "🏦 IFSC", "amounts": "💰 Amounts",
        "urls": "🔗 URLs", "percentages": "📊 Percentages",
        "vehicle_numbers": "🚗 Vehicles",
    }
    cols = st.columns(2)
    for i, (key, label) in enumerate(labels.items()):
        vals = ents.get(key, [])
        if not vals:
            continue
        with cols[i % 2]:
            st.markdown(f"**{label}**")
            for v in vals[:25]:
                st.markdown(f"- {v}")


def tab_keywords():
    kws = st.session_state.keywords
    phrases = st.session_state.phrases
    if not kws and not phrases:
        st.info("No keywords.")
        return
    if kws:
        st.markdown("**Top keywords (TF-IDF)**")
        df = pd.DataFrame(kws)
        st.dataframe(df, width="stretch")
        st.bar_chart(df.set_index("term")["score"])
    if phrases:
        st.markdown("**Top phrases**")
        st.dataframe(pd.DataFrame(phrases), width="stretch")


def tab_sentiment():
    senti = st.session_state.sentiment
    if not senti or not senti.get("overall"):
        st.info("No sentiment data.")
        return
    o = senti["overall"]
    c1, c2, c3 = st.columns(3)
    c1.metric("Mood", o["label"])
    c2.metric("Polarity", o["polarity"])
    c3.metric("Subjectivity", o["subjectivity"])
    counts = o.get("counts") or {}
    if counts:
        st.bar_chart(pd.DataFrame(
            [{"Label": k, "Count": v} for k, v in counts.items()]
        ).set_index("Label")["Count"])


def tab_compare():
    st.text_area("Document A", key="cmp_a", height=150)
    st.text_area("Document B", key="cmp_b", height=150)
    if st.button("Compare"):
        a = st.session_state.get("cmp_a", "")
        b = st.session_state.get("cmp_b", "")
        if not a.strip() or not b.strip():
            st.warning("Both needed.")
            return
        result = compare_documents(a, b)
        if not result:
            st.warning("Failed.")
            return
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Overall", f"{result['overall_similarity']*100:.1f}%")
        c2.metric("Char", f"{result['char_similarity']*100:.1f}%")
        c3.metric("Jaccard", f"{result['jaccard_similarity']*100:.1f}%")
        c4.metric("Cosine", f"{result['cosine_similarity']*100:.1f}%")


def tab_redact():
    red = st.session_state.redacted
    if not red or not red.get("redacted"):
        st.info("Upload first.")
        return
    summary = red.get("summary", {})
    if summary:
        st.markdown("**Redacted:** " + ", ".join(
            f"{k}: {v}" for k, v in summary.items()
        ))
    st.text_area("Redacted text", red["redacted"], height=400)
    st.download_button("⬇️ Redacted (.txt)",
                       data=red["redacted"].encode("utf-8"),
                       file_name="redacted.txt", mime="text/plain")


def tab_timeline():
    entries = st.session_state.timeline
    if not entries:
        st.info("No dates found.")
        return
    st.markdown(f"**{len(entries)} date(s) found**")
    for e in entries:
        st.markdown(f"- **{e['display']}** — {e['context']}")
    st.download_button("⬇️ Timeline (CSV)",
                       data=timeline_to_csv(entries).encode("utf-8"),
                       file_name="timeline.csv", mime="text/csv")


def tab_contacts():
    contacts = st.session_state.contacts
    if not contacts:
        st.info("No contact info found.")
        return
    for i, c in enumerate(contacts, 1):
        st.markdown(f"**Contact {i}**")
        if c.get("name"): st.markdown(f"- 👤 Name: {c['name']}")
        if c.get("email"): st.markdown(f"- ✉️ Email: {c['email']}")
        if c.get("phone"): st.markdown(f"- 📞 Phone: {c['phone']}")
        if c.get("address"): st.markdown(f"- 🏠 Address: {c['address']}")
        st.download_button(
            f"⬇️ vCard {i}",
            data=card_to_vcard(c).encode("utf-8"),
            file_name=f"contact_{i}.vcf", mime="text/vcard",
            key=f"vcf_{i}",
        )


def tab_alerts():
    alerts = st.session_state.alerts
    if not alerts:
        st.success("✅ No anomalies detected.")
        return
    for a in alerts:
        icon = {"info": "ℹ️", "warning": "⚠️", "danger": "🚨"}.get(a["level"], "")
        st.markdown(f"### {icon} {a['title']}")
        st.caption(a["detail"])


def tab_reading():
    text = st.session_state.extracted_text
    if not text:
        st.info("Upload first.")
        return
    st.markdown("**Listen to your document** — generates audio from the extracted text.")
    max_chars = st.slider("Characters to read", 500, 10000,
                          min(4000, max(500, len(text))), step=500)
    engine = st.radio("TTS engine",
                      ["gTTS (online, better)", "pyttsx3 (offline, Windows)"],
                      horizontal=True, index=0)
    if st.button("🔊 Generate audio"):
        snippet = text[:max_chars]
        prefer = "gtts" if "gTTS" in engine else "pyttsx3"
        with st.spinner("Generating audio…"):
            result = tts_synthesize(snippet, prefer=prefer)
        if result["audio"]:
            ext = result["format"]
            st.success(f"Generated with **{result['engine']}** ({len(result['audio'])//1024} KB)")
            st.audio(result["audio"], format=f"audio/{ext}")
            st.download_button(
                f"⬇️ Download audio (.{ext})",
                data=result["audio"],
                file_name=f"document_audio.{ext}",
                mime=f"audio/{ext}",
            )
        else:
            st.error("No TTS engine available. Try installing gTTS: "
                     "`python -m pip install gTTS`")


def tab_highlights():
    highlights = st.session_state.highlights
    if not highlights:
        st.info("No highlights detected.")
        return
    st.markdown(f"**{len(highlights)} highlighted sentence(s)**")
    by_cat = {}
    for h in highlights:
        by_cat.setdefault(h["category"], []).append(h)
    for cat, items in by_cat.items():
        with st.expander(f"{cat.title()} ({len(items)})", expanded=True):
            for h in items:
                st.markdown(f"> {h['sentence']}")
                st.caption(f"_{h['reason']}_")
    st.download_button("⬇️ Highlights (CSV)",
                       data=highlights_to_csv(highlights).encode("utf-8"),
                       file_name="highlights.csv", mime="text/csv")


def tab_registry():
    registry = st.session_state.registry
    if not registry:
        st.info("No documents processed yet in this session.")
        return
    st.markdown(f"**{len(registry)} unique document(s) processed**")
    df = pd.DataFrame(registry)[[
        "name", "word_count", "language", "uploads", "first_seen", "last_seen"
    ]]
    st.dataframe(df, width="stretch")
    st.download_button("⬇️ Registry (CSV)",
                       data=df.to_csv(index=False).encode("utf-8"),
                       file_name="doc_registry.csv", mime="text/csv")
    if st.button("🗑️ Clear registry"):
        st.session_state.registry = clear_registry()
        st.rerun()


def tab_regex():
    st.markdown("Test custom regex patterns against the extracted text.")
    text = st.session_state.extracted_text
    if not text:
        st.info("Upload first.")
        return
    common_choice = st.selectbox(
        "Quick pattern (or type your own below)",
        ["— custom —"] + list(COMMON_PATTERNS.keys()),
    )
    default = COMMON_PATTERNS.get(common_choice, "") if common_choice != "— custom —" else ""
    pattern = st.text_input("Regex pattern", value=default)
    flags = st.text_input("Flags (i / m / s)", value="i")
    if pattern:
        result = run_regex(text, pattern, flags)
        if result["error"]:
            st.error(result["error"])
        else:
            st.markdown(f"**{result['count']} match(es)**")
            if result["matches"]:
                df = pd.DataFrame([
                    {"Match": m["match"],
                     "Groups": ", ".join(m["groups"]) or "—",
                     "Context": m["context"]}
                    for m in result["matches"]
                ])
                st.dataframe(df, width="stretch")


def tab_toc():
    toc = st.session_state.toc
    if not toc:
        st.info("No headings detected.")
        return
    st.markdown(f"**{len(toc)} heading(s) found**")
    for item in toc:
        indent = "    " * (item["level"] - 1)
        st.markdown(f"{indent}- {item['title']}")


def tab_export():
    text = st.session_state.extracted_text
    info = st.session_state.info or {}
    if not text:
        st.info("Nothing to export.")
        return
    base = os.path.splitext(st.session_state.filename or "document")[0]
    st.download_button("⬇️ Text (.txt)",
                       data=text_to_txt_bytes(text),
                       file_name=f"{base}.txt", mime="text/plain")
    st.download_button("⬇️ Info (.json)",
                       data=info_to_json_bytes(info),
                       file_name=f"{base}_info.json", mime="application/json")
    st.download_button("⬇️ Info (.csv)",
                       data=info_to_csv_bytes(info),
                       file_name=f"{base}_info.csv", mime="text/csv")


def render_tabs():
    tabs = st.tabs([
        "📄 Text", "🧠 Summary", "🔎 Info", "📊 Tables", "💬 Chat",
        "📈 Stats", "🧾 Entities", "🔑 Keywords", "😊 Sentiment",
        "🔀 Compare", "🕵️ Redact", "⏱️ Timeline", "👤 Contacts",
        "🚨 Alerts", "✨ Highlights", "📚 Outline", "🔊 Listen",
        "🧪 Regex", "📇 Registry", "📄 Report", "🔍 Search",
        "📦 Batch", "⬇️ Download",
    ])
    renderers = [
        tab_text, tab_summary, tab_info, tab_tables, tab_chat,
        tab_stats, tab_entities, tab_keywords, tab_sentiment,
        tab_compare, tab_redact, tab_timeline, tab_contacts,
        tab_alerts, tab_highlights, tab_toc, tab_reading,
        tab_regex, tab_registry, tab_report, tab_search,
        tab_batch, tab_export,
    ]
    for tab, fn in zip(tabs, renderers):
        with tab:
            fn()


def main():
    init_state()
    st.title("📄 Smart Document Reader & Data Extractor")
    st.caption("Upload → Extract → Analyse → Chat → Export.")

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