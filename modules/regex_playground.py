"""Safe custom-regex runner for power users."""

import re


def run_regex(text: str, pattern: str, flags: str = "") -> dict:
    """
    Returns:
    {
        'matches': [{'match': str, 'start': int, 'end': int,
                     'groups': [str, ...], 'context': str}],
        'error': str | None,
        'count': int,
    }
    """
    result = {"matches": [], "error": None, "count": 0}
    if not text or not pattern:
        return result

    flag_value = 0
    if "i" in flags.lower():
        flag_value |= re.IGNORECASE
    if "m" in flags.lower():
        flag_value |= re.MULTILINE
    if "s" in flags.lower():
        flag_value |= re.DOTALL

    try:
        compiled = re.compile(pattern, flag_value)
    except re.error as exc:
        result["error"] = f"Invalid regex: {exc}"
        return result

    for m in compiled.finditer(text):
        if m.end() == m.start():
            continue  # skip zero-length matches to avoid infinite loops
        start = max(0, m.start() - 40)
        end = min(len(text), m.end() + 40)
        context = text[start:end].replace("\n", " ")
        result["matches"].append({
            "match": m.group(0),
            "start": m.start(),
            "end": m.end(),
            "groups": list(m.groups()),
            "context": f"…{context}…",
        })
        if len(result["matches"]) >= 500:
            break

    result["count"] = len(result["matches"])
    return result


COMMON_PATTERNS = {
    "Email": r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
    "Phone (India)": r"(?:\+91[\s-]?)?[6-9]\d{9}",
    "URL": r"https?://[\w\-]+(?:\.[\w\-]+)+(?:/[\w\-./?%&=+#]*)?",
    "Date (YYYY-MM-DD)": r"\d{4}-\d{2}-\d{2}",
    "Amount (INR)": r"₹\s?\d{1,3}(?:,\d{2,3})*(?:\.\d{1,2})?",
    "PIN Code": r"\b\d{6}\b",
    "IFSC Code": r"\b[A-Z]{4}0[A-Z0-9]{6}\b",
    "All CAPS words": r"\b[A-Z]{3,}\b",
    "Quoted text": r"\"[^\"]{3,}\"",
    "Numbers > 1000": r"\b\d{4,}\b",
}