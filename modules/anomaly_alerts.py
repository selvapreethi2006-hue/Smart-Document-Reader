"""Detect suspicious patterns and flag potential issues."""

import re
from datetime import datetime


def detect_anomalies(text, info, stats):
    alerts = []
    if not text:
        return alerts

    phones = info.get("phones", [])
    if len(phones) >= 5:
        alerts.append({
            "level": "warning",
            "title": f"{len(phones)} phone numbers detected",
            "detail": "This document contains many phone numbers.",
        })

    if re.search(r"\b\d{4}\s?\d{4}\s?\d{4}\b", text):
        alerts.append({
            "level": "danger",
            "title": "Aadhaar-like number detected",
            "detail": "12-digit sequences found that look like Aadhaar numbers.",
        })
    if re.search(r"\b[A-Z]{5}\d{4}[A-Z]\b", text):
        alerts.append({
            "level": "danger",
            "title": "PAN-like number detected",
            "detail": "Regulated financial PII in India.",
        })

    amounts = re.findall(r"(?:₹|Rs\.?|INR)\s?([\d,]+(?:\.\d{1,2})?)", text)
    for amt_str in amounts[:5]:
        try:
            amt = float(amt_str.replace(",", ""))
            if amt >= 10_000_000:
                alerts.append({
                    "level": "warning",
                    "title": f"Very large amount: Rs {amt:,.0f}",
                    "detail": "Amounts of this size warrant verification.",
                })
                break
        except ValueError:
            continue

    if re.search(r"-\s?(?:₹|Rs\.?|INR|\$)\s?\d", text):
        alerts.append({
            "level": "info",
            "title": "Negative amount detected",
            "detail": "May be a refund, discount, or data-entry error.",
        })

    today = datetime.now()
    for m in re.finditer(
        r"(?:expiry|expires|valid\s+until|due\s+date)[:\s]+"
        r"(\d{1,4}[-/\.]\d{1,2}[-/\.]\d{1,4})",
        text, re.IGNORECASE,
    ):
        raw = m.group(1)
        for fmt in ("%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%d",
                    "%d-%m-%Y", "%d.%m.%Y", "%Y/%m/%d"):
            try:
                dt = datetime.strptime(raw, fmt)
                if dt < today:
                    alerts.append({
                        "level": "warning",
                        "title": f"Expired date detected: {raw}",
                        "detail": "Document mentions an expiry already in the past.",
                    })
                break
            except ValueError:
                continue

    emails = info.get("emails", [])
    if len(emails) >= 10:
        alerts.append({
            "level": "warning",
            "title": f"{len(emails)} email addresses found",
            "detail": "Bulk email extraction may have privacy implications.",
        })

    words = stats.get("words", 0) if stats else 0
    if 0 < words < 20:
        alerts.append({
            "level": "info",
            "title": "Very short document",
            "detail": f"Only {words} words extracted. OCR quality may be low.",
        })

    return alerts
