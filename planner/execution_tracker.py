# c:\Users\mshas\OneDrive\Desktop\SUNDAY\planner\execution_tracker.py
"""
Telemetry & Progress Execution Tracker for SUNDAY Planner.
Emits prefix-based planner metrics and renders real-time CLI step progress indicators.
"""
import logging
from utils.logger import log_msg

logger = logging.getLogger("PLANNER_TRACKER")

class ExecutionTracker:
    @staticmethod
    def log_planner(msg: str):
        """Standard planner operational telemetry log."""
        log_msg("PLANNER", msg)
        print(f"[PLANNER] {msg}")

    @staticmethod
    def log_plan_generated(request: str, num_steps: int):
        """Logs initial plan generation success."""
        msg = f"Decomposed query '{request}' successfully into {num_steps} operational steps."
        log_msg("PLANNER", f"[PLAN GENERATED] {msg}")
        print(f"[PLAN GENERATED] {msg}")

    @staticmethod
    def log_plan_validated(num_steps: int):
        """Logs plan structural check verification."""
        msg = f"Passed Plan Validation Layer successfully. Decompressed {num_steps} steps."
        log_msg("PLANNER", f"[PLAN VALIDATED] {msg}")
        print(f"[PLAN VALIDATED] {msg}")

    @staticmethod
    def log_plan_resumed(index: int, total: int):
        """Logs plan state restoration."""
        msg = f"Restoring and resuming pending workflow from step {index+1}/{total}."
        log_msg("PLANNER", f"[PLAN RESUMED] {msg}")
        print(f"[PLAN RESUMED] {msg}")

    @staticmethod
    def log_plan_failed(step_id: int, error: str):
        """Logs plan step execution interruption."""
        msg = f"Step {step_id} failed: {error}"
        log_msg("PLANNER", f"[PLAN FAILED] {msg}")
        print(f"[PLAN FAILED] {msg}")

    @staticmethod
    def print_progress(current: int, total: int, description: str):
        """Renders highly visible CLI sequence progress step board."""
        print("\n" + "="*50)
        print(f"  [PLANNER PROGRESS]  Step {current}/{total}")
        print(f"  Action: {description}")
        print("="*50)
