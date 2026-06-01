# c:\Users\mshas\OneDrive\Desktop\SUNDAY\utils\helpers.py
"""
Auxiliary Helper Library for SUNDAY.
Provides standardized string normalizations, safe system subprocess Popen wrappers, and datetime formatters.
"""
import subprocess
import string
from typing import Union, List
from datetime import datetime

def normalize_command_text(text: str) -> str:
    """
    Standardizes user CLI commands by converting to lowercase,
    removing punctuation marks, and stripping whitespace.
    """
    if not text:
        return ""
    clean = text.lower().strip()
    clean = clean.translate(str.maketrans('', '', string.punctuation))
    return " ".join(clean.split())

def format_timestamp(dt: datetime = None, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Returns a formatted timestamp string for records or CLI logs."""
    if dt is None:
        dt = datetime.now()
    return dt.strftime(format_str)

def get_iso_timestamp() -> str:
    """Returns an ISO 8601 formatted timestamp string."""
    return datetime.now().isoformat()

def safe_subprocess_popen(command: Union[str, List[str]], shell: bool = True) -> subprocess.Popen:
    """
    Safely executes an external system program in a non-blocking background thread.
    Suppresses console window popups on Windows systems automatically.
    """
    creation_flags = 0
    # Apply CREATE_NO_WINDOW flag on Windows systems to avoid popping cmd boxes
    import platform
    if platform.system() == "Windows":
        creation_flags = subprocess.CREATE_NO_WINDOW
        
    try:
        proc = subprocess.Popen(
            command,
            shell=shell,
            creationflags=creation_flags,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return proc
    except Exception as e:
        raise OSError(f"Failed to spawn background subprocess wrapper: {e}")

def get_process_name_by_pid(pid: int) -> str:
    """
    Returns the process name associated with a given Process ID (PID).
    Completely dependency-free, running standard Windows tasklist checks.
    """
    if not pid or pid < 0:
        return "Unknown"
    try:
        output = subprocess.check_output(f'tasklist /FI "PID eq {pid}" /NH', shell=True).decode('utf-8', errors='ignore')
        parts = output.strip().split()
        if parts:
            return parts[0]
    except Exception:
        pass
    return "Unknown"
