"""Extractive summarizer — no LLM, no dummy text."""

import re
from collections import Counter

_STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "if", "then", "so", "of", "to",
    "in", "on", "for", "with", "as", "at", "by", "from", "is", "are", "was",
    "were", "be", "been", "being", "it", "its", "this", "that", "these",
    "those", "we", "you", "they", "he", "she", "i", "me", "my", "our",
    "your", "their", "his", "her", "them", "us", "will", "would", "can",
    "could", "should", "may", "might", "have", "has", "had", "do", "does",
    "did", "not", "no", "yes", "also", "than", "into", "over", "under",
}


def _split_sentences(text: str):
    text = re.sub(r"\s+", " ", text)
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", text)
    return [p.strip() for p in parts if len(p.strip().split()) >= 5]


def _word_freq(text: str):
    words = re.findall(r"[A-Za-z]{3,}", text.lower())
    return Counter(w for w in words if w not in _STOPWORDS)


def summarize(text: str, max_sentences: int = 5) -> dict:
    """
    Returns {'summary': str, 'key_points': list[str]}.
    Uses frequency-scored extractive summarization.
    """
    if not text or not text.strip():
        return {"summary": "", "key_points": []}

    sentences = _split_sentences(text)
    if not sentences:
        # Short/oddly formatted docs: just cap by characters
        return {"summary": text.strip()[:500], "key_points": []}

    if len(sentences) <= max_sentences:
        return {
            "summary": " ".join(sentences),
            "key_points": sentences[:max_sentences],
        }

    freq = _word_freq(text)
    if not freq:
        return {"summary": " ".join(sentences[:max_sentences]),
                "key_points": sentences[:max_sentences]}

    max_freq = max(freq.values())
    scored = []
    for idx, sentence in enumerate(sentences):
        words = re.findall(r"[A-Za-z]{3,}", sentence.lower())
        if not words:
            continue
        score = sum(freq.get(w, 0) for w in words) / (max_freq * len(words))
        # Slight bias to earlier sentences (often contain key info)
        score *= (1 + 1.0 / (idx + 1))
        scored.append((score, idx, sentence))

    top = sorted(scored, key=lambda x: x[0], reverse=True)[:max_sentences]
    top.sort(key=lambda x: x[1])  # restore document order

    key_points = [s for _, _, s in top]
    return {"summary": " ".join(key_points), "key_points": key_points}