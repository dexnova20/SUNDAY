import os
import sys
import queue
import numpy as np
import sounddevice as sd
import vosk
import json
import whisper
import warnings

# Suppress warnings if running whisper on CPU
warnings.filterwarnings("ignore", message="FP16 is not supported on CPU")

class AudioManager:
    def __init__(self):
        # Initialize Vosk
        base_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(base_dir, "model")
        if not os.path.exists(model_path):
            print(f"ERROR: Vosk model not found at {os.path.abspath(model_path)}")
            print("Please download a lightweight model (e.g. vosk-model-small-en-us-0.15) from https://alphacephei.com/vosk/models and extract it to a folder named 'model' in this directory.")
            sys.exit(1)
            
        self.vosk_model = vosk.Model(model_path)

        self.input_device = None

        # Probe supported sample rates: try 16000 first (ideal for Vosk/Whisper), fallback to native
        for rate in [16000, 44100, 48000]:
            try:
                sd.check_input_settings(device=self.input_device, samplerate=rate, channels=1, dtype='int16')
                self.sample_rate = rate
                print(f"[Audio] Using sample rate: {self.sample_rate}Hz")
                break
            except Exception:
                continue
        else:
            # Last resort: read whatever the device reports
            try:
                self.sample_rate = int(sd.query_devices(None, 'input')['default_samplerate'])
            except Exception:
                self.sample_rate = 44100
            print(f"[Audio] Fallback sample rate: {self.sample_rate}Hz")

        # Initialize Whisper (Local)
        print("Loading local Whisper model ('base'). This may take a moment...")
        self.whisper_model = whisper.load_model("base")
        print("Whisper model loaded.")

        self.q = queue.Queue()

    def _audio_callback(self, indata, frames, time, status):
        if status:
            print(status, file=sys.stderr)
        self.q.put(bytes(indata))

    def listen_for_wake_word(self) -> bool:
        """Continuously listens using Vosk until 'sunday' is detected."""
        print("\n[Vosk] Listening for wake word ('sunday')...")
        while not self.q.empty():
            try:
                self.q.get_nowait()
            except queue.Empty:
                break

        # Vosk requires 16000Hz — resample on the fly if needed
        vosk_rate = 16000
        rec = vosk.KaldiRecognizer(self.vosk_model, vosk_rate)

        try:
            with sd.RawInputStream(samplerate=self.sample_rate, blocksize=8000, device=self.input_device,
                                   dtype='int16', channels=1, callback=self._audio_callback):
                while True:
                    data = self.q.get()
                    # Resample bytes to 16000Hz for Vosk if needed
                    if self.sample_rate != vosk_rate:
                        import numpy as np
                        import scipy.signal as sps
                        audio_np = np.frombuffer(data, dtype=np.int16).astype(np.float32)
                        num_samples = int(len(audio_np) * vosk_rate / self.sample_rate)
                        resampled = sps.resample(audio_np, num_samples).astype(np.int16)
                        data = resampled.tobytes()
                    if rec.AcceptWaveform(data):
                        res = json.loads(rec.Result())
                        text = res.get("text", "")
                        if "sunday" in text.lower():
                            print(f"\nWake word detected! (Vosk heard: '{text}')")
                            return True
        except sd.PortAudioError as e:
            print(f"\n[CRITICAL AUDIO ERROR] Could not access the microphone: {e}")
            print(">>> Troubleshooting Steps:")
            print("1. Kill any existing 'python' or 'pythonw' processes in Task Manager.")
            print("2. Check if Zoom, Teams, or Discord is using the mic.")
            print("3. Windows Settings -> Privacy -> Microphone -> Allow desktop apps: ON.")
            import time
            time.sleep(5)
            return False  # Graceful: let the main loop retry instead of crashing

    def listen_and_transcribe(self, record_seconds: int = 5) -> str:
        """Records a short window and transcribes it using local Whisper for high accuracy."""
        import string, time
        whisper_sample_rate = 16000

        # Whisper hallucinates common phrases on silence. Filter these out.
        HALLUCINATION_PHRASES = {
            "thank you", "thanks", "thank you.", "thanks.",
            "you", "bye", "bye bye", "goodbye",
            "", ".", "...", "the", "a", "and",
            "subtitles by", "www.mooji.org",
        }

        for attempt in range(2):
            print(f"\n[Whisper] Recording command for {record_seconds} seconds...")

            recording = sd.rec(
                int(record_seconds * self.sample_rate),
                samplerate=self.sample_rate,
                channels=1, dtype='float32',
                device=self.input_device
            )
            sd.wait()
            time.sleep(0.3)

            audio_array = recording.flatten()

            # --- SILENCE DETECTION ---
            # Use RMS energy on raw (un-normalized) audio.
            # Threshold 0.005 = very quiet room noise; anything below is silence.
            rms = float(np.sqrt(np.mean(audio_array ** 2)))
            print(f"[Audio] RMS energy: {rms:.5f}")
            if rms < 0.005:
                print("[Audio] Silence detected (RMS too low). Skipping transcription.")
                return ""

            # Resample to 16000 Hz if device native rate differs
            if self.sample_rate != whisper_sample_rate:
                import scipy.signal as sps
                num_samples = int(len(audio_array) * whisper_sample_rate / self.sample_rate)
                audio_array = sps.resample(audio_array, num_samples)

            # Normalize amplitude for Whisper
            max_amp = np.max(np.abs(audio_array))
            if max_amp > 0:
                audio_array = audio_array / max_amp

            try:
                result = self.whisper_model.transcribe(
                    audio_array,
                    fp16=False,
                    language="en",
                    # Prevents Whisper from "completing" sentences using previous context,
                    # which is the main cause of hallucinated words on silence.
                    condition_on_previous_text=False,
                )
                text = result.get("text", "").strip()

                # --- NO-SPEECH PROBABILITY FILTER ---
                # Whisper outputs a no_speech_prob per segment.
                # If ALL segments have high no-speech probability, the audio is silence.
                segments = result.get("segments", [])
                if segments:
                    avg_no_speech = sum(s.get("no_speech_prob", 0) for s in segments) / len(segments)
                    print(f"[Whisper] avg no_speech_prob: {avg_no_speech:.3f}")
                    if avg_no_speech > 0.6:
                        print("[Whisper] High no-speech probability — treating as silence.")
                        return ""

                print(f"[Transcript]: {text}")

                if not text:
                    if attempt == 0:
                        continue
                    return ""

                normalized = text.lower().translate(str.maketrans('', '', string.punctuation)).strip()

                # Filter out known Whisper hallucination phrases
                if normalized in HALLUCINATION_PHRASES:
                    print(f"[Whisper] Filtered hallucination: '{text}'")
                    return ""

                if normalized == "nano":
                    return "__SAGE_MODE_TRIGGER__"

                return text.replace("Nano", "[REDACTED]").replace("nano", "[REDACTED]")

            except Exception as e:
                print(f"[ERROR] Whisper: {e}")
                if attempt == 0:
                    continue
                return ""
        return ""

    def cleanup(self):
        # Sounddevice manages its own streams contextually
        pass
