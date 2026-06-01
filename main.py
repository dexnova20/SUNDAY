# c:\Users\mshas\OneDrive\Desktop\SUNDAY\main.py
"""
SUNDAY TEXT-FIRST AGENT ENTRY POINT
Validates the Ollama connection and registers custom brain models.
Then transitions execution control entirely to the ChatInterface CLI subsystem.
"""
import sys
import os
import time
import logging
import requests
import subprocess
import threading

# Centralized settings and configuration paths
from config.settings import LOG_PATH, OLLAMA_URL

# Record boot start time for benchmarking
import time
BOOT_START_TIME = time.time()

# Load .env file so any environment variables defined there are available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Suppress root logger to prevent duplicate console output.
logging.getLogger().handlers = []
logging.getLogger().setLevel(logging.WARNING)

log = logging.getLogger("SUNDAY")
log.propagate = False

def run_startup_diagnostics():
    """
    Validates Ollama connection and handles auto-building of the sundaybrain model
    if the GGUF model is present at C:\\SUNDAY\\models\\heretic.gguf.
    """
    from utils.logger import get_log_level
    debug = get_log_level() >= 2

    # Run Memory Guard Audit on startup
    try:
        from utils.memory_guard import run_memory_guard_audit
        run_memory_guard_audit()
    except Exception:
        pass

    ollama_running = False

    for attempt in range(3):
        try:
            requests.get(OLLAMA_URL, timeout=2)
            ollama_running = True
            break
        except requests.ConnectionError:
            if attempt == 0:
                if debug:
                    print("[STARTUP] Ollama not running. Attempting to start...")
                try:
                    import platform
                    creation_flags = 0
                    if platform.system() == "Windows":
                        creation_flags = subprocess.CREATE_NO_WINDOW
                    subprocess.Popen(["ollama", "serve"], creationflags=creation_flags)
                except Exception as e:
                    if debug:
                        print(f"[STARTUP] Could not start Ollama: {e}")
            time.sleep(3)

    if not ollama_running:
        print("[STARTUP] CRITICAL: Ollama is not running. Please start it and restart SUNDAY.")
        return

    from config.settings import PREFERRED_MODEL
    if PREFERRED_MODEL == "auto":
        if debug:
            print("[STARTUP] Dynamic Auto-Routing ACTIVE.")
        return

    sundaybrain_exists = False
    try:
        response = requests.get(OLLAMA_URL.rstrip('/') + "/api/tags", timeout=3)
        if response.status_code == 200:
            models = [m["name"] for m in response.json().get("models", [])]
            sundaybrain_exists = any("sundaybrain" in m for m in models)
            if debug:
                print(f"[STARTUP] Installed models: {', '.join(models) if models else 'None'}")
    except Exception as e:
        if debug:
            print(f"[STARTUP] Could not query Ollama models: {e}")

    if not sundaybrain_exists:
        gguf_path = "C:\\SUNDAY\\models\\heretic.gguf"
        modelfile_path = "C:\\SUNDAY\\models\\Modelfile"

        if os.path.exists(gguf_path) and os.path.exists(modelfile_path):
            if debug:
                print("[STARTUP] Building 'sundaybrain' in background...")

            def build_model_task():
                try:
                    proc = subprocess.Popen(
                        ["ollama", "create", "sundaybrain", "-f", modelfile_path],
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
                    )
                    _, stderr = proc.communicate()
                    if proc.returncode != 0 and debug:
                        print(f"[STARTUP] Build failed: {stderr}")
                except Exception as ex:
                    if debug:
                        print(f"[STARTUP] Build exception: {ex}")

            threading.Thread(target=build_model_task, daemon=True).start()
        elif debug:
            print(f"[STARTUP] 'sundaybrain' not found. GGUF missing at {gguf_path}")

if __name__ == "__main__":
    run_startup_diagnostics()

    from interface.chat_interface import ChatInterface
    app = ChatInterface()
    app.run()
