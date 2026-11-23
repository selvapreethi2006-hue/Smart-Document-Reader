"""Produce a redacted version of the text — hides PII for safe sharing."""

from modules.info_extractor import extract_info


def _mask(value: str, keep: int = 2) -> str:
    """Show first `keep` chars, mask the rest."""
    if len(value) <= keep:
        return "*" * len(value)
    return value[:keep] + "*" * (len(value) - keep)


def redact_text(text: str) -> dict:
    """
    Returns {'redacted': str, 'summary': {emails: n, phones: n, ...}}.
    Uses the same regexes as info_extractor so redaction is complete.
    """
    if not text or not text.strip():
        return {"redacted": "", "summary": {}}

    info = extract_info(text)
    redacted = text
    summary = {}

    for email in info.get("emails", []):
        redacted = redacted.replace(email, _mask(email, 3))
        summary["emails"] = summary.get("emails", 0) + 1

    for phone in info.get("phones", []):
        digits_only = "".join(c for c in phone if c.isdigit())
        if len(digits_only) >= 7:
            redacted = redacted.replace(phone, "*" * len(digits_only))
            summary["phones"] = summary.get("phones", 0) + 1

    for name in info.get("names", []):
        # Only redact 2+ word names (avoids nuking every common noun)
        if len(name.split()) >= 2:
            redacted = redacted.replace(name, _mask(name, 1))
            summary["names"] = summary.get("names", 0) + 1

    for addr in info.get("addresses", []):
        redacted = redacted.replace(addr, "[REDACTED ADDRESS]")
        summary["addresses"] = summary.get("addresses", 0) + 1

    return {"redacted": redacted, "summary": summary}