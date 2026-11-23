"""Per-sentence and overall sentiment using TextBlob."""

import re

try:
    from textblob import TextBlob
    _HAS_TEXTBLOB = True
except Exception:
    _HAS_TEXTBLOB = False


def _label(polarity: float) -> str:
    if polarity >= 0.3:
        return "Positive"
    if polarity <= -0.3:
        return "Negative"
    return "Neutral"


def analyse_sentiment(text: str) -> dict:
    """Return {'overall': {...}, 'sentences': [...]}."""
    if not text or not text.strip():
        return {"overall": {}, "sentences": []}

    if not _HAS_TEXTBLOB:
        return {"overall": {}, "sentences": [],
                "error": "TextBlob not installed"}

    sentences = re.split(r"(?<=[.!?])\s+", re.sub(r"\s+", " ", text))
    sentences = [s.strip() for s in sentences if len(s.strip().split()) >= 3]

    results = []
    for s in sentences[:100]:  # cap for speed
        try:
            blob = TextBlob(s)
            pol = blob.sentiment.polarity
            subj = blob.sentiment.subjectivity
            results.append({
                "sentence": s[:200],
                "polarity": round(pol, 3),
                "subjectivity": round(subj, 3),
                "label": _label(pol),
            })
        except Exception:
            continue

    if not results:
        return {"overall": {}, "sentences": []}

    avg_pol = sum(r["polarity"] for r in results) / len(results)
    avg_subj = sum(r["subjectivity"] for r in results) / len(results)
    counts = {"Positive": 0, "Neutral": 0, "Negative": 0}
    for r in results:
        counts[r["label"]] += 1

    return {
        "overall": {
            "polarity": round(avg_pol, 3),
            "subjectivity": round(avg_subj, 3),
            "label": _label(avg_pol),
            "counts": counts,
        },
        "sentences": results,
    }