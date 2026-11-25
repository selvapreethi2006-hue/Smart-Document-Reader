"""Persistent Q&A session log — save and export every question asked."""

import json
from datetime import datetime


def add_to_history(history, question, answers):
    entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "question": question,
        "answers": [
            {"score": round(s, 3), "sentence": sent} for s, sent in answers
        ],
    }
    history.append(entry)
    return history


def history_to_json(history):
    return json.dumps(history, indent=2, ensure_ascii=False).encode("utf-8")


def history_to_markdown(history):
    lines = ["# Q&A History", ""]
    for i, entry in enumerate(history, start=1):
        lines.append(f"## {i}. {entry['question']}")
        lines.append(f"*Asked at: {entry['timestamp']}*")
        lines.append("")
        for a in entry["answers"]:
            lines.append(f"- **({a['score']:.2f})** {a['sentence']}")
        lines.append("")
    return "\n".join(lines)
