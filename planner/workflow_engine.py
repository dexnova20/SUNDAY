# c:\Users\mshas\OneDrive\Desktop\SUNDAY\planner\workflow_engine.py
"""
Workflow Orchestration Engine for SUNDAY.
Executes multi-step plans, resolves parameters dynamically, checks safety controls,
and persists progress inside session.json for plan resumption.
Includes SAFE-mode human approval gates, plan confidence checks, and workflow persistence.
"""
import os
import re
import time
import logging
from datetime import datetime
from planner.execution_tracker import ExecutionTracker
from planner.task_manager import TaskManager
from execution.action_executor import ActionExecutor
from config.settings import BASE_DIR
from utils.file_utils import atomic_write_json

logger = logging.getLogger("PLANNER_ENGINE")

class WorkflowEngine:
    def __init__(self, session_manager):
        self.session_manager = session_manager
        self.executor = ActionExecutor()
        self.valid_intents = set(self.executor.tools.keys())
        self.valid_intents.add("general_query")
        self.outputs = {}  # step_id -> execution result string/dictionary

    def validate_plan(self, steps: list) -> bool:
        """
        Plan Validation Layer. Checks structure and tool matching parameters before execution.
        """
        if not steps or not isinstance(steps, list):
            logger.error("Plan Validation failed: Plan must be a non-empty list of steps.")
            return False
            
        seen_ids = set()
        for idx, step in enumerate(steps):
            if not isinstance(step, dict):
                logger.error(f"Plan Validation failed: Step index {idx} is not a dictionary.")
                return False
                
            step_id = step.get("step_id")
            if step_id is None or not isinstance(step_id, int) or step_id <= 0:
                logger.error(f"Plan Validation failed: Step index {idx} has invalid step_id '{step_id}'.")
                return False
            if step_id in seen_ids:
                logger.error(f"Plan Validation failed: Duplicate step_id '{step_id}' found.")
                return False
            seen_ids.add(step_id)
            
            description = step.get("description")
            if not description or not isinstance(description, str):
                logger.error(f"Plan Validation failed: Step {step_id} is missing description.")
                return False
                
            intent = step.get("intent")
            if not intent or intent not in self.valid_intents:
                logger.error(f"Plan Validation failed: Step {step_id} has invalid intent '{intent}'.")
                return False
                
            parameters = step.get("parameters")
            if parameters is not None and not isinstance(parameters, dict):
                logger.error(f"Plan Validation failed: Step {step_id} parameters must be a dictionary.")
                return False
                
        # Emit telemetry
        ExecutionTracker.log_plan_validated(len(steps))
        return True

    def contains_sensitive_actions(self, steps: list) -> bool:
        """Scans steps for intents flagged as highly sensitive."""
        sensitive_intents = {"system_shutdown", "system_restart", "system_sleep"}
        for step in steps:
            if step.get("intent") in sensitive_intents:
                return True
        return False

    def execute_plan(self, steps: list, start_index: int = 0, dry_run: bool = False, confidence: float = 1.0) -> bool:
        """
        Orchestrates sequential multi-step plan execution.
        Handles dry-runs, confidence checks, human approval, parameter propagation, and session saving.
        Records structured workflow outcomes for future learning.
        """
        planning_start = time.time()
        execution_start = None
        plan_success = False
        error_step_id = None
        error_message = ""
        
        # 1. Validation check
        if not self.validate_plan(steps):
            ExecutionTracker.log_planner("Plan validation failed. Aborting execution.")
            self._save_workflow_outcome(steps, confidence, False, None, "Plan validation failed", planning_start, None)
            return False

        # 2. Dry-Run Mode
        if dry_run:
            print("\n" + "="*50)
            print("         SUNDAY DRY-RUN PLAN SIMULATION")
            print("="*50)
            print(f"Confidence Score: {confidence:.2f}")
            for step in steps:
                print(f"Step {step['step_id']}: {step['description']}")
                print(f"  Intent: {step['intent']} | Params: {step.get('parameters', {})}")
            print("="*50 + "\n")
            return True

        # 3. Planner Confidence Score Validation (Approved Requirement)
        if confidence < 0.80:
            print(f"\n[PLANNER WARNING] Plan has a low confidence score: {confidence:.2f}.")
            confirm = input("Explicit approval is required before execution. Authorize this plan? [y/n]: ").strip().lower()
            if confirm != 'y':
                ExecutionTracker.log_planner("Plan aborted by user due to low confidence.")
                self._save_workflow_outcome(steps, confidence, False, None, "User rejected low confidence plan", planning_start, None)
                return False

        # 4. Sensitive Action Authorization Prompts
        if self.contains_sensitive_actions(steps):
            print("\n[PLANNER] [WARNING] This plan contains highly critical system command operations.")
            confirm = input("Are you sure you want to authorize and execute this plan? [y/n]: ").strip().lower()
            if confirm != 'y':
                ExecutionTracker.log_planner("Plan authorization denied by user. Aborting.")
                self._save_workflow_outcome(steps, confidence, False, None, "User denied sensitive action authorization", planning_start, None)
                return False

        # 5. Initialize task manager
        manager = TaskManager(steps, start_index)
        
        # Save plan initially inside session memory
        self.session_manager.save_plan(steps, start_index, "in_progress")
        
        total_steps = len(steps)
        execution_start = time.time()
        
        while manager.current_index < total_steps:
            step = manager.get_current_step()
            if not step:
                break
                
            step_id = step["step_id"]
            desc = step["description"]
            intent = step["intent"]
            
            # Save session progress before running
            self.session_manager.save_plan(steps, manager.current_index, "in_progress")
            
            # Print progressive headers
            ExecutionTracker.print_progress(manager.current_index + 1, total_steps, desc)
            
            # Parameter value propagation
            raw_params = step.get("parameters", {})
            resolved_params = self._resolve_parameters(raw_params)
            
            step["status"] = "in_progress"

            # 6. Human Approval Layer in SAFE Mode (Approved Requirement)
            sensitive_categories = {
                "click_control", "type_text", "type", "write", "write_text",
                "open_website", "search_web", "web_scrape",
                "system_shutdown", "system_restart", "system_sleep"
            }
            if self.session_manager.automation_mode == "safe" and intent in sensitive_categories:
                print(f"\n[SAFE MODE - HUMAN APPROVAL GATE] SUNDAY is about to execute:")
                print(f"  Step {step_id}: {desc}")
                print(f"  Action: {intent} | Parameters: {resolved_params}")
                confirm = input("Authorize this automation step? [y/n]: ").strip().lower()
                if confirm != 'y':
                    # Log failure and allow recovery skip/abort options
                    print("[SAFE MODE] Action execution denied by operator.")
                    action = manager.handle_failure("Human approval denied")
                    if action == "skip":
                        self.outputs[step_id] = "Step Skipped by Human."
                        continue
                    else:
                        self.session_manager.save_plan(steps, manager.current_index, "failed")
                        ExecutionTracker.log_planner("Plan aborted by operator during human approval gate.")
                        self._save_workflow_outcome(steps, confidence, False, step_id, "Human approval denied", planning_start, execution_start)
                        return False
            
            # Execute step intent
            success = False
            error_msg = ""
            result_val = ""
            
            try:
                if intent == "general_query":
                    # Query conversational LLM directly
                    from brain.brain import BrainModule
                    brain = BrainModule()
                    prompt = resolved_params.get("prompt", desc)
                    res = brain.process_chat(prompt)
                    result_val = res.get("reply_text", "Done.")
                    print(f"\n[SUNDAY]:\n{result_val}\n")
                    success = True
                else:
                    # Run central Tool registry automation
                    res = self.executor.execute(intent, resolved_params)
                    success = res.get("success", True)
                    error_msg = res.get("message", "Unknown execution error")
                    # Capture exact output data if available (e.g. scraper dictionary returns)
                    result_val = res.get("data", res.get("text", res.get("message", "Success.")))
                    if success:
                        if isinstance(result_val, dict):
                            print(f"\n[SUNDAY EXECUTION SUCCESS]: Extracted {len(result_val.get('text', ''))} characters from '{result_val.get('title', '')}'\n")
                        else:
                            print(f"\n[SUNDAY EXECUTION SUCCESS]: {result_val}\n")
            except Exception as ex:
                success = False
                error_msg = str(ex)

            if success:
                # Save step output for parameter propagation (supports raw dictionaries/strings)
                self.outputs[step_id] = result_val
                manager.mark_completed()
            else:
                # Failure recovery loop
                action = manager.handle_failure(error_msg)
                
                if action == "retry":
                    continue
                elif action == "skip":
                    self.outputs[step_id] = "Step Skipped."
                    continue
                elif action == "abort":
                    self.session_manager.save_plan(steps, manager.current_index, "failed")
                    ExecutionTracker.log_planner("Plan execution ceased due to abort action.")
                    self._save_workflow_outcome(steps, confidence, False, step_id, error_msg, planning_start, execution_start)
                    return False

        # 7. Save structured workflow outcome artifact
        plan_success = True
        self._save_workflow_outcome(steps, confidence, True, None, "", planning_start, execution_start)

        # Plan fully completed, clean session files
        self.session_manager.clear_plan()
        ExecutionTracker.log_planner("All workflow steps completed successfully. Session cleared.")
        return True

    def _detect_swap_pressure(self) -> bool:
        """Checks if system memory is under swap pressure (>85% load)."""
        try:
            from models.model_registry import get_system_ram_info
            ram = get_system_ram_info()
            return ram.get("memory_load", 50) > 85
        except Exception:
            return False

    def _save_workflow_outcome(self, steps: list, confidence: float, success: bool,
                                error_step: int = None, error_message: str = "",
                                planning_start: float = None, execution_start: float = None):
        """
        Creates and saves a structured workflow artifact with a complete outcome node
        for future workflow learning and reinforcement analysis.
        """
        try:
            workflow_dir = os.path.join(BASE_DIR, "data", "workflows")
            os.makedirs(workflow_dir, exist_ok=True)
            filename = f"workflow_{int(time.time())}.json"
            filepath = os.path.join(workflow_dir, filename)
            
            now = time.time()
            planning_duration = (execution_start - planning_start) if (planning_start and execution_start) else (now - planning_start) if planning_start else 0.0
            execution_duration = (now - execution_start) if execution_start else 0.0
            
            # Format outputs safely (convert non-serializable elements to string)
            serializable_outputs = {}
            for sid, out in self.outputs.items():
                if isinstance(out, (dict, list, str, int, float, bool)) or out is None:
                    serializable_outputs[sid] = out
                else:
                    serializable_outputs[sid] = str(out)

            workflow_data = {
                "timestamp": datetime.now().isoformat(),
                "confidence_score": confidence,
                "automation_mode": self.session_manager.automation_mode,
                "steps": steps,
                "outputs": serializable_outputs,
                "outcome": {
                    "status": "success" if success else "failed",
                    "error_step": error_step,
                    "error_message": error_message,
                    "planning_duration_sec": round(planning_duration, 3),
                    "execution_duration_sec": round(execution_duration, 3),
                    "steps_count": len(steps),
                    "swap_occurred": self._detect_swap_pressure()
                }
            }
            
            status_tag = "[PLAN COMPLETED]" if success else "[PLAN FAILED]"
            print(f"{status_tag} Outcome: {workflow_data['outcome']['status']} | Steps: {len(steps)} | "
                  f"Planning: {planning_duration:.2f}s | Execution: {execution_duration:.2f}s")
            
            atomic_write_json(filepath, workflow_data)
            print(f"[AUTOMATION] Workflow artifact saved successfully at: {filepath}")
        except Exception as w_e:
            logger.error(f"Failed to save workflow artifact: {w_e}")

    def _resolve_parameters(self, parameters: dict) -> dict:
        """
        Replaces {output_step_X} or {output_step_X.subkey} placeholders dynamically
        with preceding execution output values.
        """
        if not parameters:
            return {}
            
        resolved = {}
        for k, v in parameters.items():
            if isinstance(v, str):
                # Regex search to capture {output_step_X} or {output_step_X.subkey}
                matches = re.findall(r"\{output_step_(\d+)(?:\.([a-zA-Z_0-9]+))?\}", v)
                for step_id_str, subkey in matches:
                    step_id = int(step_id_str)
                    placeholder = f"{{output_step_{step_id_str}.{subkey}}}" if subkey else f"{{output_step_{step_id_str}}}"
                    
                    if step_id in self.outputs:
                        output_val = self.outputs[step_id]
                        
                        if subkey:
                            # Resolve nested subkey from dictionary return
                            if isinstance(output_val, dict):
                                resolved_val = output_val.get(subkey, "")
                            else:
                                resolved_val = ""
                        else:
                            # Resolve full text/message output
                            if isinstance(output_val, dict):
                                resolved_val = output_val.get("text", output_val.get("message", str(output_val)))
                            else:
                                resolved_val = str(output_val)
                                
                        v = v.replace(placeholder, str(resolved_val))
            resolved[k] = v
        return resolved
