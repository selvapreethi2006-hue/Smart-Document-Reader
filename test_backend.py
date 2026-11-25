from modules.extractor import extract_text
from modules.info_extractor import extract_info
from modules.summarizer import summarize
from modules.stats import document_stats

# Test with a simple in-memory "PDF" — we'll use a dummy text extraction
# so this only tests the module imports
print("extract_text import OK")
print("extract_info import OK")
print("summarize import OK")
print("document_stats import OK")

# Quick behaviour test on raw text (no file needed)
sample = """John Smith works at Acme Corp.
Email: john.smith@acme.com. Phone: +91 98765 43210.
Invoice INV-2024-001 dated 15/01/2024 for Rs 45,000.
Address: 123 MG Road, Bangalore 560001.
"""
info = extract_info(sample)
print("info:", info)
summary = summarize(sample)
print("summary:", summary["summary"][:200])
stats = document_stats(sample)
print("words:", stats["words"])
print("ALL OK")
