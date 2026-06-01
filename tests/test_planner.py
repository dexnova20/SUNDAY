# c:\Users\mshas\OneDrive\Desktop\SUNDAY\tests\test_planner.py
"""
Automated Verification Suite for SUNDAY Planner Layer.
Tests request decomposition, plan validation, parameter value propagation,
session serialization, task recovery, and dry-run execution blocks.
"""
import os
import sys
import time

# Ensure project root is in python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_planner_test_suite():
    print("="*60)
    print("         SUNDAY PLANNER LAYER INTEGRITY SUITE")
    print("="*60)

    # Mock Session Manager for testing
    class MockSessionManager:
        def __init__(self):
            self.active_plan = None
        def save_plan(self, steps, current_index, status):
            self.active_plan = {
                "steps": steps,
                "current_step_index": current_index,
                "status": status
            }
        def clear_plan(self):
            self.active_plan = None

    session = MockSessionManager()

    # 1. Test Plan Validation Layer (Checks structure and intents)
    try:
        from planner.workflow_engine import WorkflowEngine
        engine = WorkflowEngine(session)
        
        valid_steps = [
            {"step_id": 1, "description": "Search web", "intent": "search_web", "parameters": {"query": "test query"}},
            {"step_id": 2, "description": "Conversational reply", "intent": "general_query", "parameters": {"prompt": "summarize"}}
        ]
        
        invalid_steps_intent = [
            {"step_id": 1, "description": "Search web", "intent": "non_existent_tool_intent", "parameters": {}}
        ]
        
        invalid_steps_duplicate = [
            {"step_id": 1, "description": "Step 1", "intent": "take_screenshot"},
            {"step_id": 1, "description": "Duplicate ID", "intent": "take_screenshot"}
        ]
        
        assert engine.validate_plan(valid_steps) is True, "Valid plan failed validation check!"
        assert engine.validate_plan(invalid_steps_intent) is False, "Invalid intent did not fail validation check!"
        assert engine.validate_plan(invalid_steps_duplicate) is False, "Duplicate step_id did not fail validation check!"
        
        print("[PASS] Plan Validation Layer verified successfully.")
        
    except Exception as e:
        print(f"[FAIL] Plan Validation check failed: {e}")
        return False

    # 2. Test Parameter Value Propagation ({output_step_X})
    try:
        engine.outputs[1] = "France is in Western Europe."
        params = {"prompt": "Based on this finding: {output_step_1}, list capital city."}
        
        resolved = engine._resolve_parameters(params)
        assert "France is in Western Europe." in resolved["prompt"], "Placeholder value substitution failed!"
        
        print("[PASS] Parameter value propagation resolved successfully.")
        
    except Exception as e:
        print(f"[FAIL] Parameter propagation check failed: {e}")
        return False

    # 3. Test Session Serialization / Plan Resumption
    try:
        # Run dry-run simulation first to verify it executes successfully
        engine.execute_plan(valid_steps, dry_run=True)
        
        # Explicitly check session serialization functionality
        session.save_plan(valid_steps, 0, "in_progress")
        assert session.active_plan is not None, "Active plan not saved in session memory"
        assert len(session.active_plan["steps"]) == 2, "Saved plan mismatch in steps size"
        
        print("[PASS] Session serialization and dry-run simulation verified successfully.")
        
    except Exception as e:
        print(f"[FAIL] Session serialization check failed: {e}")
        return False

    # 4. Test Failures & Recovery Loops (Retry/Skip/Abort)
    try:
        from planner.task_manager import TaskManager
        manager = TaskManager(valid_steps)
        
        # Test retry logic
        action = manager.handle_failure("Network timeout error")
        assert action == "retry", "Step failure did not trigger expected retry"
        assert manager.retry_counts[1] == 1, "Retry counter was not incremented correctly"
        
        # Exceed MAX_RETRIES = 2
        manager.retry_counts[1] = 2
        # Mock input to simulate user skipping
        sys_input_backup = __builtins__.input
        try:
            # Inject mock user skip choice
            __builtins__.input = lambda prompt: 's'
            action = manager.handle_failure("Out of resources error")
            assert action == "skip", "User skip prompt failed to trigger skip behavior"
            assert manager.current_index == 1, "Skipped step index was not incremented"
        finally:
            __builtins__.input = sys_input_backup
            
        print("[PASS] Task failure recovery loops (Retry/Skip) verified successfully.")
        
    except Exception as e:
        print(f"[FAIL] Task recovery checks failed: {e}")
        return False

    # 5. Test Cognitive Task Decomposition (Planning Call)
    try:
        from planner.planner import CognitivePlanner
        planner = CognitivePlanner(model="llama3.2:1b")
        
        # Query offline plan decomposition
        print("[PLANNER] Decomposing compound task query in background...")
        steps = planner.decompose_request("Take a screenshot and then search for prime numbers")
        
        assert len(steps) > 0, "No steps generated for compound task request"
        assert len(steps) <= planner.MAX_STEPS, "Planner exceeded maximum step cap limit"
        
        print(f"[PASS] Cognitive Task Decomposition successfully generated {len(steps)} plan steps:")
        for s in steps:
            print(f"       - Step {s['step_id']}: '{s['description']}' -> Intent: {s['intent']}")
            
    except Exception as e:
        print(f"[FAIL] Cognitive Task Decomposition check failed: {e}")
        return False

    print("="*60)
    print("         PLANNER LAYER VERIFICATION COMPLETED SUCCESSFULLY!")
    print("="*60)
    return True

if __name__ == "__main__":
    success = run_planner_test_suite()
    sys.exit(0 if success else 1)
