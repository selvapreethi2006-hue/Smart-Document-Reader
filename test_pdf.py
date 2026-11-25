import sys
from modules.extractor import extract_text

if len(sys.argv) < 2:
    print("Usage: python test_pdf.py <path-to-pdf>")
    sys.exit(1)

path = sys.argv[1]
with open(path, "rb") as f:
    data = f.read()

try:
    result = extract_text(data, path)
    print("pages:", result["page_count"])
    print("ocr_pages:", result["ocr_pages"])
    print("text length:", len(result["text"]))
    print("--- first 300 chars ---")
    print(result["text"][:300])
    print("--- end ---")
except Exception as exc:
    print("FAILED:", type(exc).__name__, exc)
