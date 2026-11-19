<<<<<<< HEAD
# Smart Document Reader & Data Extractor

An AI-assisted document processing app built with **Python + Streamlit**.  
Upload a PDF or image, extract text (with OCR fallback for scanned pages),
generate a summary, pull out names / emails / phones / dates / addresses,
search the text, and export the results.

---

## Features

- **Upload** PDF, JPG, JPEG, PNG (validated, size-capped)
- **Text extraction**
  - Digital PDFs → PyMuPDF (`fitz`)
  - Scanned PDFs / images → OpenCV preprocessing + Tesseract OCR
- **Structured info** via regex: names, emails, phones, dates, addresses
  (missing fields are simply empty — never fabricated)
- **Extractive summary** with key points
- **Keyword search** with highlighted snippets
- **Exports**: `.txt`, `.csv`, `.json`

---

## 1. Install prerequisites

### Python 3.9+

Check:
```bash
python --version
```

### Tesseract OCR (required for images / scanned PDFs)

- **Windows:** download the installer from  
  <https://github.com/UB-Mannheim/tesseract/wiki>  
  Default path: `C:\Program Files\Tesseract-OCR\tesseract.exe`
- **macOS:** `brew install tesseract`
- **Ubuntu/Debian:** `sudo apt update && sudo apt install tesseract-ocr`

If Tesseract is not on your `PATH`, set an env var before running:

```bash
# Windows (PowerShell)
$env:TESSERACT_CMD="C:\Program Files\Tesseract-OCR\tesseract.exe"

# macOS / Linux
export TESSERACT_CMD=/usr/local/bin/tesseract
```

The app also auto-detects common install locations.

---

## 2. Set up the environment

```bash
# Clone / copy the project, then:
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

---

## 3. Run the app

```bash
streamlit run app.py
```

Open the URL Streamlit prints (usually <http://localhost:8501>).

---

## 4. How to use

1. Upload a **PDF / JPG / JPEG / PNG**.
2. Click **🚀 Extract**.
3. Review the tabs:
   - **Extracted Text** — full text or per-page view
   - **Summary** — short extractive summary + key points
   - **Structured Info** — names, emails, phones, dates, addresses
   - **Search** — keyword search with highlighted snippets
   - **Download** — export `.txt`, `.csv`, `.json`
4. **♻️ Reset** clears the session.

---

## 5. Notes & limitations

- Regex extraction is heuristic. Names in particular may miss unusual formats
  or include false positives; emails/phones/dates are much more reliable.
- OCR accuracy depends on image quality. Preprocessing (denoise + adaptive
  threshold) is applied automatically, but very noisy scans may need manual
  cleanup.
- Max upload size is 25 MB (change `MAX_MB` in `app.py` to adjust).

---

## 6. Project layout

```
app.py                    # Streamlit UI + orchestration
modules/extractor.py      # PDF / image text extraction
modules/info_extractor.py # Regex-based structured data
modules/summarizer.py     # Extractive summarizer
modules/exporter.py       # TXT / CSV / JSON builders
requirements.txt
.gitignore
```
=======
# Smart-Document-Reader
An AI-powered document reader and data extraction system that extracts text and useful information from documents using Python and OCR technology.
>>>>>>> b5861ab580af6402fd6d2192d9a7f4be89139317
