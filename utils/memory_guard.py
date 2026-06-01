# c:\Users\mshas\OneDrive\Desktop\SUNDAY\utils\memory_guard.py
"""
Memory Guard RAM Protection System for SUNDAY.
Checks available RAM dynamically and enters safe mode to prevent system lockups.
"""
import logging
from models.model_registry import get_system_ram_info

logger = logging.getLogger("MEMORY_GUARD")
logger.propagate = False

_memory_guard_active = False

def run_memory_guard_audit() -> bool:
    """
    Dynamically audits available physical RAM on startup or query loop.
    Enables protective restrictions if available RAM falls below 2.0 GB.
    """
    global _memory_guard_active
    try:
        ram_info = get_system_ram_info()
        avail = ram_info.get("avail_gb", 8.0)
        
        if avail < 2.0:
            if not _memory_guard_active:
                _memory_guard_active = True
                print(f"\n[MEMORY GUARD] WARNING: Low available RAM ({avail:.2f}GB). Activating RAM Protection Mode.")
                print("[MEMORY GUARD] Forcing model to llama3.2:1b, disabling pre-load caching.\n")
            return True
        else:
            _memory_guard_active = False
            return False
    except Exception as e:
        logger.warning(f"Error auditing system memory: {e}")
        return False

def is_memory_guard_active() -> bool:
    """Returns True if low physical memory protection is active."""
    return _memory_guard_active
