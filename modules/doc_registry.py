"""Session-wide registry of every document processed.
Tracks fingerprint, name, key stats, and duplicate relationships."""

import hashlib
import re
from datetime import datetime


def _fingerprint(text: str) -> str:
    normalised = re.sub(r"\s+", " ", text.lower().strip())
    return hashlib.sha256(normalised.encode("utf-8")).hexdigest()[:16]


def add_to_registry(registry: list, name: str, text: str,
                    word_count: int, language: str) -> list:
    """Add or update an entry. Returns the updated registry."""
    fp = _fingerprint(text)
    for entry in registry:
        if entry["fingerprint"] == fp:
            entry["uploads"] += 1
            entry["last_seen"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return registry

    registry.append({
        "fingerprint": fp,
        "name": name,
        "word_count": word_count,
        "language": language,
        "first_seen": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "last_seen": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "uploads": 1,
    })
    return registry


def find_duplicates(registry: list, text: str) -> list:
    """Return registry entries whose fingerprint matches."""
    fp = _fingerprint(text)
    return [e for e in registry if e["fingerprint"] == fp]


def clear_registry() -> list:
    return []