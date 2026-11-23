"""Document statistics: word count, reading time, readability."""

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


def _count_syllables(word: str) -> int:
    word = word.lower()
    vowels = "aeiouy"
    count = 0
    prev_was_vowel = False
    for ch in word:
        is_vowel = ch in vowels
        if is_vowel and not prev_was_vowel:
            count += 1
        prev_was_vowel = is_vowel
    if word.endswith("e") and count > 1:
        count -= 1
    return max(1, count)


def _readability_grade(text: str) -> dict:
    """Flesch Reading Ease + Flesch-Kincaid Grade."""
    sentences = [s for s in re.split(r"[.!?]+", text) if s.strip()]
    words = re.findall(r"[A-Za-z]+", text)
    if not sentences or not words:
        return {}

    total_words = len(words)
    total_sentences = len(sentences)
    total_syllables = sum(_count_syllables(w) for w in words)

    # Flesch Reading Ease
    fre = 206.835 - 1.015 * (total_words / total_sentences) - 84.6 * (total_syllables / total_words)
    fre = max(0.0, min(100.0, fre))

    # Flesch-Kincaid Grade Level
    fkgl = 0.39 * (total_words / total_sentences) + 11.8 * (total_syllables / total_words) - 15.59
    fkgl = max(1.0, min(18.0, fkgl))

    if fre >= 80:
        ease = "Very Easy"
    elif fre >= 70:
        ease = "Easy"
    elif fre >= 60:
        ease = "Standard"
    elif fre >= 50:
        ease = "Fairly Difficult"
    elif fre >= 30:
        ease = "Difficult"
    else:
        ease = "Very Difficult"

    return {
        "flesch_ease": round(fre, 1),
        "flesch_label": ease,
        "fk_grade": round(fkgl, 1),
    }


def document_stats(text: str) -> dict:
    """Return word/sentence/paragraph counts, reading time, top words."""
    if not text or not text.strip():
        return {
            "characters": 0, "words": 0, "sentences": 0, "paragraphs": 0,
            "reading_time_min": 0, "unique_words": 0, "top_words": [],
            "readability": {},
        }

    words = re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?", text)
    sentences = [s for s in re.split(r"[.!?]+", text) if s.strip()]
    paragraphs = [p for p in re.split(r"\n\s*\n", text) if p.strip()]

    total_words = len(words)
    # Reading speed ~ 200 words/minute
    reading_min = max(1, round(total_words / 200)) if total_words > 0 else 0

    meaningful = [w.lower() for w in words if w.lower() not in _STOPWORDS and len(w) > 2]
    top_words = Counter(meaningful).most_common(10)

    return {
        "characters": len(text),
        "words": total_words,
        "sentences": len(sentences),
        "paragraphs": len(paragraphs),
        "reading_time_min": reading_min,
        "unique_words": len(set(w.lower() for w in words)),
        "top_words": [{"word": w, "count": c} for w, c in top_words],
        "readability": _readability_grade(text),
    }