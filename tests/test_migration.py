# c:\Users\mshas\OneDrive\Desktop\SUNDAY\tests\test_migration.py
"""
Automated Restructuring Verification Tests.
Validates configurations, imports, session managers, memory APIs, and executor tool bindings.
"""
import os
import sys

# Ensure project root is in python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_test_suite():
    print("="*60)
    print("        SUNDAY STRUCTURAL MIGRATION VERIFICATION SUITE")
    print("="*60)
    
    # 1. Test Config Settings
    try:
        from config.settings import BASE_DIR, MEMORY_PATH, SESSION_PATH, LOG_PATH, SCREENSHOT_PATH, OLLAMA_URL
        print("[PASS] Centralized config.settings imported successfully.")
        print(f"       BASE_DIR: {BASE_DIR}")
        print(f"       MEMORY_PATH: {MEMORY_PATH}")
        print(f"       SESSION_PATH: {SESSION_PATH}")
        print(f"       LOG_PATH: {LOG_PATH}")
        print(f"       SCREENSHOT_PATH: {SCREENSHOT_PATH}")
        print(f"       OLLAMA_URL: {OLLAMA_URL}")
        
        assert os.path.isabs(MEMORY_PATH), "MEMORY_PATH must be absolute"
        assert os.path.isabs(SESSION_PATH), "SESSION_PATH must be absolute"
        assert os.path.isabs(LOG_PATH), "LOG_PATH must be absolute"
        assert os.path.isabs(SCREENSHOT_PATH), "SCREENSHOT_PATH must be absolute"
    except Exception as e:
        print(f"[FAIL] Config settings check failed: {e}")
        return False

    # 2. Test Session Persistence Manager
    try:
        from memory.session_manager import SessionManager
        session = SessionManager()
        state = session.load_session()
        print("[PASS] SessionManager instantiated and session.json loaded.")
        
        # Test updating project/goals
        session.set_project("Verification Test Project")
        session.set_goal("Verify refactoring integrity")
        assert session.current_project == "Verification Test Project"
        assert session.active_goal == "Verify refactoring integrity"
        
        # Test task list operations
        session.add_task("Unit test UIA context")
        session.add_task("Assert absolute path resolution")
        assert "Unit test UIA context" in session.open_tasks
        
        # Test fuzzy complete task
        removed = session.complete_task("UIA context")
        assert removed == "Unit test UIA context"
        assert "Unit test UIA context" not in session.open_tasks
        
        # Restore backup or original session data if needed
        session.set_project("SUNDAY Text-First Agent Rebuild")
        session.set_goal("Achieve full stability and modularity")
        session.open_tasks = ["Verify session manager functionality", "Upgrade active visual OCR scanner"]
        session.save_session()
        print("[PASS] SessionManager read/write/fuzzy-match flows verified successfully.")
    except Exception as e:
        print(f"[FAIL] SessionManager check failed: {e}")
        return False

    # 3. Test Memory APIs
    try:
        from memory.memory_manager import MemoryManager
        matches = MemoryManager.recall_knowledge("Introducing Yourself")
        print(f"[PASS] MemoryManager.recall_knowledge parsed memory database (found {len(matches)} matches).")
        for match in matches:
            print(f"       Match: [{match['topic']}] -> {match['content']}")
            
        search_matches = MemoryManager.search_knowledge("robotic")
        print(f"[PASS] MemoryManager.search_knowledge verified search matching (found {len(search_matches)} matches).")
    except Exception as e:
        print(f"[FAIL] MemoryManager check failed: {e}")
        return False

    # 4. Test Action Executor Tool Registry Bindings
    try:
        from execution.action_executor import ActionExecutor
        executor = ActionExecutor()
        print("[PASS] ActionExecutor instantiated and VisionSession bound successfully.")
        
        # Check tool bindings count
        assert len(executor.tools) >= 14, f"Expected at least 14 registered tools, got {len(executor.tools)}"
        print(f"[PASS] Centralized Tool Registry successfully binds {len(executor.tools)} operational automation tools:")
        for tool_name, tool_instance in executor.tools.items():
            print(f"       - '{tool_name}' -> {tool_instance.__class__.__name__}")
            
        # Test shortcut evaluation
        shortcut_screenshot = executor.evaluate_shortcut("take a screenshot")
        assert shortcut_screenshot["intent"] == "take_screenshot"
        
        shortcut_volume = executor.evaluate_shortcut("mute volume")
        assert shortcut_volume["intent"] == "volume_mute"
        
        shortcut_open = executor.evaluate_shortcut("open chrome")
        assert shortcut_open["intent"] == "open_app"
        assert shortcut_open["parameters"]["app_name"] == "chrome"
        
        print("[PASS] ActionExecutor rule-based shortcut bypass engine verified successfully.")
    except Exception as e:
        print(f"[FAIL] ActionExecutor check failed: {e}")
        return False

    print("="*60)
    print("        MIGRATION INTEGRITY INTEGRATION TEST PASSED!")
    print("="*60)
    return True

if __name__ == "__main__":
    success = run_test_suite()
    sys.exit(0 if success else 1)
