# c:\Users\mshas\OneDrive\Desktop\SUNDAY\memory\session_manager.py
"""
Session Manager for SUNDAY (Text-First Rebuild).
Saves, loads, and manages project context, active goals, open tasks, recent commands,
and last actions inside a persistent session.json database.
"""
from config.settings import SESSION_PATH
from utils.file_utils import load_json, atomic_write_json
from utils.helpers import get_iso_timestamp

class SessionManager:
    def __init__(self):
        self.file_path = SESSION_PATH
        self.current_project = ""
        self.active_goal = ""
        self.open_tasks = []
        self.recent_context = []
        self.last_action = ""
        self.last_session_time = ""
        self.active_plan = None
        self.automation_mode = "safe"
        self.last_memory_accessed = None

    def load_session(self) -> dict:
        """
        Loads the session state from session.json.
        Initializes default values if the file is missing or corrupted.
        """
        default_state = {
            "current_project": "",
            "active_goal": "",
            "open_tasks": [],
            "recent_context": [],
            "last_action": "",
            "last_session_time": "",
            "active_plan": None,
            "automation_mode": "safe",
            "log_level": 0
        }
        
        # Load JSON database safely via file_utils
        state = load_json(self.file_path, dict)
        if not isinstance(state, dict):
            state = default_state
        else:
            # Update default state with loaded parameters
            merged = default_state.copy()
            merged.update(state)
            state = merged
                
        # Bind loaded values to self
        self.current_project = state.get("current_project", "")
        self.active_goal = state.get("active_goal", "")
        self.open_tasks = state.get("open_tasks", [])
        self.recent_context = state.get("recent_context", [])
        self.last_action = state.get("last_action", "")
        self.active_plan = state.get("active_plan", None)
        self.automation_mode = state.get("automation_mode", "safe")
        self.log_level = state.get("log_level", 0)
        self.last_memory_accessed = state.get("last_memory_accessed", None)
        
        # Update last session time on load to current time
        self.last_session_time = get_iso_timestamp()
        self.save_session()
        
        return state

    def save_session(self):
        """Atomically saves the current session state to session.json."""
        state = {
            "current_project": self.current_project,
            "active_goal": self.active_goal,
            "open_tasks": self.open_tasks,
            "recent_context": self.recent_context,
            "last_action": self.last_action,
            "last_session_time": self.last_session_time,
            "active_plan": self.active_plan,
            "automation_mode": self.automation_mode,
            "log_level": self.log_level,
            "last_memory_accessed": self.last_memory_accessed
        }
        # Safely execute atomic JSON dump
        atomic_write_json(self.file_path, state)

    def set_automation_mode(self, mode: str) -> bool:
        """Updates the active automation execution mode (safe/auto)."""
        mode_clean = mode.strip().lower()
        if mode_clean in ["safe", "auto"]:
            self.automation_mode = mode_clean
            self.save_session()
            return True
        return False

    def save_plan(self, steps: list, current_index: int, status: str):
        """Persists the active planner state dynamically into session.json."""
        self.active_plan = {
            "steps": steps,
            "current_step_index": current_index,
            "status": status
        }
        self.save_session()

    def clear_plan(self):
        """Clears the active planner state from session.json."""
        self.active_plan = None
        self.save_session()

    def set_project(self, name: str):
        """Updates the active project and persists change."""
        self.current_project = name.strip()
        self.save_session()
        # Invalidate Response Cache dynamically (Phase 8)
        try:
            from brain.brain import ResponseCache
            ResponseCache.invalidate()
        except ImportError:
            pass

    def set_goal(self, desc: str):
        """Updates the active goal and persists change."""
        self.active_goal = desc.strip()
        self.save_session()
        try:
            from brain.brain import ResponseCache
            ResponseCache.invalidate()
        except ImportError:
            pass

    def add_task(self, task: str):
        """Appends a new task to the task list and persists change."""
        if task.strip():
            self.open_tasks.append(task.strip())
            self.save_session()
            try:
                from brain.brain import ResponseCache
                ResponseCache.invalidate()
            except ImportError:
                pass

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
                try:
                    from brain.brain import ResponseCache
                    ResponseCache.invalidate()
                except ImportError:
                    pass
                return removed
                
        # 2. Look for substring match
        for idx, task in enumerate(self.open_tasks):
            if query_lower in task.lower():
                removed = self.open_tasks.pop(idx)
                self.save_session()
                try:
                    from brain.brain import ResponseCache
                    ResponseCache.invalidate()
                except ImportError:
                    pass
                return removed
                
        return None

    def add_context(self, cmd_text: str):
        """Appends command to the rolling context logs, capped to a maximum of 20 entries."""
        if cmd_text.strip():
            self.recent_context.append(cmd_text.strip())
            if len(self.recent_context) > 20:
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

    def set_last_memory_accessed(self, memory_ref: dict):
        """Updates and persists the last accessed cognitive memory reference."""
        self.last_memory_accessed = memory_ref
        self.save_session()
