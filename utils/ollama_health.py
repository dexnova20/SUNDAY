# c:\Users\mshas\OneDrive\Desktop\SUNDAY\utils\ollama_health.py
"""
Ollama Connection Health Monitor for SUNDAY.
Tracks response successes, timeouts, consecutive failures, and triggers automatic recovery.
"""
import logging
import subprocess
import platform

logger = logging.getLogger("HEALTH_MONITOR")
logger.propagate = False

_consecutive_failures = 0
_timeout_count = 0
_total_successes = 0
_total_latencies = 0.0
_force_downgrade = False

def record_success(latency: float):
    """Logs a successful query and resets consecutive failures."""
    global _consecutive_failures, _total_successes, _total_latencies
    _consecutive_failures = 0
    _total_successes += 1
    _total_latencies += latency

def record_failure(is_timeout: bool = False) -> bool:
    """
    Logs a request failure. If 3 consecutive failures occur,
    initiates connection restart and active model downgrade.
    """
    global _consecutive_failures, _timeout_count, _force_downgrade
    _consecutive_failures += 1
    if is_timeout:
        _timeout_count += 1
        
    logger.warning(f"[HEALTH MONITOR] Query failed ({_consecutive_failures}/3).")
    
    if _consecutive_failures >= 3:
        _force_downgrade = True
        trigger_recovery()
        return True
    return False

def is_health_downgrade_active() -> bool:
    """Returns True if recovery forced model downgrade is active."""
    return _force_downgrade

def get_average_latency() -> float:
    """Returns the computed running average latency of successful calls."""
    if _total_successes == 0:
        return 0.0
    return _total_latencies / _total_successes

def trigger_recovery():
    """Triggers system process restarts and downgrades."""
    global _consecutive_failures
    _consecutive_failures = 0
    print("\n[HEALTH MONITOR] CRITICAL: 3 consecutive Ollama failures detected!")
    print("[HEALTH MONITOR] Attempting serve process restart and forcing Llama 1B downgrade...")
    
    # 1. Spawn Ollama serve in background
    try:
        creation_flags = 0
        if platform.system() == "Windows":
            creation_flags = subprocess.CREATE_NO_WINDOW
            
        subprocess.Popen(
            ["ollama", "serve"],
            shell=True,
            creationflags=creation_flags,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print("[HEALTH MONITOR] Connection serving triggered successfully.")
    except Exception as e:
        print(f"[HEALTH MONITOR] Serve process failed to launch: {e}")
        
    print("[HEALTH MONITOR] Please re-run your prompt to resume with optimized speed.\n")
