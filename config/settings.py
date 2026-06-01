# c:\Users\mshas\OneDrive\Desktop\SUNDAY\config\settings.py
"""
Central Configuration Settings for SUNDAY.
Defines base directory, Ollama API URLs, model search chains, and resolves absolute
paths to the data, logs, and screenshot folders.
"""
import os

# Base Directory of the SUNDAY Project (points to the root SUNDAY folder)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Ollama Core Settings
OLLAMA_URL = "http://localhost:11434/"
PREFERRED_MODEL = "auto"
FALLBACK_CHAIN = ["llama3.2:latest", "phi3:latest", "llama3:8b", "llama3.2:1b"]

# Persistent Paths relative to BASE_DIR
MEMORY_PATH = os.path.join(BASE_DIR, "data", "memory.json")
SESSION_PATH = os.path.join(BASE_DIR, "data", "session.json")
LOG_PATH = os.path.join(BASE_DIR, "logs", "sunday.log")

# Desktop Screenshot Path
_desktop = os.path.join(os.path.expanduser("~"), "OneDrive", "Desktop")
if not os.path.exists(_desktop):
    _desktop = os.path.join(os.path.expanduser("~"), "Desktop")
SCREENSHOT_PATH = _desktop
