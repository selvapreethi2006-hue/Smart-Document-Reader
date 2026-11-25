"""Detect headings and build a table of contents."""

import re

# Heading heuristics:
# - Numbered: "1.", "1.2", "Chapter 3", "Section 4.5"
# - ALL CAPS short lines
# - Title Case short lines without trailing punctuation
# - Markdown-style "#", "##" (if present)

NUMBERED_HEADING = re.compile(
    r"^\s*(?:\d+(?:\.\d+)*\.?|Chapter\s+\d+|Section\s+\d+(?:\.\d+)*|Part\s+[IVX]+)"
    r"[\s\.\):]+(.+)$",
    re.MULTILINE,
)
MARKDOWN_HEADING = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
ALL_CAPS_LINE = re.compile(r"^[A-Z][A-Z\s\d\-:&/]{2,60}$")


def _looks_like_heading(line: str) -> bool:
    s = line.strip()
    if not s or len(s) < 3 or len(s) > 100:
        return False
    # Ends with sentence punctuation → not a heading
    if s.endswith((".", ",", ";", "?", "!")) and not s.endswith(":"):
        return False
    # Too many words → probably a sentence
    if len(s.split()) > 15:
        return False
    return True


def detect_toc(text: str) -> list:
    """
    Return list of {'title': str, 'level': int, 'line_no': int}.
    Level: 1 for chapter/part, 2 for section, 3 for sub-section.
    """
    if not text or not text.strip():
        return []

    lines = text.split("\n")
    toc = []
    in_toc_section = False

    for idx, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue

        # Detect start of an explicit TOC section
        if re.match(r"^(table of contents|contents|toc)\s*$",
                    stripped, re.IGNORECASE):
            in_toc_section = True
            continue

        # Markdown-style heading
        md = MARKDOWN_HEADING.match(stripped)
        if md:
            level = len(md.group(1))
            toc.append({
                "title": md.group(2).strip(),
                "level": min(level, 3),
                "line_no": idx + 1,
            })
            continue

        # Numbered heading
        nm = NUMBERED_HEADING.match(stripped)
        if nm:
            # Level = dot count in the number
            num_part = stripped.split()[0]
            level = min(num_part.count(".") + 1, 3)
            toc.append({
                "title": stripped[:100],
                "level": level,
                "line_no": idx + 1,
            })
            continue

        # ALL CAPS short line
        if ALL_CAPS_LINE.match(stripped) and _looks_like_heading(stripped):
            toc.append({
                "title": stripped.title(),
                "level": 2,
                "line_no": idx + 1,
            })
            continue

        # Title Case line: 2–8 words, no ending punctuation
        words = stripped.split()
        if (2 <= len(words) <= 8
                and _looks_like_heading(stripped)
                and all(w[0].isupper() for w in words
                        if w and w[0].isalpha())):
            # Only treat as heading if NOT inside a TOC listing
            if not in_toc_section:
                toc.append({
                    "title": stripped,
                    "level": 3,
                    "line_no": idx + 1,
                })

    # De-dupe by title
    seen = set()
    out = []
    for item in toc:
        key = item["title"].lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out