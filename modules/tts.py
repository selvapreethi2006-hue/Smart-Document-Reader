"""Text-to-speech with two backends:
- gTTS (online, better voices, works everywhere)
- pyttsx3 (offline, Windows native SAPI)

Falls back gracefully if neither works.
"""

import io
import re

def _clean_for_tts(text: str, max_chars: int = 4000) -> str:
    """Remove markdown-ish junk and cap length for the API."""
    text = re.sub(r"[#*_>`|]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_chars]


def tts_gtts(text: str, lang: str = "en") -> bytes | None:
    """Returns MP3 bytes or None on failure."""
    try:
        from gtts import gTTS
        clean = _clean_for_tts(text)
        if not clean:
            return None
        buf = io.BytesIO()
        tts = gTTS(text=clean, lang=lang, slow=False)
        tts.write_to_fp(buf)
        return buf.getvalue()
    except Exception:
        return None


def tts_pyttsx3(text: str) -> bytes | None:
    """Offline TTS via pyttsx3 (Windows only). Returns WAV bytes or None."""
    try:
        import pyttsx3
        import tempfile, os
        clean = _clean_for_tts(text, 2000)
        if not clean:
            return None
        engine = pyttsx3.init()
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        tmp.close()
        engine.save_to_file(clean, tmp.name)
        engine.runAndWait()
        with open(tmp.name, "rb") as f:
            data = f.read()
        os.unlink(tmp.name)
        return data
    except Exception:
        return None


def synthesize(text: str, lang: str = "en", prefer: str = "gtts") -> dict:
    """
    Returns {'audio': bytes|None, 'format': 'mp3'|'wav'|None, 'engine': str}
    """
    if prefer == "pyttsx3":
        audio = tts_pyttsx3(text)
        if audio:
            return {"audio": audio, "format": "wav", "engine": "pyttsx3 (offline)"}
    # Try gTTS first (or as fallback)
    audio = tts_gtts(text, lang)
    if audio:
        return {"audio": audio, "format": "mp3", "engine": "gTTS"}
    # Last-ditch: offline
    audio = tts_pyttsx3(text)
    if audio:
        return {"audio": audio, "format": "wav", "engine": "pyttsx3 (offline)"}
    return {"audio": None, "format": None, "engine": "none"}