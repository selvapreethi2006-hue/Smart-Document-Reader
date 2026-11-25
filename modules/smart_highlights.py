"""Auto-highlight important sentences: definitions, numbers, actions, facts."""

import re

# Sentence-likely-important markers
IMPORTANT_MARKERS = {
    "definition": [
        r"\b(is|are|means|refers to|is defined as|is known as)\b",
    ],
    "action": [
        r"\b(must|should|shall|required|mandatory|important|note that|please)\b",
    ],
    "numbers": [
        r"\b\d+[\.,]?\d*\s?(?:%|percent|rupees|dollars|inr|usd|kg|km|m|gb|mb)\b",
        r"\b(?:₹|Rs\.?|INR|\$)\s?\d",
    ],
    "dates": [
        r"\b\d{1,2}[/\-.]\d{1,2}[/\-.]\d{2,4}\b",
        r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{2,4}\b",
    ],
    "conclusion": [
        r"\b(therefore|thus|hence|in conclusion|in summary|as a result|consequently)\b",
    ],
    "warning": [
        r"\b(warning|caution|careful|note|alert|attention|do not|avoid)\b",
    ],
    "contact": [
        r"\b(email|phone|contact|call|reach|address)\b",
    ],
}

_COMPILED = {
    cat: [re.compile(p, re.IGNORECASE) for p in pats]
    for cat, pats in IMPORTANT_MARKERS.items()
}


def _split_sentences(text: str) -> list:
    text = re.sub(r"\s+", " ", text)
    parts = re.split(r"(?<=[.!?])\s+", text)
    return [p.strip() for p in parts if len(p.strip().split()) >= 5]


def find_highlights(text: str, max_per_category: int = 5) -> list:
    """
    Return a list of
    {'sentence': str, 'category': str, 'reason': str}
    """
    if not text or not text.strip():
        return []

    sentences = _split_sentences(text)
    found = []

    for sentence in sentences:
        matched = None
        reason = None
        for category, patterns in _COMPILED.items():
            for pat in patterns:
                m = pat.search(sentence)
                if m:
                    matched = category
                    reason = f"matched '{m.group(0)}'"
                    break
            if matched:
                break

        if matched:
            found.append({
                "sentence": sentence,
                "category": matched,
                "reason": reason,
            })

    # Cap per category (keeps the best first — first occurrence usually matters)
    by_cat = {}
    for item in found:
        cat = item["category"]
        if cat in by_cat and len(by_cat[cat]) >= max_per_category:
            continue
        by_cat.setdefault(cat, []).append(item)

    # Flatten in original order
    order = {s: i for i, s in enumerate(sentences)}
    flat = [item for items in by_cat.values() for item in items]
    flat.sort(key=lambda x: order.get(x["sentence"], 999))
    return flat


def highlights_to_csv(highlights: list) -> str:
    import csv, io as _io
    out = _io.StringIO()
    writer = csv.writer(out)
    writer.writerow(["sentence", "category", "reason"])
    for h in highlights:
        writer.writerow([h["sentence"], h["category"], h["reason"]])
    return out.getvalue()