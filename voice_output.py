import os
import time
import pyttsx3

try:
    from gtts import gTTS
    import pygame
    ONLINE_READY = True
except ImportError:
    ONLINE_READY = False
    print("Warning: gTTS/pygame not found. Defaulting to offline voice.")

_MIXER_INITIALIZED = False

# Always use English — SUNDAY is an English-only assistant.
# Removing langdetect eliminates 100ms+ latency and prevents
# random misclassification of English as other languages.
_LANG = "en"
_AUDIO_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_voice.mp3")


def _init_mixer() -> bool:
    """Lazily initialise pygame mixer once."""
    global _MIXER_INITIALIZED
    if not _MIXER_INITIALIZED:
        try:
            pygame.mixer.init()
            _MIXER_INITIALIZED = True
        except Exception as e:
            print(f"[TTS] pygame mixer init failed: {e}")
            return False
    return True


def _cleanup_audio():
    """Delete the temp MP3 if it still exists (e.g. after a crash)."""
    try:
        if os.path.exists(_AUDIO_FILE):
            os.remove(_AUDIO_FILE)
    except Exception:
        pass


def _speak_online(text: str):
    """High-quality online TTS via gTTS + pygame. English only."""
    if not ONLINE_READY:
        raise RuntimeError("gTTS/pygame not installed")

    if not _init_mixer():
        raise RuntimeError("pygame mixer unavailable")

    tts = gTTS(text=text, lang=_LANG, slow=False)
    tts.save(_AUDIO_FILE)

    pygame.mixer.music.load(_AUDIO_FILE)
    pygame.mixer.music.play()

    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)

    pygame.mixer.music.unload()

    # Small delay to release Windows file handle before deleting
    time.sleep(0.15)
    _cleanup_audio()


def _speak_offline(text: str):
    """Fallback SAPI5 offline TTS (no internet required)."""
    try:
        engine = pyttsx3.init()
        engine.setProperty("rate", 170)
        engine.setProperty("volume", 1.0)
        for voice in engine.getProperty("voices"):
            if "zira" in voice.name.lower() or "female" in voice.name.lower():
                engine.setProperty("voice", voice.id)
                break
        engine.say(text)
        engine.runAndWait()
        del engine
    except Exception as e:
        print(f"[TTS] Offline engine error: {e}")


def speak(text: str):
    """
    Speak text aloud. Tries online (gTTS) first, falls back to offline (pyttsx3).
    Also prints to console for visibility.
    """
    if not text or not text.strip():
        return
    print(f"SUNDAY: {text}")
    try:
        _speak_online(text)
    except Exception:
        _speak_offline(text)


# Clean up any stale audio file left from a previous crash on import
_cleanup_audio()
