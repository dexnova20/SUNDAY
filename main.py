import sys
import os
import time
import string
import threading
import logging
import logging.handlers
from vision_engine import VisionSession
from hotkey_manager import HotkeyManager
import requests
from datetime import datetime

# Load .env file so any environment variables defined there are available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ── Logging setup: rotate sunday.log at 5 MB, keep 2 backups ──────────────────
_log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sunday.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.handlers.RotatingFileHandler(
            _log_path, maxBytes=5 * 1024 * 1024, backupCount=2, encoding="utf-8"
        ),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("SUNDAY")

# Give Windows audio drivers time to initialize on boot
if "--boot" in sys.argv:
    _delay = int(os.environ.get("SUNDAY_BOOT_DELAY", "30"))
    print(f"Boot mode detected. Waiting {_delay}s for audio drivers to initialize...")
    time.sleep(_delay)

from audio_manager import AudioManager
from brain import BrainModule
from permission_manager import PermissionManager
from action_executor import ActionExecutor
from context_manager import ContextManager
from voice_output import speak

# --- Response Cache: instant replies without LLM ---
RESPONSE_CACHE = {
    "hello": "Hey! How can I help?",
    "hi": "Hey! How can I help?",
    "hey": "Hey! How can I help?",
    "how are you": "I'm running great, thanks for asking!",
    "what time is it": lambda: f"It's {datetime.now().strftime('%I:%M %p')}.",
    "what is the time": lambda: f"It's {datetime.now().strftime('%I:%M %p')}.",
    "what day is it": lambda: f"Today is {datetime.now().strftime('%A, %B %d')}.",
    "thank you": "You're welcome!",
    "thanks": "Anytime!",
}

def run_startup_diagnostics():
    """
    Validates Ollama connection and handles auto-building of the sundaybrain model
    if the GGUF model is present at C:\\SUNDAY\\models\\heretic.gguf.
    """
    print("\n" + "="*60)
    print("      SUNDAY OPERATIONAL BRAIN DIAGNOSTICS & STARTUP CHECK")
    print("="*60)
    
    ollama_url = "http://localhost:11434/"
    ollama_running = False
    
    # 1. Verify/Start Ollama service
    for attempt in range(3):
        try:
            requests.get(ollama_url, timeout=2)
            ollama_running = True
            print("[STARTUP] Ollama service is connected and running.")
            break
        except requests.ConnectionError:
            if attempt == 0:
                print("[STARTUP] Ollama is not running. Attempting to start the service...")
                try:
                    subprocess.Popen(["ollama", "serve"], creationflags=subprocess.CREATE_NO_WINDOW)
                except Exception as e:
                    print(f"[STARTUP] [ERROR] Could not start Ollama automatically: {e}")
            time.sleep(3)
            
    if not ollama_running:
        print("[STARTUP] [CRITICAL] Ollama service is not running and could not be started.")
        print("[STARTUP] Please start Ollama manually and restart SUNDAY.")
        print("="*60 + "\n")
        return

    # 2. Check if sundaybrain is installed
    sundaybrain_exists = False
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=3)
        if response.status_code == 200:
            models = [m["name"] for m in response.json().get("models", [])]
            if any("sundaybrain" in m for m in models):
                sundaybrain_exists = True
                print("[STARTUP] Custom brain model 'sundaybrain' is successfully registered.")
            else:
                available = ", ".join(models) if models else "None"
                print(f"[STARTUP] 'sundaybrain' not found. Installed models: {available}")
    except Exception as e:
        print(f"[STARTUP] [ERROR] Could not query Ollama models: {e}")

    # 3. Handle Auto-Build or Setup Guidance
    if not sundaybrain_exists:
        gguf_path = "C:\\SUNDAY\\models\\heretic.gguf"
        modelfile_path = "C:\\SUNDAY\\models\\Modelfile"
        
        if os.path.exists(gguf_path) and os.path.exists(modelfile_path):
            print(f"[STARTUP] Local GGUF found at {gguf_path}!")
            print(f"[STARTUP] Modelfile found at {modelfile_path}!")
            print("[STARTUP] Launching background build process for 'sundaybrain'...")
            
            def build_model_task():
                try:
                    # We run this in a background thread to prevent blocking SUNDAY startup
                    import subprocess
                    proc = subprocess.Popen(
                        ["ollama", "create", "sundaybrain", "-f", modelfile_path],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                    stdout, stderr = proc.communicate()
                    if proc.returncode == 0:
                        print("\n[OLLAMA] [BUILD SUCCESS] Custom model 'sundaybrain' has been built and registered successfully!")
                    else:
                        print(f"\n[OLLAMA] [BUILD FAILED] Failed to build custom model: {stderr}")
                except Exception as ex:
                    print(f"\n[OLLAMA] [BUILD FAILED] Exception in background build: {ex}")
            
            threading.Thread(target=build_model_task, daemon=True).start()
            print("[STARTUP] Background build task started. This will take 1-3 minutes.")
            print("[STARTUP] SUNDAY will run using the best available fallback model in the meantime.")
        else:
            print("[STARTUP] [WARNING] Custom brain 'sundaybrain' is missing and GGUF model was not found!")
            print(f"[STARTUP] Expected GGUF location: {gguf_path}")
            print("[STARTUP] Expected Modelfile location: C:\\SUNDAY\\models\\Modelfile")
            print("[STARTUP] Setup instructions have been generated at: C:\\SUNDAY\\models\\setup_instructions.md")
            print("[STARTUP] Please follow those instructions. SUNDAY will load fallback models for now.")

    print("="*60 + "\n")

class SundayAssistant:
    def __init__(self):
        print("Initializing SUNDAY Assistant...")
        try:
            self.audio_manager = AudioManager()
            self.brain = BrainModule()
            self.permission_manager = PermissionManager(self.audio_manager)
            # Initialize Vision Session and Hotkey Manager
            self.vision_session = VisionSession()
            self.hotkey_manager = HotkeyManager(self.vision_session)
            self.executor = ActionExecutor()
            print("Initialization Complete.")
        except Exception as e:
            print(f"Failed to initialize SUNDAY: {e}")
            sys.exit(1)

    def run(self):
        """The main execution loop."""
        print("\nSUNDAY is running. Press Ctrl+C to exit.")
        try:
            while True:
                try:
                    wake_word_detected = self.audio_manager.listen_for_wake_word()

                    if wake_word_detected:
                        speak("Yes?")

                        conversation_mode = True
                        empty_count = 0
                        turns_count = 0
                        pending_task = None
                        task_turns = 0

                        while conversation_mode and turns_count < 10:
                            turns_count += 1

                            # Capture lightweight context (no screen read yet)
                            context = {
                                "active_window": ContextManager.get_active_window_title(),
                                "open_windows": ContextManager.get_all_window_titles(),
                                "screen_text": ""
                            }

                            command_text = self.audio_manager.listen_and_transcribe()

                            # --- SAGE MODE TRIGGER ---
                            if command_text == "__SAGE_MODE_TRIGGER__":
                                speak("Sage mode activated.")
                                explanation = self.audio_manager.listen_and_transcribe(record_seconds=30)
                                if explanation:
                                    from memory_manager import MemoryManager
                                    MemoryManager.save_knowledge(explanation)
                                    speak("Knowledge stored.")
                                conversation_mode = False
                                continue

                            # Silence handling
                            if not command_text:
                                empty_count += 1
                                if empty_count >= 2:
                                    conversation_mode = False
                                continue

                            empty_count = 0

                            normalized_cmd = command_text.lower().translate(str.maketrans('', '', string.punctuation)).strip()

                            # Exit commands
                            if normalized_cmd == "done":
                                speak("Ending session.")
                                conversation_mode = False
                                continue

                            if normalized_cmd in ["cancel", "stop", "nevermind", "abort"]:
                                if pending_task:
                                    speak("Task cancelled.")
                                    pending_task = None
                                    task_turns = 0
                                else:
                                    speak("Ending session.")
                                    conversation_mode = False
                                continue

                            # On-demand screen read
                            screen_triggers = ["what is on my screen", "whats on my screen", "explain this", "read my screen"]
                            if any(t in normalized_cmd for t in screen_triggers):
                                # Use VisionSession context if available, fallback to raw screen text
                                if hasattr(self, "vision_session") and self.vision_session.context:
                                    summary = self.vision_session.context.get("summary", "")
                                    important = self.vision_session.context.get("important_text", "")
                                    context["screen_text"] = f"{summary}\nImportant: {important}" if summary else self.vision_session.context.get("ocr_text", "")
                                else:
                                    context["screen_text"] = ContextManager.read_screen_text()

                            # --- CACHE CHECK (instant, no LLM) ---
                            if not pending_task:
                                cached = RESPONSE_CACHE.get(normalized_cmd)
                                if cached:
                                    reply = cached() if callable(cached) else cached
                                    speak(reply)
                                    time.sleep(1)
                                    continue

                            # --- SHORTCUT ENGINE (no Whisper/Ollama overhead) ---
                            if not pending_task:
                                intent_data = self.executor.evaluate_shortcut(command_text)
                                if intent_data:
                                    print(f"[SHORTCUT] {intent_data['intent']}")
                                    intent_data["is_complete"] = True
                                else:
                                    speak("Let me think...")
                                    intent_data = self.brain.process_command(command_text, context)
                            else:
                                task_turns += 1
                                if task_turns > 3:
                                    speak("Task taking too long. Resetting.")
                                    pending_task = None
                                    task_turns = 0
                                    continue
                                speak("Let me think...")
                                intent_data = self.brain.process_command(command_text, context, pending_task)

                            if not isinstance(intent_data, dict):
                                intent_data = {"intent": "unknown", "is_complete": True}

                            is_complete = intent_data.get("is_complete", True)

                            if not is_complete:
                                pending_task = intent_data
                                speak(intent_data.get("follow_up_question", "Please provide more details."))
                                continue

                            pending_task = None
                            task_turns = 0

                            intent = intent_data.get("intent", "unknown")
                            parameters = intent_data.get("parameters", {})
                            sensitivity = intent_data.get("sensitivity", 0)
                            reply_text = intent_data.get("reply_text", "")

                            print(f"[INTENT] {intent}")

                            if intent == "unknown":
                                speak("I didn't understand that command.")
                                time.sleep(1)
                                continue

                            if intent == "general_query" and reply_text:
                                speak(reply_text)
                                time.sleep(1)
                                continue

                            permission_granted = self.permission_manager.request_permission(
                                intent=intent, parameters=parameters, sensitivity=sensitivity
                            )

                            if permission_granted:
                                # Run execution in background thread to keep loop responsive
                                threading.Thread(
                                    target=self._execute_and_confirm,
                                    args=(intent, parameters, context),
                                    daemon=True
                                ).start()
                            else:
                                speak("Action aborted.")

                            time.sleep(1)

                except Exception as e:
                    print(f"[CRITICAL ERROR] {e}")
                    import traceback
                    traceback.print_exc()
                    time.sleep(3)

        except KeyboardInterrupt:
            print("\nShutting down SUNDAY...")
            speak("Bye boss")
        finally:
            self.audio_manager.cleanup()

    def _execute_and_confirm(self, intent, parameters, context):
        self.executor.execute(intent, parameters, context)
        if intent not in ["solve_query"]:
            speak("Done.")

if __name__ == "__main__":
    # Ensure this runs strictly in background
    # (To run completely hidden on Windows, use `pythonw main.py`)
    run_startup_diagnostics()
    app = SundayAssistant()
    app.run()
