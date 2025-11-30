"""Offline / Low-Bandwidth Mode Utilities

Provides fallback implementations for Speech-To-Text (STT), Text-To-Speech (TTS),
and Machine Translation (MT) that work without relying on cloud services.

Design goals:
 - Graceful degradation: if a library/model is missing, return None with instructions
 - Non-blocking init: attempt lazy loading only when offline mode enabled
 - Minimal footprint: prefer lightweight or already cached resources

Dependencies (optional, install as needed):
  pip install vosk pyttsx3 argostranslate==1.9.0

Argos Translate language packs must be installed separately, for example:
  python -m argostranslate.package install <package_file.argosmodel>
See https://github.com/argosopentech/argos-translate for language packs.
"""

from __future__ import annotations

import os
import json
from typing import Optional, Tuple

import streamlit as st

# Feature availability flags
_vosk_available = False
_pyttsx3_available = False
_argos_available = False

_vosk_model = None
_vosk_samplerate = 16000
_pyttsx3_engine = None

def initialize_offline_resources():
    """Attempt to initialize offline components.

    Sets session_state flags for availability and returns a summary dict.
    Safe to call multiple times (idempotent)."""
    global _vosk_available, _pyttsx3_available, _argos_available, _vosk_model, _pyttsx3_engine

    summary = {"vosk": False, "pyttsx3": False, "argos": False}
    
    # Return cached results if already initialized
    if _vosk_available and _pyttsx3_available and _argos_available:
        summary = {"vosk": True, "pyttsx3": True, "argos": True}
        st.session_state["offline_capabilities"] = summary
        return summary

    # Vosk STT
    if not _vosk_available:
        try:
            from vosk import Model  # type: ignore
            # Try VOSK_MODEL_PATH env var first, then check common locations
            model_path = os.getenv("VOSK_MODEL_PATH", "")
            if not model_path or not os.path.isdir(model_path):
                # Check for the actual extracted model directory
                candidates = [
                    "models/vosk/en/vosk-model-small-en-us-0.15",
                    "models/vosk/en",
                    "models/vosk/vosk-model-small-en-us-0.15"
                ]
                for cand in candidates:
                    if os.path.isdir(cand) and os.path.exists(os.path.join(cand, "conf")):
                        model_path = cand
                        break
            
            if model_path and os.path.isdir(model_path):
                _vosk_model = Model(model_path)
                _vosk_available = True
                summary["vosk"] = True
            else:
                summary["vosk"] = False
        except Exception as e:
            print(f"Vosk init error: {e}")
            summary["vosk"] = False
    else:
        summary["vosk"] = True

    # pyttsx3 TTS
    if not _pyttsx3_available:
        try:
            import pyttsx3  # type: ignore
            _pyttsx3_engine = pyttsx3.init()
            _pyttsx3_available = True
            summary["pyttsx3"] = True
        except Exception as e:
            print(f"pyttsx3 init error: {e}")
            summary["pyttsx3"] = False
    else:
        summary["pyttsx3"] = True

    # Argos Translate
    if not _argos_available:
        try:
            import argostranslate.translate  # type: ignore
            import argostranslate.package    # type: ignore
            # Verify at least one language is installed
            langs = argostranslate.translate.get_installed_languages()
            if len(langs) > 0:
                _argos_available = True
                summary["argos"] = True
            else:
                summary["argos"] = False
        except Exception as e:
            print(f"Argos init error: {e}")
            summary["argos"] = False
    else:
        summary["argos"] = True

    st.session_state.setdefault("offline_capabilities", summary)
    st.session_state["offline_capabilities"] = summary
    return summary

def offline_stt(timeout: int = 8) -> Optional[str]:
    """Perform offline speech recognition using Vosk.
    Returns recognized text or None with user-facing warnings."""
    if not _vosk_available or _vosk_model is None:
        st.warning("Offline STT unavailable: install 'vosk' and place a model in 'models/vosk/en'.")
        return None
    try:
        import pyaudio  # type: ignore
        from vosk import KaldiRecognizer  # type: ignore
        import json as _json

        recognizer = KaldiRecognizer(_vosk_model, _vosk_samplerate)
        pa = pyaudio.PyAudio()
        stream = pa.open(format=pyaudio.paInt16, channels=1, rate=_vosk_samplerate, input=True, frames_per_buffer=4096)
        stream.start_stream()
        st.info("🎤 (Offline) Speak now...")

        import time
        start = time.time()
        result_text = []
        while time.time() - start < timeout:
            data = stream.read(4096, exception_on_overflow=False)
            if recognizer.AcceptWaveform(data):
                res = _json.loads(recognizer.Result())
                if res.get("text"):
                    result_text.append(res["text"])
            else:
                # partial = _json.loads(recognizer.PartialResult())  # can show partial if desired
                pass

        # Final flush
        final_res = _json.loads(recognizer.FinalResult())
        if final_res.get("text"):
            result_text.append(final_res["text"])

        stream.stop_stream(); stream.close(); pa.terminate()
        text_out = " ".join(result_text).strip()
        return text_out if text_out else None
    except Exception as e:
        st.error(f"Offline STT error: {e}")
        return None

def offline_tts(text: str, language: str = "en", output_file: str = "offline_output.mp3") -> Optional[str]:
    """Offline TTS via pyttsx3 (best for English). Returns path or None."""
    if not _pyttsx3_available or _pyttsx3_engine is None:
        st.warning("Offline TTS unavailable: install 'pyttsx3'.")
        return None
    try:
        # Attempt language voice selection heuristic
        voices = _pyttsx3_engine.getProperty("voices")
        target_voice = None
        lang_map_pref = {
            "en": ["en", "English"],
            "hi": ["hi", "Hindi"],
            "ta": ["ta", "Tamil"],
            "te": ["te", "Telugu"],
            "kn": ["kn", "Kannada"],
            "mr": ["mr", "Marathi"],
            "bn": ["bn", "Bengali"],
            "gu": ["gu", "Gujarati"],
            "pa": ["pa", "Punjabi"],
            "ur": ["ur", "Urdu"],
            "es": ["es", "Spanish"],
            "fr": ["fr", "French"],
            "de": ["de", "German"],
            "ja": ["ja", "Japanese"],
            "zh": ["zh", "Chinese"],
            "ar": ["ar", "Arabic"],
        }
        prefs = lang_map_pref.get(language, [])
        for v in voices:
            meta = f"{v.id} {getattr(v, 'name', '')} {getattr(v, 'languages', '')}".lower()
            if any(p.lower() in meta for p in prefs):
                target_voice = v.id
                break
        if target_voice:
            _pyttsx3_engine.setProperty("voice", target_voice)
        _pyttsx3_engine.save_to_file(text, output_file)
        _pyttsx3_engine.runAndWait()
        if os.path.exists(output_file):
            return output_file
    except Exception as e:
        st.error(f"Offline TTS error: {e}")
    return None

def offline_translate(text: str, src_lang: str = "auto", tgt_lang: str = "en") -> Optional[str]:
    """Offline translation via Argos Translate.
    Returns translated text or None with guidance."""
    if not _argos_available:
        st.warning("Offline translation unavailable: install 'argostranslate' and language packs.")
        return None
    try:
        import argostranslate.translate as arg_trans  # type: ignore
        import argostranslate.package as arg_pkg      # type: ignore

        installed = arg_trans.get_installed_languages()
        # Auto-detect simplified: if src_lang == 'auto', assume English if ASCII ratio > threshold
        if src_lang == "auto":
            ascii_ratio = sum(c.isascii() for c in text) / max(1, len(text))
            src_lang = "en" if ascii_ratio > 0.85 else "hi"  # heuristic fallback

        from_lang = next((l for l in installed if l.code == src_lang), None)
        to_lang = next((l for l in installed if l.code == tgt_lang), None)
        if not from_lang or not to_lang:
            st.warning(f"Argos language pack missing for {src_lang}->{tgt_lang}. Install appropriate .argosmodel packages.")
            return None
        translation = from_lang.get_translation(to_lang)
        return translation.translate(text)
    except Exception as e:
        st.error(f"Offline translation error: {e}")
        return None

def capabilities_summary() -> str:
    caps = st.session_state.get("offline_capabilities") or {}
    return json.dumps(caps, indent=2)

def is_offline_mode() -> bool:
    return bool(st.session_state.get("offline_mode_enabled", False))
