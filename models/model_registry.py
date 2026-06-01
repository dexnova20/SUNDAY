# c:\Users\mshas\OneDrive\Desktop\SUNDAY\models\model_registry.py
"""
Model Registry for SUNDAY.
Defines available models, fallback order, and dynamic model routing logic.
Includes ctypes-based zero-dependency RAM diagnostics.
"""
import ctypes
import logging

logger = logging.getLogger("REGISTRY")

# Centralized Model definitions
MODEL_REGISTRY = {
    "llama3.2:latest": {
        "name": "llama3.2:latest",
        "description": "Llama 3.2 3B model, optimized for balanced speed and intelligence.",
        "size": "3B",
        "speed": "High",
        "class": "Balanced"
    },
    "phi3:latest": {
        "name": "phi3:latest",
        "description": "Phi-3 3.8B model, outstanding logic, coding, and math reasoning.",
        "size": "3.8B",
        "speed": "High",
        "class": "Code/Logic"
    },
    "llama3:8b": {
        "name": "llama3:8b",
        "description": "Standard Llama 3 8B model, deep reasoning fallback.",
        "size": "8B",
        "speed": "Medium",
        "class": "Reasoning"
    },
    "llama3.2:1b": {
        "name": "llama3.2:1b",
        "description": "Ultra-lightweight Llama 3.2 1B model, maximum velocity.",
        "size": "1B",
        "speed": "Ultra-High",
        "class": "Fastest"
    }
}

# Mode-to-Model priority mapping (Approved Requirement)
MODE_MODEL_PRIORITY = {
    "FAST": "llama3.2:1b",
    "NORMAL": "llama3.2:latest",
    "THINK": "llama3.2:latest",
    "CODE": "phi3:latest"
}

# Configured fallback priority chain matching user preference exactly
FALLBACK_ORDER = ["llama3.2:latest", "phi3:latest", "llama3:8b", "llama3.2:1b"]

class MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [
        ("dwLength", ctypes.c_ulong),
        ("dwMemoryLoad", ctypes.c_ulong),
        ("ullTotalPhys", ctypes.c_ulonglong),
        ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong),
        ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong),
        ("ullAvailVirtual", ctypes.c_ulonglong),
        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
    ]

def get_system_ram_info() -> dict:
    """
    Zero-dependency retrieval of total and available RAM in GB, and memory load in % on Windows.
    """
    try:
        stat = MEMORYSTATUSEX()
        stat.dwLength = ctypes.sizeof(stat)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
        return {
            "total_gb": stat.ullTotalPhys / (1024**3),
            "avail_gb": stat.ullAvailPhys / (1024**3),
            "memory_load": stat.dwMemoryLoad
        }
    except Exception as e:
        logger.warning(f"Failed to query system RAM via ctypes: {e}")
        # Failsafe values
        return {
            "total_gb": 8.0,
            "avail_gb": 4.0,
            "memory_load": 50
        }

def match_tag(model_name: str, available_tags: list) -> str:
    """
    Finds a direct or partial match for a model name in the installed Ollama tags.
    """
    # Normalize comparison names
    name_clean = model_name.lower().replace(":latest", "").strip()
    
    # Try exact match first
    for tag in available_tags:
        if tag.lower() == model_name.lower():
            return tag
            
    # Try exact clean name match
    for tag in available_tags:
        tag_clean = tag.lower().replace(":latest", "").strip()
        if tag_clean == name_clean:
            return tag
            
    # Try substring match
    for tag in available_tags:
        if name_clean in tag.lower():
            return tag
            
    return ""

def get_best_available_model(available_tags: list) -> str:
    """
    Returns the first matching model in FALLBACK_ORDER that is installed in Ollama.
    """
    for model_name in FALLBACK_ORDER:
        matched = match_tag(model_name, available_tags)
        if matched:
            return matched
            
    # Failsafe fallback
    if available_tags:
        return available_tags[0]
    return "llama3.2:1b"

def get_model_for_mode(mode: str, available_tags: list) -> str:
    """
    Resolves the active model based on switchable brain modes and installed Ollama tags.
    Applies strict fallback logic if the target mode model is not installed.
    """
    try:
        from utils.memory_guard import is_memory_guard_active
        from utils.ollama_health import is_health_downgrade_active
        if is_memory_guard_active() or is_health_downgrade_active():
            matched = match_tag("llama3.2:1b", available_tags)
            if matched:
                return matched
            return "llama3.2:1b"
    except Exception:
        pass

    target_model_name = MODE_MODEL_PRIORITY.get(mode.upper())
    if target_model_name:
        matched = match_tag(target_model_name, available_tags)
        if matched:
            return matched
            
    # Fallback to general priority chain
    return get_best_available_model(available_tags)
