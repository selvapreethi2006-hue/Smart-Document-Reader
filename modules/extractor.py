"""Text extraction: pdfplumber (PDFs) + RapidOCR (images/scanned PDFs)."""

import io
import os

import pdfplumber
from PIL import Image

_engine = None


def _get_engine():
    global _engine
    if _engine is None:
        from rapidocr_onnxruntime import RapidOCR
        _engine = RapidOCR()
    return _engine


def _ocr_image(img: Image.Image) -> str:
    try:
        import numpy as np
        engine = _get_engine()
        arr = np.array(img.convert("RGB"))
        result, _ = engine(arr)
        if not result:
            return ""
        return "\n".join(item[1] for item in result).strip()
    except Exception as exc:
        raise RuntimeError(f"OCR failed: {exc}") from exc


def extract_from_pdf(file_bytes: bytes) -> dict:
    """Extract text + tables from PDF."""
    pages, ocr_pages, tables = [], 0, []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for idx, page in enumerate(pdf.pages, start=1):
            text = (page.extract_text() or "").strip()
            if not text:
                pil_img = page.to_image(resolution=150).original
                text = _ocr_image(pil_img)
                if text:
                    ocr_pages += 1
            pages.append({"page": idx, "text": text})

            # Table extraction (works only on digital PDFs)
            try:
                for t in page.extract_tables():
                    if t and len(t) > 1:
                        tables.append({"page": idx, "rows": t})
            except Exception:
                pass

        page_count = len(pdf.pages)

    combined = "\n\n".join(p["text"] for p in pages if p["text"])
    return {
        "text": combined,
        "pages": pages,
        "page_count": page_count,
        "ocr_pages": ocr_pages,
        "tables": tables,
    }


def extract_from_image(file_bytes: bytes) -> dict:
    pil = Image.open(io.BytesIO(file_bytes)).convert("RGB")
    text = _ocr_image(pil)
    return {
        "text": text,
        "pages": [{"page": 1, "text": text}],
        "page_count": 1,
        "ocr_pages": 1 if text else 0,
        "tables": [],
    }


def extract_text(file_bytes: bytes, filename: str) -> dict:
    ext = os.path.splitext(filename)[1].lower()
    if ext == ".pdf":
        return extract_from_pdf(file_bytes)
    if ext in (".jpg", ".jpeg", ".png"):
        return extract_from_image(file_bytes)
    raise ValueError(f"Unsupported file type: {ext}")


def extract_batch(files: list) -> list:
    """
    files: list of (filename, bytes) tuples.
    Returns list of {'filename': ..., 'result': extract_text(...)} dicts.
    Errors on individual files are captured, not raised.
    """
    out = []
    for name, data in files:
        try:
            result = extract_text(data, name)
            out.append({"filename": name, "result": result, "error": None})
        except Exception as exc:
            out.append({"filename": name, "result": None, "error": str(exc)})
    return out