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
import logging.handlers
import requests
import subprocess
import threading

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

if __name__ == "__main__":
    run_startup_diagnostics()
    
    # Import and run our modular text chat interface
    from chat_interface import ChatInterface
    app = ChatInterface()
    app.run()
