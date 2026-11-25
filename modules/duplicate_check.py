"""Detect near-duplicate documents via hashing + Jaccard similarity."""

import hashlib
import re
from difflib import SequenceMatcher


def fingerprint(text):
    normalised = re.sub(r"\s+", " ", text.lower().strip())
    return hashlib.sha256(normalised.encode("utf-8")).hexdigest()


def _token_set(text):
    return {w.lower() for w in re.findall(r"[A-Za-z]{3,}", text)}


def similarity(text_a, text_b):
    if not text_a or not text_b:
        return {"jaccard": 0.0, "char": 0.0, "overall": 0.0}

    a, b = _token_set(text_a), _token_set(text_b)
    jaccard = len(a & b) / len(a | b) if (a | b) else 0.0

    norm_a = re.sub(r"\s+", " ", text_a.lower())
    norm_b = re.sub(r"\s+", " ", text_b.lower())
    char = SequenceMatcher(None, norm_a[:3000], norm_b[:3000]).ratio()

    overall = round((jaccard * 0.5 + char * 0.5), 3)
    return {
        "jaccard": round(jaccard, 3),
        "char": round(char, 3),
        "overall": overall,
    }


def is_duplicate(text_a, text_b, threshold=0.85):
    if fingerprint(text_a) == fingerprint(text_b):
        return True
    return similarity(text_a, text_b)["overall"] >= threshold
