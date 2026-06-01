# c:\Users\mshas\OneDrive\Desktop\SUNDAY\memory\goal_manager.py
"""
Goal Manager for SUNDAY.
Tracks long-term user objectives, categorizing them into active, completed,
and abandoned states. Includes confidence tracking and timestamps.
"""
import os
from datetime import datetime
from config.settings import BASE_DIR
from utils.file_utils import load_json, atomic_write_json

GOALS_PATH = os.path.join(BASE_DIR, "data", "goals.json")

class GoalManager:
    @staticmethod
    def load_goals() -> dict:
        """Loads goals from disk, establishing structure if empty."""
        data = load_json(GOALS_PATH, dict)
        if "active_goals" not in data:
            data["active_goals"] = []
        if "completed_goals" not in data:
            data["completed_goals"] = []
        if "abandoned_goals" not in data:
            data["abandoned_goals"] = []
        return data

    @staticmethod
    def save_goals(data: dict):
        """Atomically saves goals database to disk."""
        atomic_write_json(GOALS_PATH, data)

    @staticmethod
    def add_goal(goal_text: str, confidence: float = 0.90):
        """Adds a new active goal if it doesn't already exist."""
        if not goal_text:
            return

        goals = GoalManager.load_goals()
        goal_text_clean = goal_text.strip()
        
        # Check if already active
        for g in goals["active_goals"]:
            if g["goal"].lower() == goal_text_clean.lower():
                g["confidence"] = max(g.get("confidence", 0.5), confidence)
                g["last_updated"] = datetime.now().isoformat()
                g["last_accessed"] = datetime.now().isoformat()
                GoalManager.save_goals(goals)
                return

        now_str = datetime.now().isoformat()
        new_goal = {
            "goal": goal_text_clean,
            "confidence": confidence,
            "created_at": now_str,
            "last_updated": now_str,
            "last_accessed": now_str
        }
        
        goals["active_goals"].append(new_goal)
        GoalManager.save_goals(goals)

        # Synchronize relationship graph
        try:
            from memory.relationship_manager import RelationshipManager
            RelationshipManager.add_relationship("User", "works_on", goal_text_clean, confidence=confidence)
        except Exception:
            pass
        
        from brain.learning_engine import LearningTelemetry
        LearningTelemetry.log(f"[GOAL DETECTED] Goal: '{goal_text_clean}' (confidence={confidence:.2f})")

    @staticmethod
    def complete_goal(goal_text: str) -> bool:
        """Moves a goal from active_goals to completed_goals."""
        if not goal_text:
            return False

        goals = GoalManager.load_goals()
        goal_text_clean = goal_text.strip().lower()
        now_str = datetime.now().isoformat()
        
        found = None
        for g in goals["active_goals"]:
            if goal_text_clean in g["goal"].lower():
                found = g
                break
                
        if found:
            goals["active_goals"].remove(found)
            found["completed_at"] = now_str
            found["last_updated"] = now_str
            found["last_accessed"] = now_str
            goals["completed_goals"].append(found)
            GoalManager.save_goals(goals)
            
            from brain.learning_engine import LearningTelemetry
            LearningTelemetry.log(f"[MEMORY UPDATED] Goal completed: '{found['goal']}'")
            return True
            
        return False

    @staticmethod
    def abandon_goal(goal_text: str) -> bool:
        """Moves a goal from active_goals to abandoned_goals."""
        if not goal_text:
            return False

        goals = GoalManager.load_goals()
        goal_text_clean = goal_text.strip().lower()
        now_str = datetime.now().isoformat()
        
        found = None
        for g in goals["active_goals"]:
            if goal_text_clean in g["goal"].lower():
                found = g
                break
                
        if found:
            goals["active_goals"].remove(found)
            found["abandoned_at"] = now_str
            found["last_updated"] = now_str
            found["last_accessed"] = now_str
            goals["abandoned_goals"].append(found)
            GoalManager.save_goals(goals)
            
            from brain.learning_engine import LearningTelemetry
            LearningTelemetry.log(f"[MEMORY UPDATED] Goal abandoned: '{found['goal']}'")
            return True
            
        return False

    @staticmethod
    def get_active_goals() -> list:
        """Retrieves a list of active goal strings, updating access timestamps."""
        goals = GoalManager.load_goals()
        now_str = datetime.now().isoformat()
        active_list = []
        
        for g in goals["active_goals"]:
            g["last_accessed"] = now_str
            active_list.append(g["goal"])
            
        if active_list:
            GoalManager.save_goals(goals)
        return active_list

    @staticmethod
    def adjust_confidence(goal_text: str, amount: float):
        """Boosts or penalizes the confidence score of a specific active goal."""
        if not goal_text:
            return

        goals = GoalManager.load_goals()
        goal_text_clean = goal_text.strip().lower()
        goals_updated = False

        for g in list(goals.get("active_goals", [])):
            if goal_text_clean in g["goal"].lower():
                old_conf = g.get("confidence", 0.9)
                new_conf = round(min(1.0, max(0.0, old_conf + amount)), 2)
                g["confidence"] = new_conf
                g["last_updated"] = datetime.now().isoformat()
                goals_updated = True
                
                from brain.learning_engine import LearningTelemetry
                LearningTelemetry.log(f"[MEMORY UPDATED] Goal '{g['goal']}' confidence: {old_conf:.2f} -> {new_conf:.2f}")

                if new_conf < 0.4:
                    LearningTelemetry.log(f"[MEMORY MAINTENANCE] Goal abandoned due to low confidence ({new_conf:.2f}): '{g['goal']}'")
                    goals["active_goals"].remove(g)
                    g["abandoned_at"] = datetime.now().isoformat()
                    goals["abandoned_goals"].append(g)
                break

        if goals_updated:
            GoalManager.save_goals(goals)
