"""Detect the language of extracted text."""

from langdetect import detect, detect_langs, LangDetectException

_LANG_NAMES = {
    "en": "English", "ta": "Tamil", "hi": "Hindi", "te": "Telugu",
    "ml": "Malayalam", "kn": "Kannada", "bn": "Bengali", "mr": "Marathi",
    "gu": "Gujarati", "pa": "Punjabi", "ur": "Urdu",
    "fr": "French", "de": "German", "es": "Spanish", "it": "Italian",
    "pt": "Portuguese", "ru": "Russian", "zh-cn": "Chinese (Simplified)",
    "zh-tw": "Chinese (Traditional)", "ja": "Japanese", "ko": "Korean",
    "ar": "Arabic", "nl": "Dutch", "tr": "Turkish", "sv": "Swedish",
    "pl": "Polish", "vi": "Vietnamese", "th": "Thai", "id": "Indonesian",
}


def detect_language(text: str) -> dict:
    """
    Returns {'code': 'en', 'name': 'English', 'confidence': 0.98}.
    Returns empty dict if text is too short / undetectable.
    """
    if not text or len(text.strip()) < 20:
        return {}

    try:
        # langdetect needs enough text for accuracy
        sample = text[:5000]
        probs = detect_langs(sample)
        if not probs:
            return {}
        top = probs[0]
        code = top.lang
        return {
            "code": code,
            "name": _LANG_NAMES.get(code, code.upper()),
            "confidence": round(top.prob, 2),
        }
    except LangDetectException:
        return {}
    except Exception:
        return {}


def detect_language_simple(text: str) -> str:
    """Just the language code, or '' if undetectable."""
    info = detect_language(text)
    return info.get("code", "")