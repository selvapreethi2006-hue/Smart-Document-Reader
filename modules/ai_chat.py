"""
Conversational Q&A engine with:
- Follow-up question support (uses prior questions as context)
- Context-aware scoring (weights recent conversation)
- Source evidence (page number + sentence + snippet)
- Fully offline, no LLM / API key required.
"""

import re
from collections import Counter

_STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "if", "then", "so", "of", "to",
    "in", "on", "for", "with", "as", "at", "by", "from", "is", "are", "was",
    "were", "be", "been", "being", "it", "its", "this", "that", "these",
    "those", "we", "you", "they", "he", "she", "i", "me", "my", "our",
    "your", "their", "his", "her", "them", "us", "what", "who", "when",
    "where", "why", "how", "which", "does", "do", "did", "can", "could",
    "will", "would", "should", "is", "there", "any", "about", "tell",
    "explain", "describe", "give", "show", "please", "also", "more",
    "further", "again", "then", "now",
}

# Pronouns / follow-up markers that reference the previous question
FOLLOWUP_MARKERS = {
    "it", "its", "this", "that", "these", "those", "they", "them",
    "their", "he", "she", "him", "her", "more", "else", "another",
    "further", "same", "also", "too",
}


def _tokenize(text: str) -> list:
    return [w.lower() for w in re.findall(r"[A-Za-z0-9]+", text)]


def _split_sentences(text: str) -> list:
    text = re.sub(r"\s+", " ", text)
    parts = re.split(r"(?<=[.!?])\s+", text)
    return [p.strip() for p in parts if len(p.strip().split()) >= 4]


def _is_followup(question: str) -> bool:
    tokens = set(_tokenize(question))
    # Short question + contains a referential pronoun → likely a follow-up
    return len(tokens) <= 6 and bool(tokens & FOLLOWUP_MARKERS)


def _build_context_question(current_question: str, history: list) -> str:
    """
    If the current question is a follow-up, prepend keywords from
    the last 1–2 questions so the ranking has context to work with.
    """
    if not history or not _is_followup(current_question):
        return current_question

    recent = history[-2:] if len(history) >= 2 else history[-1:]
    context_terms = []
    for entry in recent:
        q_tokens = [
            t for t in _tokenize(entry["question"])
            if t not in _STOPWORDS and len(t) > 1
        ]
        context_terms.extend(q_tokens[:5])

    combined = " ".join(context_terms) + " " + current_question
    return combined.strip()


def _score_sentence(sentence: str, query_tokens: list,
                    context_counter: Counter = None) -> float:
    """Score a sentence against query tokens, with optional context boost."""
    s_tokens = [t for t in _tokenize(sentence) if t not in _STOPWORDS]
    if not s_tokens:
        return 0.0
    s_counter = Counter(s_tokens)
    base = sum(1 for qt in query_tokens if qt in s_counter)
    if base == 0:
        return 0.0
    # Normalise by question length (fewer tokens = each hit weighs more)
    score = base / (len(query_tokens) ** 0.5)

    # Context boost: if sentence contains words from previous questions
    if context_counter:
        context_hits = sum(1 for t in s_tokens if t in context_counter)
        score += 0.15 * context_hits

    return score


def answer_with_context(text: str, question: str, history: list,
                        pages: list = None, top_k: int = 3) -> dict:
    """
    Return:
    {
        'question': str,
        'is_followup': bool,
        'context_question': str,   # the expanded query used for scoring
        'answers': [
            {'score': float, 'sentence': str,
             'page': int | None, 'snippet': str}
        ]
    }
    """
    result = {
        "question": question,
        "is_followup": False,
        "context_question": question,
        "answers": [],
    }
    if not text or not question:
        return result

    is_fu = _is_followup(question)
    result["is_followup"] = is_fu

    ctx_question = _build_context_question(question, history)
    result["context_question"] = ctx_question

    q_tokens = [t for t in _tokenize(ctx_question) if t not in _STOPWORDS and len(t) > 1]
    if not q_tokens:
        return result

    # Build context counter from recent questions to boost related sentences
    context_counter = None
    if is_fu and history:
        ctx_words = []
        for entry in history[-2:]:
            ctx_words.extend([
                t for t in _tokenize(entry["question"])
                if t not in _STOPWORDS
            ])
        if ctx_words:
            context_counter = Counter(ctx_words)

    # Determine page boundaries for evidence mapping
    page_bounds = []  # [(page_num, start_idx, end_idx)]
    if pages:
        cursor = 0
        for p in pages:
            ptext = p.get("text", "")
            if not ptext:
                continue
            start = text.find(ptext[:50], cursor)
            if start == -1:
                start = cursor
            end = start + len(ptext)
            page_bounds.append((p["page"], start, end))
            cursor = end

    def _find_page(sentence_start: int) -> int:
        for page_num, s, e in page_bounds:
            if s <= sentence_start < e:
                return page_num
        return None

    sentences = _split_sentences(text)
    if not sentences:
        return result

    scored = []
    cursor = 0
    for sentence in sentences:
        # Find sentence's actual position in text for evidence lookup
        pos = text.find(sentence, cursor)
        if pos == -1:
            pos = text.find(sentence)
        sentence_start = pos if pos >= 0 else cursor
        cursor = sentence_start + len(sentence) if pos >= 0 else cursor

        score = _score_sentence(sentence, q_tokens, context_counter)
        if score <= 0:
            continue

        # Build a short snippet around the matched sentence
        snippet_start = max(0, sentence_start - 60)
        snippet_end = min(len(text), sentence_start + len(sentence) + 60)
        snippet = text[snippet_start:snippet_end].replace("\n", " ").strip()

        scored.append({
            "score": round(score, 3),
            "sentence": sentence,
            "page": _find_page(sentence_start),
            "snippet": f"…{snippet}…",
        })

    scored.sort(key=lambda x: x["score"], reverse=True)
    result["answers"] = scored[:top_k]
    return result