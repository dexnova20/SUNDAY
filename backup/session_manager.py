# c:\Users\mshas\OneDrive\Desktop\SUNDAY\session_manager.py
"""
Session Manager for SUNDAY (Text-First Rebuild).
Saves, loads, and manages project context, active goals, open tasks, recent commands,
and last actions inside a persistent .sunday_session.json database.
"""
import os
import json
from datetime import datetime

class SessionManager:
    def __init__(self):
        self.file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".sunday_session.json")
        self.current_project = ""
        self.active_goal = ""
        self.open_tasks = []
        self.recent_context = []
        self.last_action = ""
        self.last_session_time = ""

    def load_session(self) -> dict:
        """
        Loads the session state from .sunday_session.json.
        Initializes default values if the file is missing or corrupted.
        """
        state = {
            "current_project": "",
            "active_goal": "",
            "open_tasks": [],
            "recent_context": [],
            "last_action": "",
            "last_session_time": ""
        }
        
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    if isinstance(loaded, dict):
                        state.update(loaded)
            except Exception as e:
                # Silently catch and use defaults on corrupted JSON
                pass
                
        # Bind loaded values to self
        self.current_project = state.get("current_project", "")
        self.active_goal = state.get("active_goal", "")
        self.open_tasks = state.get("open_tasks", [])
        self.recent_context = state.get("recent_context", [])
        self.last_action = state.get("last_action", "")
        
        # Update last session time on load to current time
        self.last_session_time = datetime.now().isoformat()
        self.save_session()
        
        return state

    def save_session(self):
        """Atomically saves the current session state to .sunday_session.json."""
        state = {
            "current_project": self.current_project,
            "active_goal": self.active_goal,
            "open_tasks": self.open_tasks,
            "recent_context": self.recent_context,
            "last_action": self.last_action,
            "last_session_time": self.last_session_time
        }
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=4)
        except Exception:
            pass

    def set_project(self, name: str):
        """Updates the active project and persists change."""
        self.current_project = name.strip()
        self.save_session()

    def set_goal(self, desc: str):
        """Updates the active goal and persists change."""
        self.active_goal = desc.strip()
        self.save_session()

    def add_task(self, task: str):
        """Appends a new task to the task list and persists change."""
        if task.strip():
            self.open_tasks.append(task.strip())
            self.save_session()

    def complete_task(self, query: str) -> str:
        """
        Fuzzy matches and removes/resolves a task by case-insensitive substring match.
        Returns the exact task name removed, or None if no match found.
        """
        if not query or not self.open_tasks:
            return None
            
        query_lower = query.strip().lower()
        
        # 1. Look for exact match
        for idx, task in enumerate(self.open_tasks):
            if task.lower() == query_lower:
                removed = self.open_tasks.pop(idx)
                self.save_session()
                return removed
                
        # 2. Look for substring match
        for idx, task in enumerate(self.open_tasks):
            if query_lower in task.lower():
                removed = self.open_tasks.pop(idx)
                self.save_session()
                return removed
                
        return None

    def add_context(self, cmd_text: str):
        """Appends command to the rolling context logs, capped to the last 4 commands."""
        if cmd_text.strip():
            self.recent_context.append(cmd_text.strip())
            if len(self.recent_context) > 4:
                self.recent_context.pop(0)
            self.save_session()

    def set_last_action(self, action: str):
        """Updates the last executed action and persists change."""
        self.last_action = action.strip()
        self.save_session()

    def get_prompt_context(self) -> str:
        """
        Generates a concise status context string to inject into Brain prompts.
        Keeps token sizes extremely lightweight.
        """
        project = self.current_project if self.current_project else "None"
        goal = self.active_goal if self.active_goal else "None"
        tasks = ", ".join(self.open_tasks) if self.open_tasks else "None"
        history = " -> ".join(self.recent_context) if self.recent_context else "None"
        
        return f"[PROJECT: {project}] [GOAL: {goal}] [ACTIVE TASKS: {tasks}] [RECENT HISTORY: {history}]"
