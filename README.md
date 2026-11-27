# Smart Document Reader & Data Extractor

An AI-powered document processing application built with **Python + Streamlit**.
Upload PDFs or images → extract text (OCR for scans) → summarize → extract structured
data → chat with your document → export as TXT / CSV / JSON / PDF report.

The project now features a **full 3-tier architecture**:
**Streamlit Frontend (8501) → FastAPI Backend (8000) → Supabase PostgreSQL**.

## Features

### Core
- 📄 **Single & batch upload** — process up to 5 files at once
- 🔍 **Text extraction** — pdfplumber for digital PDFs
- 🖼️ **OCR** — RapidOCR for images and scanned PDFs (no Tesseract required)
- 🧠 **Summary** — extractive summary with key points (offline, no LLM)
- 🔎 **Structured info** — names, emails, phones, dates, addresses
- 🧾 **Entity extraction** — invoices, GST, PAN, Aadhaar, IFSC, amounts, URLs
- 📊 **Table extraction** — pulled from PDFs as DataFrames, downloadable as CSV
- 🔑 **Keywords** — TF-IDF ranked keywords + top phrases
- 😊 **Sentiment** — per-sentence polarity + overall mood
- 📈 **Statistics** — word count, reading time, readability grade, top words
- 🌐 **Language detection** — automatic with confidence score
- 🔀 **Document comparison** — similarity % + unique words
- 🕵️ **PII redaction** — one-click masked version for safe sharing
- ⏱️ **Timeline** — dates sorted chronologically
- 👤 **Contact cards** — auto-built names/emails/phones, exportable as vCard
- 🚨 **Anomaly alerts** — flags PII, large amounts, expired dates
- 🔁 **Duplicate detection** — warns if doc is similar to one you already uploaded
- 📄 **PDF report** — multi-page downloadable report

### AI Chat
- 💬 **Question answering** — ask anything about the document
- 🔁 **Follow-up questions** — uses previous questions for context
- 🧠 **Context-aware responses** — recent Q&A boosts related sentences
- 📑 **Source evidence** — each answer shows page number + snippet

### Backend & Integration
- ☁️ **Cloud Database (Supabase)** — Save, search, and load extracted documents securely to a PostgreSQL cloud database.
- 🚀 **FastAPI Backend** — REST API with GET, POST, and DELETE endpoints.
- 🔗 **Frontend ↔ Backend Integration** — Streamlit communicates with the backend via an API client using HTTP requests.

## Tech Stack

### Frontend
- **Streamlit** — UI and interactive components
- **requests** — API client for backend communication

### Backend
- **FastAPI** — REST API framework
- **Uvicorn** — ASGI web server
- **Pydantic** — Data validation
- **python-dotenv** — Environment variables

### Database
- **Supabase (PostgreSQL)** — Cloud database for storing documents and chat history

### Core Processing
- **pdfplumber + pypdfium2** — PDF text & tables
- **RapidOCR + ONNX Runtime** — image OCR (pure pip, no system install)
- **Pillow + NumPy** — image handling
- **pandas** — data processing
- **langdetect** — language detection
- **textblob** — sentiment
- **fpdf2** — PDF report generation
- **dateparser** — timeline sorting

## Installation

### 1. Install Python Dependencies
```powershell
python -m pip install -r requirements.txt
python -m textblob.download_corpora