# c:\Users\mshas\OneDrive\Desktop\SUNDAY\utils\logger.py
"""
Centralized Telemetry Logger for SUNDAY.
Three log levels: MINIMAL, NORMAL, DEBUG.
Only file handler here — no StreamHandler to avoid duplicate console output.
"""
import os
import logging
import logging.handlers
from config.settings import LOG_PATH

# Log levels: MINIMAL=0, NORMAL=1, DEBUG=2
_log_level = 0  # Default: MINIMAL (PRODUCTION default)

os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

# 1. Setup SUNDAY_SYSTEM Logger idempotently
_logger = logging.getLogger("SUNDAY_SYSTEM")
_logger.setLevel(logging.INFO)
_logger.propagate = False  # Prevent propagation to root logger

# Clear any duplicate handlers that might have been registered
for h in list(_logger.handlers):
    _logger.removeHandler(h)

_file_handler = logging.handlers.RotatingFileHandler(
    LOG_PATH, maxBytes=5 * 1024 * 1024, backupCount=2, encoding="utf-8"
)
_file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
_logger.addHandler(_file_handler)

# 2. Setup Root Logger idempotently to completely suppress library console spam
root_logger = logging.getLogger()
for h in list(root_logger.handlers):
    root_logger.removeHandler(h)
root_logger.setLevel(logging.WARNING)

# Suppress specific library loggers actively to prevent terminal pollution
for lib_name in ["pywinauto", "urllib3", "requests", "PIL", "comtypes", "pytesseract"]:
    lib_logger = logging.getLogger(lib_name)
    lib_logger.handlers = []
    lib_logger.propagate = False
    lib_logger.setLevel(logging.WARNING)


# Categories visible per log level
_NORMAL_CATEGORIES = {"INPUT", "ACTION", "ROUTER", "EXECUTOR"}
_DEBUG_CATEGORIES = {"BRAIN", "VISION", "MEMORY", "PROJECT", "SESSION", "OCR", "UI CONTEXT", "ACTIVE WINDOW", "PLANNER", "SYSTEM"}

def set_log_level(level: int):
    """Set log level: 0=MINIMAL, 1=NORMAL, 2=DEBUG"""
    global _log_level
    _log_level = max(0, min(2, level))

def get_log_level() -> int:
    return _log_level

def get_system_logger() -> logging.Logger:
    return _logger

def log_msg(category: str, message: str):
    """
    Prints structured telemetry based on active log level.
    MINIMAL: silent. NORMAL: action/routing only. DEBUG: everything.
    """
    normalized_cat = category.upper().strip()

    # Always write to file
    _logger.info(f"[{normalized_cat}] {message}")

    # Console output gated by log level
    if _log_level == 0:
        return  # MINIMAL: no console output from log_msg
    if _log_level == 1 and normalized_cat not in _NORMAL_CATEGORIES:
        return  # NORMAL: only action/routing categories
    # DEBUG: print everything
    print(f"[{normalized_cat}] {message}")

def log_debug(message: str):
    """Prints benchmark/trace output only in DEBUG mode."""
    _logger.debug(message)
    if _log_level >= 2:
        print(message)
