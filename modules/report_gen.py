"""Generate a styled PDF report from the current document."""

import io
from datetime import datetime
from fpdf import FPDF


class _ReportPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(40, 40, 40)
        self.cell(0, 10, "Smart Document Reader — Report", ln=True, align="C")
        self.set_font("Helvetica", "", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 5, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                  ln=True, align="C")
        self.ln(3)
        self.set_draw_color(200, 200, 200)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")

    def section_title(self, title):
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(30, 80, 160)
        self.cell(0, 8, title, ln=True)
        self.set_text_color(0, 0, 0)
        self.ln(1)

    def body_text(self, text, size=10):
        self.set_font("Helvetica", "", size)
        self.multi_cell(0, 5, text or "—")
        self.ln(2)


def _safe(text, limit=2000):
    """fpdf2 can only encode latin-1 by default; replace unsupported chars."""
    if not text:
        return ""
    text = text[:limit]
    return text.encode("latin-1", "replace").decode("latin-1")


def generate_report(meta: dict, summary: dict, info: dict,
                    stats: dict, language: dict,
                    tables: list, filename: str) -> bytes:
    pdf = _ReportPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # --- File info ---
    pdf.section_title("Document Information")
    pdf.body_text(
        f"File: {_safe(meta.get('filename', 'unknown'))}\n"
        f"Pages: {meta.get('page_count', 0)}\n"
        f"OCR pages: {meta.get('ocr_pages', 0)}\n"
        f"Language: {language.get('name', 'Unknown')} "
        f"(confidence {language.get('confidence', 0)})\n"
        f"Words: {stats.get('words', 0)}  |  "
        f"Sentences: {stats.get('sentences', 0)}  |  "
        f"Reading time: {stats.get('reading_time_min', 0)} min"
    )

    # --- Summary ---
    if summary.get("summary"):
        pdf.section_title("Summary")
        pdf.body_text(_safe(summary["summary"]))
        if summary.get("key_points"):
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(0, 6, "Key points:", ln=True)
            pdf.set_font("Helvetica", "", 9)
            for point in summary["key_points"]:
                pdf.multi_cell(0, 5, f"•  {_safe(point)}")
            pdf.ln(2)

    # --- Structured info ---
    pdf.section_title("Extracted Information")
    labels = {
        "names": "Names", "emails": "Emails", "phones": "Phones",
        "dates": "Dates", "addresses": "Addresses",
    }
    any_info = False
    for key, label in labels.items():
        values = info.get(key, [])
        if not values:
            continue
        any_info = True
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 5, label, ln=True)
        pdf.set_font("Helvetica", "", 9)
        for v in values[:20]:
            pdf.multi_cell(0, 5, f"  •  {_safe(v, 200)}")
    if not any_info:
        pdf.body_text("No structured information detected.")

    # --- Tables ---
    if tables:
        pdf.section_title(f"Tables ({len(tables)} detected)")
        for i, t in enumerate(tables, start=1):
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(0, 6, f"Table {i} (page {t['page']}):", ln=True)
            rows = t.get("rows") or []
            if not rows:
                pdf.body_text("Empty table.")
                continue
            # Render each table as plain text (fpdf2 tables are complex to style)
            pdf.set_font("Helvetica", "", 8)
            for row in rows[:15]:
                cells = [(_safe(c, 30) if c else "") for c in row]
                pdf.multi_cell(0, 4, " | ".join(cells))
            pdf.ln(3)

    return bytes(pdf.output())