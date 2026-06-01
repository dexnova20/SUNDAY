# c:\Users\mshas\OneDrive\Desktop\SUNDAY\memory\profile_manager.py
"""
User Profile Manager for SUNDAY.
Maintains a structured personal profile in data/profile.json.
Tracks field-level confidence scores, last updated timestamps, and historical values.
"""
import os
from datetime import datetime
from config.settings import BASE_DIR
from utils.file_utils import load_json, atomic_write_json

PROFILE_PATH = os.path.join(BASE_DIR, "data", "profile.json")

class ProfileManager:
    @staticmethod
    def load_profile() -> dict:
        """Loads the profile dictionary from file, initializing structure if necessary."""
        return load_json(PROFILE_PATH, dict)

    @staticmethod
    def save_profile(profile: dict):
        """Atomically saves the profile to data/profile.json."""
        atomic_write_json(PROFILE_PATH, profile)

    @staticmethod
    def update_profile(field: str, value: str, confidence: float = 1.0):
        """
        Updates a specific profile field with previous value history and confidence tracking.
        If a new value is different, the old value is archived in the history list.
        """
        if not field or not value:
            return

        profile = ProfileManager.load_profile()
        field_clean = field.strip().lower()
        value_clean = value.strip()

        now_str = datetime.now().isoformat()
        
        # Check if the field already exists
        if field_clean in profile and isinstance(profile[field_clean], dict):
            current_data = profile[field_clean]
            current_value = current_data.get("value")
            
            # If value is unchanged, just update timestamp/confidence if higher
            if current_value == value_clean:
                current_data["confidence"] = max(current_data.get("confidence", 0.5), confidence)
                current_data["last_updated"] = now_str
                # Mark as accessed
                current_data["last_accessed"] = now_str
            else:
                # Value has changed (correction/update)
                history_entry = {
                    "value": current_value,
                    "confidence": current_data.get("confidence", 0.5),
                    "updated_at": current_data.get("last_updated", now_str)
                }
                
                # Setup history list if not present
                history = current_data.get("history", [])
                if not isinstance(history, list):
                    history = []
                history.append(history_entry)
                
                # Keep history capped at 10 items
                history = history[-10:]
                
                # Update current field data
                profile[field_clean] = {
                    "value": value_clean,
                    "confidence": confidence,
                    "last_updated": now_str,
                    "last_accessed": now_str,
                    "history": history
                }
                
                from brain.learning_engine import LearningTelemetry
                LearningTelemetry.log(f"[MEMORY UPDATED] Profile field '{field_clean}': '{current_value}' -> '{value_clean}'")
        else:
            # New field
            profile[field_clean] = {
                "value": value_clean,
                "confidence": confidence,
                "last_updated": now_str,
                "last_accessed": now_str,
                "history": []
            }
            from brain.learning_engine import LearningTelemetry
            LearningTelemetry.log(f"[MEMORY STORED] Profile field '{field_clean}': '{value_clean}'")

        # Synchronize relationship graph
        try:
            from memory.relationship_manager import RelationshipManager
            pred_map = {
                "name": "named",
                "college": "studies_at",
                "branch": "studies_major",
                "occupation": "works_as",
                "location": "lives_in",
                "age": "has_age"
            }
            predicate = pred_map.get(field_clean, f"has_{field_clean}")
            RelationshipManager.add_relationship("User", predicate, value_clean, confidence=confidence)
        except Exception:
            pass

        profile["last_updated"] = now_str
        ProfileManager.save_profile(profile)

    @staticmethod
    def get_field(field: str) -> dict:
        """Retrieves raw data for a specific field, updating last accessed time."""
        profile = ProfileManager.load_profile()
        field_clean = field.strip().lower()
        
        if field_clean in profile and isinstance(profile[field_clean], dict):
            # Update last accessed
            profile[field_clean]["last_accessed"] = datetime.now().isoformat()
            ProfileManager.save_profile(profile)
            return profile[field_clean]
        return {}

    @staticmethod
    def get_profile() -> dict:
        """Returns simplified profile view of field values."""
        profile = ProfileManager.load_profile()
        simple_profile = {}
        for k, v in profile.items():
            if k != "last_updated" and isinstance(v, dict):
                # Update accessed timestamp
                v["last_accessed"] = datetime.now().isoformat()
                simple_profile[k] = v.get("value")
        if simple_profile:
            ProfileManager.save_profile(profile)
        return simple_profile

    @staticmethod
    def adjust_confidence(field: str, amount: float):
        """Boosts or penalizes the confidence score of a profile field."""
        profile = ProfileManager.load_profile()
        field_clean = field.strip().lower()
        
        if field_clean in profile and isinstance(profile[field_clean], dict):
            current_data = profile[field_clean]
            old_conf = current_data.get("confidence", 0.5)
            new_conf = round(min(1.0, max(0.0, old_conf + amount)), 2)
            current_data["confidence"] = new_conf
            current_data["last_updated"] = datetime.now().isoformat()
            
            from brain.learning_engine import LearningTelemetry
            LearningTelemetry.log(f"[MEMORY UPDATED] Profile field '{field_clean}' confidence: {old_conf:.2f} -> {new_conf:.2f}")
            
            if new_conf < 0.4:
                LearningTelemetry.log(f"[MEMORY MAINTENANCE] Removing stale profile field '{field_clean}' due to low confidence ({new_conf:.2f})")
                del profile[field_clean]

            profile["last_updated"] = datetime.now().isoformat()
            ProfileManager.save_profile(profile)
