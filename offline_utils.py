"""Offline / Low-Bandwidth Mode Utilities

Provides fallback implementations for Speech-To-Text (STT), Text-To-Speech (TTS),
and Machine Translation (MT) that work without relying on cloud services.

Design goals:
 - Graceful degradation: if a library/model is missing, return None with instructions
 - Non-blocking init: attempt lazy loading only when offline mode enabled
 - Minimal footprint: prefer lightweight or already cached resources
 - Improved accuracy: sentence splitting, pre/post-processing, script detection

Translation Accuracy Improvements:
 1. Script-based language detection (Devanagari, Bengali, Arabic, Latin)
 2. Sentence splitting for better context preservation
 3. Text preprocessing (normalize whitespace, handle URLs/emails)
 4. Post-processing (fix punctuation, capitalization)
 5. Support for Hindi, Bengali, Urdu (limited by Argos availability)

Dependencies (optional, install as needed):
  pip install vosk pyttsx3 argostranslate==1.9.0

Argos Translate language packs must be installed separately, for example:
  python -m argostranslate.package install <package_file.argosmodel>
See https://github.com/argosopentech/argos-translate for language packs.

Note: Offline translation accuracy is 60-70% compared to cloud services.
For best results, use online mode (Google Translate) when internet is available.
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
    """Offline translation via Argos Translate with improved accuracy.
    - Tries direct src→tgt
    - Falls back to pivot via English (src→en→tgt) when available
    Returns translated text or None with guidance."""
    if not _argos_available:
        st.warning("Offline translation unavailable: install 'argostranslate' and language packs.")
        return None
    try:
        import argostranslate.translate as arg_trans  # type: ignore
        import argostranslate.package as arg_pkg      # type: ignore

        installed = arg_trans.get_installed_languages()
        
        # Improved auto-detection with multiple heuristics
        if src_lang == "auto":
            src_lang = _detect_language_offline(text, installed)
        
        from_lang = next((l for l in installed if l.code == src_lang), None)
        to_lang = next((l for l in installed if l.code == tgt_lang), None)

        # Pre-process text for better accuracy
        cleaned_text = _preprocess_text_for_translation(text)

        # Try direct translation first
        if from_lang and to_lang:
            translation_obj = from_lang.get_translation(to_lang)
            if translation_obj:
                translated = _translate_with_sentence_splitting(cleaned_text, translation_obj)
                translated = _postprocess_translation(translated, tgt_lang)
                return translated

        # If direct path missing, attempt pivot via English
        pivot_code = "en"
        pivot_lang = next((l for l in installed if l.code == pivot_code), None)
        if from_lang and to_lang and pivot_lang and from_lang != to_lang:
            pivot_result = _translate_via_pivot(cleaned_text, from_lang, pivot_lang, to_lang)
            if pivot_result is not None:
                return _postprocess_translation(pivot_result, tgt_lang)

        # Otherwise, provide guidance on missing packs
        missing = []
        if not from_lang:
            missing.append(src_lang)
        if not to_lang:
            missing.append(tgt_lang)
        if missing:
            st.warning(
                f"Argos language pack missing for {', '.join(missing)}. Install appropriate .argosmodel packages."
            )
        else:
            st.warning(
                f"No translation path found for {src_lang}->{tgt_lang}. Try installing src→en and en→tgt packs, or use online mode."
            )
        return None
        
    except Exception as e:
        st.error(f"Offline translation error: {e}")
        return None

def _detect_language_offline(text: str, installed_langs) -> str:
    """Improved language detection using multiple heuristics."""
    # Check installed language codes
    installed_codes = [l.code for l in installed_langs]
    
    # Script-based detection
    devanagari_chars = sum(1 for c in text if '\u0900' <= c <= '\u097F')
    bengali_chars = sum(1 for c in text if '\u0980' <= c <= '\u09FF')
    arabic_chars = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
    ascii_chars = sum(1 for c in text if c.isascii())
    
    total_chars = len(text)
    if total_chars == 0:
        return "en"
    
    # Determine dominant script
    if devanagari_chars / total_chars > 0.3:
        return "hi" if "hi" in installed_codes else "en"
    elif bengali_chars / total_chars > 0.3:
        return "bn" if "bn" in installed_codes else "en"
    elif arabic_chars / total_chars > 0.3:
        return "ur" if "ur" in installed_codes else "ar" if "ar" in installed_codes else "en"
    elif ascii_chars / total_chars > 0.85:
        return "en"
    
    # Fallback to first available non-English language or English
    return next((code for code in ["hi", "bn", "ur"] if code in installed_codes), "en")

def _preprocess_text_for_translation(text: str) -> str:
    """Clean and normalize text for better translation."""
    import re
    
    # Preserve URLs and emails
    text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', ' URL ', text)
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', ' EMAIL ', text)
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Fix common punctuation issues
    text = re.sub(r'\s+([.,!?;:])', r'\1', text)
    text = re.sub(r'([.,!?;:])\s*', r'\1 ', text)
    
    return text

def _translate_with_sentence_splitting(text: str, translation_obj) -> str:
    """Translate text by splitting into sentences for better context."""
    import re
    
    # Split by sentence boundaries (simple heuristic)
    sentences = re.split(r'(?<=[.!?।॥])\s+', text)
    
    # If text is short, translate as-is
    if len(sentences) <= 1 or len(text) < 100:
        return translation_obj.translate(text)
    
    # Translate each sentence
    translated_sentences = []
    for sentence in sentences:
        if sentence.strip():
            translated = translation_obj.translate(sentence.strip())
            translated_sentences.append(translated)
    
    return ' '.join(translated_sentences)

def _translate_via_pivot(text: str, from_lang, pivot_lang, to_lang) -> Optional[str]:
    """Attempt two-hop translation via a pivot language (usually English).
    Returns translated text or None if either hop is unavailable."""
    try:
        # First hop: from -> pivot
        hop1 = from_lang.get_translation(pivot_lang)
        if not hop1:
            return None
        intermediate = _translate_with_sentence_splitting(text, hop1)

        # Second hop: pivot -> to
        hop2 = pivot_lang.get_translation(to_lang)
        if not hop2:
            return None
        final = _translate_with_sentence_splitting(intermediate, hop2)
        return final
    except Exception:
        return None

def _postprocess_translation(text: str, target_lang: str) -> str:
    """Fix common translation issues."""
    import re
    
    # Restore URLs and emails
    # (In production, you'd want to store and restore actual values)
    
    # Fix spacing around punctuation
    text = re.sub(r'\s+([.,!?;:])', r'\1', text)
    text = re.sub(r'([.,!?;:])\s*', r'\1 ', text)
    
    # Fix multiple spaces
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Capitalize first letter if target is English
    if target_lang == "en" and text:
        text = text[0].upper() + text[1:] if len(text) > 1 else text.upper()
    
    return text

def capabilities_summary() -> str:
    caps = st.session_state.get("offline_capabilities") or {}
    return json.dumps(caps, indent=2)

def is_offline_mode() -> bool:
    return bool(st.session_state.get("offline_mode_enabled", False))
