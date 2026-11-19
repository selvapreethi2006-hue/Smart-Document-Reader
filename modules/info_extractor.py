"""Regex-based extraction of structured fields (no fake values)."""

import re

EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")

PHONE_RE = re.compile(
    r"(?:(?:\+?\d{1,3}[\s\-\.]?)?(?:\(?\d{2,4}\)?[\s\-\.]?){1,3}\d{3,4}[\s\-\.]?\d{3,4})"
)

DATE_RE = re.compile(
    r"\b(?:"
    r"\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}"
    r"|"
    r"\d{4}[\/\-\.]\d{1,2}[\/\-\.]\d{1,2}"
    r"|"
    r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{2,4}"
    r"|"
    r"\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4}"
    r")\b",
    re.IGNORECASE,
)

ADDRESS_RE = re.compile(
    r"\b\d{1,6}\s+[A-Za-z0-9\.\-]+(?:\s+[A-Za-z0-9\.\-]+){0,4}"
    r"(?:\s+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|"
    r"Court|Ct|Way|Place|Pl|Terrace|Ter|Circle|Cir|Highway|Hwy))\.?"
    r"(?:,?\s+[A-Za-z\s]+)?(?:,?\s+\d{5}(?:-\d{4})?)?",
    re.IGNORECASE,
)

# Conservative name heuristic: 2–3 Title-Case words, optional middle initial,
# excludes common street/role words to reduce false positives.
NAME_RE = re.compile(
    r"\b([A-Z][a-z]{1,20}(?:\s+[A-Z]\.)?(?:\s+[A-Z][a-z]{1,20}){1,2})\b"
)

_STOP_TOKENS = {
    "Street", "St", "Avenue", "Ave", "Road", "Rd", "Boulevard", "Blvd",
    "Lane", "Ln", "Drive", "Dr", "Court", "Ct", "Way", "Place", "Pl",
    "Terrace", "Ter", "Circle", "Cir", "Highway", "Hwy",
    "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep",
    "Oct", "Nov", "Dec",
}


def _dedupe(seq):
    seen, out = set(), []
    for item in seq:
        key = item.strip()
        if key and key not in seen:
            seen.add(key)
            out.append(key)
    return out


def extract_info(text: str) -> dict:
    """Return a dict of lists. Empty lists mean 'not found' (never fabricated)."""
    if not text or not text.strip():
        return {"names": [], "emails": [], "phones": [], "dates": [], "addresses": []}

    emails = _dedupe(EMAIL_RE.findall(text))
    phones = _dedupe(PHONE_RE.findall(text))
    # Filter phone candidates to plausible digit counts
    phones = [p for p in phones if 7 <= len(re.sub(r"\D", "", p)) <= 15]

    dates = _dedupe(DATE_RE.findall(text))

    raw_addresses = ADDRESS_RE.findall(text)
    addresses = _dedupe([re.sub(r"\s+", " ", a).strip(" ,.") for a in raw_addresses])

    name_candidates = []
    for m in NAME_RE.finditer(text):
        candidate = m.group(1).strip()
        tokens = candidate.split()
        if any(tok in _STOP_TOKENS for tok in tokens):
            continue
        if len(tokens) < 2:
            continue
        name_candidates.append(candidate)
    names = _dedupe(name_candidates)

    return {
        "names": names,
        "emails": emails,
        "phones": phones,
        "dates": dates,
        "addresses": addresses,
    }