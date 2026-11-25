import streamlit as st
import pandas as pd
import pdfplumber
from PIL import Image

st.set_page_config(page_title="Test", page_icon="📄", layout="wide")
st.title("Step 1: Basic Streamlit OK")

st.header("Step 2: Testing imports")
st.write("streamlit OK")
st.write("pandas OK")
st.write("pdfplumber OK")
st.write("PIL OK")

st.header("Step 3: Testing modules")
try:
    from modules.extractor import extract_text
    st.success("extractor OK")
except Exception as e:
    st.error(f"extractor FAILED: {e}")

try:
    from modules.info_extractor import extract_info
    st.success("info_extractor OK")
except Exception as e:
    st.error(f"info_extractor FAILED: {e}")

try:
    from modules.summarizer import summarize
    st.success("summarizer OK")
except Exception as e:
    st.error(f"summarizer FAILED: {e}")

try:
    from modules.stats import document_stats
    st.success("stats OK")
except Exception as e:
    st.error(f"stats FAILED: {e}")

try:
    from modules.language_detector import detect_language
    st.success("language_detector OK")
except Exception as e:
    st.error(f"language_detector FAILED: {e}")

try:
    from modules.ai_chat import answer_with_context
    st.success("ai_chat OK")
except Exception as e:
    st.error(f"ai_chat FAILED: {e}")

try:
    from modules.tts import synthesize
    st.success("tts OK")
except Exception as e:
    st.error(f"tts FAILED: {e}")

try:
    from modules.smart_highlights import find_highlights
    st.success("smart_highlights OK")
except Exception as e:
    st.error(f"smart_highlights FAILED: {e}")

st.header("Step 4: Testing RapidOCR (slow on first load)")
if st.button("Test OCR engine"):
    with st.spinner("Loading RapidOCR…"):
        try:
            from rapidocr_onnxruntime import RapidOCR
            engine = RapidOCR()
            st.success("RapidOCR loaded OK")
        except Exception as e:
            st.error(f"RapidOCR FAILED: {e}")
