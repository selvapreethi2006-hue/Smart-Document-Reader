"""TF-IDF keyword and phrase extraction. No external model needed."""

import re
from collections import Counter
from math import log

_STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "if", "then", "so", "of", "to",
    "in", "on", "for", "with", "as", "at", "by", "from", "is", "are", "was",
    "were", "be", "been", "being", "it", "its", "this", "that", "these",
    "those", "we", "you", "they", "he", "she", "i", "me", "my", "our",
    "your", "their", "his", "her", "them", "us", "will", "would", "can",
    "could", "should", "may", "might", "have", "has", "had", "do", "does",
    "did", "not", "no", "yes", "also", "than", "into", "over", "under",
}


def _split_sentences(text):
    text = re.sub(r"\s+", " ", text)
    parts = re.split(r"(?<=[.!?])\s+", text)
    return [p.strip() for p in parts if p.strip()]


def extract_keywords(text: str, top_n: int = 15) -> list:
    """Return list of {term, score} sorted by TF-IDF across sentences."""
    if not text or not text.strip():
        return []

    sentences = _split_sentences(text)
    if not sentences:
        return []

    # Tokenise per sentence
    tokens_per_sentence = []
    doc_freq = Counter()
    for s in sentences:
        toks = [
            w.lower() for w in re.findall(r"[A-Za-z]{3,}", s)
            if w.lower() not in _STOPWORDS
        ]
        tokens_per_sentence.append(toks)
        for t in set(toks):
            doc_freq[t] += 1

    n_docs = len(sentences)
    tf = Counter()
    for toks in tokens_per_sentence:
        tf.update(toks)

    scores = {}
    for term, freq in tf.items():
        idf = log((1 + n_docs) / (1 + doc_freq[term])) + 1
        scores[term] = freq * idf

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_n]
    max_score = ranked[0][1] if ranked else 1
    return [
        {"term": term, "score": round(score / max_score, 3)}
        for term, score in ranked
    ]


def extract_phrases(text: str, top_n: int = 10) -> list:
    """Return top 2–3 word phrases by frequency (simple bigram/trigram)."""
    if not text or not text.strip():
        return []
    words = [
        w.lower() for w in re.findall(r"[A-Za-z]{3,}", text)
        if w.lower() not in _STOPWORDS
    ]
    bigrams = Counter(
        f"{words[i]} {words[i+1]}" for i in range(len(words) - 1)
    )
    trigrams = Counter(
        f"{words[i]} {words[i+1]} {words[i+2]}" for i in range(len(words) - 2)
    )
    combined = bigrams + trigrams
    return [
        {"phrase": p, "count": c}
        for p, c in combined.most_common(top_n) if c > 1
    ]