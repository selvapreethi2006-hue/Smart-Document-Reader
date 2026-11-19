"""Export helpers for TXT, CSV, JSON."""

import io
import json
import pandas as pd

_FIELD_ORDER = ["names", "emails", "phones", "dates", "addresses"]
_FIELD_LABELS = {
    "names": "Name",
    "emails": "Email",
    "phones": "Phone",
    "dates": "Date",
    "addresses": "Address",
}


def text_to_txt_bytes(text: str) -> bytes:
    return (text or "").encode("utf-8")


def info_to_json_bytes(info: dict) -> bytes:
    cleaned = {k: info.get(k, []) for k in _FIELD_ORDER}
    return json.dumps(cleaned, indent=2, ensure_ascii=False).encode("utf-8")


def info_to_csv_bytes(info: dict) -> bytes:
    """One row per extracted value, with its type."""
    rows = []
    for field in _FIELD_ORDER:
        for value in info.get(field, []):
            rows.append({"Field": _FIELD_LABELS[field], "Value": value})
    if not rows:
        # Emit header-only CSV so the download is still valid
        df = pd.DataFrame(columns=["Field", "Value"])
    else:
        df = pd.DataFrame(rows)
    return df.to_csv(index=False).encode("utf-8")