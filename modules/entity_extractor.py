"""Business/domain entity extraction: invoice numbers, tax IDs, amounts, URLs."""

import re

# Order matters — more specific first
PATTERNS = {
    "invoice_numbers": re.compile(
        r"\b(?:INV|Invoice|Bill)[\s#:\-]*[A-Z0-9\-]{3,20}\b", re.IGNORECASE
    ),
    "gst_numbers": re.compile(
        r"\b\d{2}[A-Z]{5}\d{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}\b"
    ),
    "pan_numbers": re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b"),
    "aadhaar_numbers": re.compile(r"\b\d{4}\s?\d{4}\s?\d{4}\b"),
    "ifsc_codes": re.compile(r"\b[A-Z]{4}0[A-Z0-9]{6}\b"),
    "amounts": re.compile(
        r"(?:₹|Rs\.?|INR|\$|USD|€|EUR)\s?\d{1,3}(?:[,.]\d{2,3})*(?:[.,]\d{1,2})?"
        r"|\b\d{1,3}(?:[,.]\d{2,3})*(?:[.,]\d{2})\s?(?:₹|Rs\.?|INR|USD)\b",
        re.IGNORECASE,
    ),
    "urls": re.compile(
        r"https?://[\w\-]+(?:\.[\w\-]+)+(?:/[\w\-./?%&=+#]*)?",
        re.IGNORECASE,
    ),
    "percentages": re.compile(r"\b\d{1,3}(?:\.\d{1,2})?\s?%"),
    "vehicle_numbers": re.compile(
        r"\b[A-Z]{2}\s?\d{2}\s?[A-Z]{1,3}\s?\d{4}\b"
    ),
}


def _dedupe(seq):
    seen, out = set(), []
    for item in seq:
        k = item.strip()
        if k and k not in seen:
            seen.add(k)
            out.append(k)
    return out


def extract_entities(text: str) -> dict:
    """Return dict of lists. Empty lists = not found (never fabricated)."""
    if not text or not text.strip():
        return {k: [] for k in PATTERNS}
    out = {}
    for name, pat in PATTERNS.items():
        matches = _dedupe(pat.findall(text))
        # Aadhaar pattern also matches phone-like chunks; keep only 12-digit ones
        if name == "aadhaar_numbers":
            matches = [
                m for m in matches
                if len(re.sub(r"\D", "", m)) == 12
            ]
        out[name] = matches
    return out