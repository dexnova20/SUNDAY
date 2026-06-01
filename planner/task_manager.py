# c:\Users\mshas\OneDrive\Desktop\SUNDAY\planner\task_manager.py
"""
Planner Task Manager for SUNDAY.
Manages active step queues, retries (capped to MAX_RETRIES = 2), and interactive
skip/retry/abort recovery systems.
"""
import logging
from planner.execution_tracker import ExecutionTracker

logger = logging.getLogger("PLANNER_TASK_MANAGER")

class TaskManager:
    MAX_RETRIES = 2

    def __init__(self, steps: list = None, current_index: int = 0):
        self.steps = steps or []
        self.current_index = current_index
        self.retry_counts = {}  # step_id -> integer retries count

    def get_current_step(self) -> dict:
        if 0 <= self.current_index < len(self.steps):
            return self.steps[self.current_index]
        return None

    def mark_completed(self):
        step = self.get_current_step()
        if step:
            step["status"] = "completed"
            logger.info(f"Step {step['step_id']} completed successfully.")
            self.current_index += 1

    def handle_failure(self, error_message: str) -> str:
        """
        Handles step failures. Tracks retries up to MAX_RETRIES = 2.
        If retry threshold exceeded, prompts user dynamically for action:
        - 'retry': Attempt execution again.
        - 'skip': Mark step as skipped and proceed.
        - 'abort': Cease execution and clean up.
        """
        step = self.get_current_step()
        if not step:
            return "abort"

        step["status"] = "failed"
        step_id = step["step_id"]
        
        # Log failure telemetry
        ExecutionTracker.log_plan_failed(step_id, error_message)
        
        # Increment and check retry counts
        retries = self.retry_counts.get(step_id, 0)
        if retries < self.MAX_RETRIES:
            self.retry_counts[step_id] = retries + 1
            ExecutionTracker.log_planner(f"Retrying step {step_id} (Attempt {retries + 1}/{self.MAX_RETRIES})...")
            step["status"] = "in_progress"
            return "retry"

        # Retry cap exceeded, prompt user for manual recovery (Phase 5 recovery)
        print(f"\n[PLANNER] [RECOVERY] Step {step_id} failed repeatedly after {self.MAX_RETRIES} retries.")
        print(f"Error: {error_message}")
        
        while True:
            choice = input("Would you like to (r)etry once more, (s)kip this step, or (a)bort the plan? [r/s/a]: ").strip().lower()
            if choice == 'r':
                ExecutionTracker.log_planner(f"User requested manual retry for step {step_id}.")
                step["status"] = "in_progress"
                return "retry"
            elif choice == 's':
                ExecutionTracker.log_planner(f"User skipped failed step {step_id}.")
                step["status"] = "skipped"
                self.current_index += 1
                return "skip"
            elif choice == 'a':
                ExecutionTracker.log_planner(f"User aborted the plan at step {step_id}.")
                step["status"] = "aborted"
                return "abort"
            print("Invalid input. Please choose 'r', 's', or 'a'.")
