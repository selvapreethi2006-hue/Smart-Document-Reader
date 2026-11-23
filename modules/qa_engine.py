"""Simple extractive Q&A: find the most relevant sentence for a question.
No LLM, no API key — pure Python. Works fully offline."""

import re
from collections import Counter

_STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "if", "then", "so", "of", "to",
    "in", "on", "for", "with", "as", "at", "by", "from", "is", "are", "was",
    "were", "be", "been", "being", "it", "its", "this", "that", "these",
    "those", "we", "you", "they", "he", "she", "i", "me", "my", "our",
    "your", "their", "his", "her", "them", "us", "what", "who", "when",
    "where", "why", "how", "which", "does", "do", "did", "can", "could",
    "will", "would", "should", "is", "there", "any", "about",
}


def _tokenize(text: str) -> list:
    return [w.lower() for w in re.findall(r"[A-Za-z0-9]+", text)]


def _split_sentences(text: str) -> list:
    text = re.sub(r"\s+", " ", text)
    parts = re.split(r"(?<=[.!?])\s+", text)
    return [p.strip() for p in parts if len(p.strip().split()) >= 4]


def answer_question(text: str, question: str, top_k: int = 3) -> list:
    """
    Return up to top_k (sentence, score) pairs ranked by keyword overlap
    with the question. Best answer first. Empty list if nothing relevant.
    """
    if not text or not question:
        return []

    q_tokens = [t for t in _tokenize(question) if t not in _STOPWORDS and len(t) > 1]
    if not q_tokens:
        return []

    sentences = _split_sentences(text)
    if not sentences:
        return []

    scored = []
    for sentence in sentences:
        s_tokens = [t for t in _tokenize(sentence) if t not in _STOPWORDS]
        if not s_tokens:
            continue
        s_counter = Counter(s_tokens)
        # Simple: count how many question keywords appear in the sentence
        score = sum(1 for qt in q_tokens if qt in s_counter)
        if score == 0:
            continue
        # Weight by how unique the matched words are
        score = score / (len(q_tokens) ** 0.5)
        scored.append((score, sentence))

    scored.sort(reverse=True)
    return scored[:top_k]