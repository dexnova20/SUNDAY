# c:\Users\mshas\OneDrive\Desktop\SUNDAY\memory\preference_manager.py
"""
Preference Manager for SUNDAY.
Learns, tracks, and manages user preferences with frequency-based scoring,
confidence levels, aging, and retrieval support.
"""
import os
from datetime import datetime
from config.settings import BASE_DIR
from utils.file_utils import load_json, atomic_write_json

PREFERENCES_PATH = os.path.join(BASE_DIR, "data", "preferences.json")

class PreferenceManager:
    @staticmethod
    def load_preferences() -> dict:
        """Loads preference database from disk."""
        return load_json(PREFERENCES_PATH, dict)

    @staticmethod
    def save_preferences(prefs: dict):
        """Atomically saves preferences database to disk."""
        atomic_write_json(PREFERENCES_PATH, prefs)

    @staticmethod
    def add_preference(category: str, value: str, weight: float = 0.2):
        """
        Learns or updates a user preference.
        Uses frequency scoring where repeated mentions increase the confidence level.
        """
        if not category or not value:
            return

        prefs = PreferenceManager.load_preferences()
        category_clean = category.strip().lower()
        value_clean = value.strip()
        val_key = value_clean.lower()

        if category_clean not in prefs:
            prefs[category_clean] = {}

        category_data = prefs[category_clean]
        now_str = datetime.now().isoformat()

        if val_key not in category_data:
            # First time observing this preference
            category_data[val_key] = {
                "value": value_clean,
                "count": 1,
                "confidence": 0.5, # Initial confidence
                "created_at": now_str,
                "last_updated": now_str,
                "last_accessed": now_str
            }
            from brain.learning_engine import LearningTelemetry
            LearningTelemetry.log(f"[PREFERENCE DETECTED] Category '{category_clean}': '{value_clean}' (first time)")
        else:
            # Repeated preference: increment count and increase confidence
            item = category_data[val_key]
            item["count"] += 1
            # Confidence grows logarithmically or linearly up to a cap of 1.0
            new_conf = min(1.0, item.get("confidence", 0.5) + weight)
            item["confidence"] = new_conf
            item["last_updated"] = now_str
            item["last_accessed"] = now_str
            
            from brain.learning_engine import LearningTelemetry
            LearningTelemetry.log(f"[MEMORY UPDATED] Preference '{category_clean}' -> '{value_clean}': count={item['count']}, confidence={new_conf:.2f}")

        # Synchronize relationship graph
        try:
            from memory.relationship_manager import RelationshipManager
            pred_map = {
                "interests": "interested_in",
                "preferred_tools": "uses_tool",
                "preferred_workflow_patterns": "uses_workflow",
                "response_style": "prefers_style"
            }
            predicate = pred_map.get(category_clean, f"prefers_{category_clean}")
            # Use item confidence if it exists, else new_conf
            conf = item.get("confidence", 0.5) if val_key in category_data else 0.5
            RelationshipManager.add_relationship("User", predicate, value_clean, confidence=conf)
        except Exception:
            pass

        PreferenceManager.save_preferences(prefs)

    @staticmethod
    def get_active_preference(category: str) -> list:
        """
        Retrieves active preferences sorted by confidence.
        Updates their last accessed time.
        """
        prefs = PreferenceManager.load_preferences()
        category_clean = category.strip().lower()

        if category_clean not in prefs or not prefs[category_clean]:
            return []

        now_str = datetime.now().isoformat()
        items = list(prefs[category_clean].values())
        
        # Sort by confidence descending, then count descending
        items.sort(key=lambda x: (x.get("confidence", 0.0), x.get("count", 0)), reverse=True)

        # Update last accessed for matches
        for item in items:
            val_key = item["value"].lower()
            prefs[category_clean][val_key]["last_accessed"] = now_str
        
        PreferenceManager.save_preferences(prefs)
        return [item["value"] for item in items if item.get("confidence", 0.0) >= 0.4]

    @staticmethod
    def get_all_preferences() -> dict:
        """Returns simplified layout of all categories to lists of strings."""
        prefs = PreferenceManager.load_preferences()
        result = {}
        now_str = datetime.now().isoformat()
        
        for category in ["response_style", "interests", "preferred_tools", "preferred_workflow_patterns"]:
            if category in prefs and prefs[category]:
                items = list(prefs[category].values())
                items.sort(key=lambda x: (x.get("confidence", 0.0), x.get("count", 0)), reverse=True)
                
                # Filter active and update access time
                active_vals = []
                for item in items:
                    val_key = item["value"].lower()
                    prefs[category][val_key]["last_accessed"] = now_str
                    active_vals.append(f"{item['value']} (x{item['count']}, conf={item.get('confidence', 0.0):.2f})")
                result[category] = active_vals
            else:
                result[category] = []
                
        PreferenceManager.save_preferences(prefs)
        return result

    @staticmethod
    def adjust_confidence(category: str, value: str, amount: float):
        """Boosts or penalizes the confidence score of a specific preference."""
        if not category or not value:
            return

        prefs = PreferenceManager.load_preferences()
        category_clean = category.strip().lower()
        val_key = value.strip().lower()

        if category_clean in prefs and val_key in prefs[category_clean]:
            item = prefs[category_clean][val_key]
            old_conf = item.get("confidence", 0.5)
            new_conf = round(min(1.0, max(0.0, old_conf + amount)), 2)
            item["confidence"] = new_conf
            item["last_updated"] = datetime.now().isoformat()
            
            from brain.learning_engine import LearningTelemetry
            LearningTelemetry.log(f"[MEMORY UPDATED] Preference '{category_clean}.{val_key}' confidence: {old_conf:.2f} -> {new_conf:.2f}")

            if new_conf < 0.4:
                LearningTelemetry.log(f"[MEMORY MAINTENANCE] Removing preference '{category_clean}.{val_key}' due to low confidence ({new_conf:.2f})")
                del prefs[category_clean][val_key]
                if not prefs[category_clean]:
                    del prefs[category_clean]

            PreferenceManager.save_preferences(prefs)
