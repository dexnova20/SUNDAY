# c:\Users\mshas\OneDrive\Desktop\SUNDAY\utils\file_utils.py
"""
File Operations Utility Library for SUNDAY.
Implements safe folder creation, automatic backups before file overwrites, and atomic temp-file JSON serializations.
"""
import os
import json
import shutil
from typing import Dict, List, Union

def ensure_directory(file_path: str):
    """Safely creates parent directories for a target file path."""
    if not file_path:
        return
    parent = os.path.dirname(os.path.abspath(file_path))
    os.makedirs(parent, exist_ok=True)

def create_backup(file_path: str) -> bool:
    """Creates a safety backup .bak copy of the target file if it already exists."""
    try:
        if os.path.exists(file_path):
            backup_path = file_path + ".bak"
            shutil.copy2(file_path, backup_path)
            return True
    except Exception:
        pass
    return False

def atomic_write_json(file_path: str, data: Union[Dict, List], indent: int = 4) -> bool:
    """
    Safely and atomically writes JSON data to disk.
    Creates a backup first, writes to a temporary file, then performs an atomic file swap.
    """
    if not file_path:
        return False
        
    try:
        # 1. Ensure directory path structure exists
        ensure_directory(file_path)
        
        # 2. Automatically generate a safety backup file
        create_backup(file_path)
        
        # 3. Write data to a temporary file in the same folder
        temp_file = file_path + ".tmp"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent)
            
        # 4. Perform atomic swap to replace original file with temp
        os.replace(temp_file, file_path)
        return True
    except Exception as e:
        # Cleanup temp file if it left residue
        temp_file = file_path + ".tmp"
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except Exception:
                pass
        raise IOError(f"Atomic JSON write failed for {file_path}: {e}")

def load_json(file_path: str, default_factory=list) -> Union[Dict, List]:
    """Safely loads a JSON database file, returning a default factory if missing/corrupted."""
    if not os.path.exists(file_path):
        return default_factory()
        
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            loaded = json.load(f)
            return loaded if loaded is not None else default_factory()
    except Exception:
        # If original file is corrupt, try recovery from backup (.bak)
        backup_path = file_path + ".bak"
        if os.path.exists(backup_path):
            try:
                with open(backup_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return default_factory()
