# c:\Users\mshas\OneDrive\Desktop\SUNDAY\memory\experience_store.py
"""
Experience Store for SUNDAY.
Tracks outcomes of workflow runs and actions to allow learning from experience.
"""
import os
from datetime import datetime
from config.settings import BASE_DIR
from utils.file_utils import load_json, atomic_write_json

EXPERIENCES_PATH = os.path.join(BASE_DIR, "data", "experiences.json")

class ExperienceStore:
    @staticmethod
    def load_experiences() -> list:
        """Loads experiences list from disk."""
        return load_json(EXPERIENCES_PATH, list)

    @staticmethod
    def save_experiences(data: list):
        """Atomically saves experiences list to disk."""
        atomic_write_json(EXPERIENCES_PATH, data)

    @staticmethod
    def add_experience(workflow: str, success: bool, confidence: float = 1.0):
        """Adds a new workflow execution record, capping history to prevent bloat."""
        if not workflow:
            return

        experiences = ExperienceStore.load_experiences()
        now_str = datetime.now().isoformat()

        new_exp = {
            "workflow": workflow.strip(),
            "success": success,
            "confidence": confidence,
            "created_at": now_str,
            "last_accessed": now_str
        }
        
        experiences.append(new_exp)
        
        # Keep only the last 100 entries to prevent memory database bloat
        experiences = experiences[-100:]
        ExperienceStore.save_experiences(experiences)

        # Experience-Driven Preference Adaptation
        try:
            from memory.preference_manager import PreferenceManager
            if success:
                PreferenceManager.add_preference("preferred_workflow_patterns", workflow.strip(), weight=0.1)
            else:
                PreferenceManager.adjust_confidence("preferred_workflow_patterns", workflow.strip(), -0.15)
        except Exception:
            pass

        from brain.learning_engine import LearningTelemetry
        LearningTelemetry.log(f"[MEMORY STORED] Experience workflow '{workflow.strip()}': success={success}, confidence={confidence:.2f}")
