"""Compare two documents: similarity score + structural diff."""

import re
from collections import Counter
from difflib import SequenceMatcher


def _normalise(text: str) -> str:
    text = re.sub(r"\s+", " ", text).lower().strip()
    return text


def _token_set(text: str) -> set:
    return {w for w in re.findall(r"[A-Za-z]{3,}", text.lower())}


def _cosine_similarity(a: Counter, b: Counter) -> float:
    common = set(a) & set(b)
    num = sum(a[t] * b[t] for t in common)
    denom = (sum(v * v for v in a.values()) ** 0.5) * \
            (sum(v * v for v in b.values()) ** 0.5)
    return num / denom if denom else 0.0


def compare_documents(text_a: str, text_b: str) -> dict:
    if not text_a or not text_b:
        return {}

    norm_a, norm_b = _normalise(text_a), _normalise(text_b)

    # Character-level similarity (good for near-duplicates)
    char_sim = SequenceMatcher(None, norm_a[:5000], norm_b[:5000]).ratio()

    # Token-set similarity (Jaccard)
    set_a, set_b = _token_set(norm_a), _token_set(norm_b)
    jaccard = len(set_a & set_b) / len(set_a | set_b) if (set_a | set_b) else 0.0

    # TF cosine similarity
    tf_a = Counter(re.findall(r"[A-Za-z]{3,}", norm_a))
    tf_b = Counter(re.findall(r"[A-Za-z]{3,}", norm_b))
    cosine = _cosine_similarity(tf_a, tf_b)

    # Word-level differences
    only_a = sorted(set_a - set_b)[:30]
    only_b = sorted(set_b - set_a)[:30]
    shared = sorted(set_a & set_b)[:30]

    return {
        "char_similarity": round(char_sim, 3),
        "jaccard_similarity": round(jaccard, 3),
        "cosine_similarity": round(cosine, 3),
        "overall_similarity": round(
            (char_sim * 0.3 + jaccard * 0.35 + cosine * 0.35), 3
        ),
        "only_in_first": only_a,
        "only_in_second": only_b,
        "shared_words": shared,
        "word_count_a": len(re.findall(r"[A-Za-z]{3,}", text_a)),
        "word_count_b": len(re.findall(r"[A-Za-z]{3,}", text_b)),
    }