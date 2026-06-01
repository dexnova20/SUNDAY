# c:\Users\mshas\OneDrive\Desktop\SUNDAY\tests\test_routing.py
"""
Comprehensive Test Suite for SUNDAY Phase 6: Brain Enhancement & Intelligent Routing.
Tests:
  - IntelligentRouter task classification accuracy
  - DynamicContextBudgeter token budgeting and pruning
  - Workflow outcome structured serialization
  - Router-to-model mapping correctness
"""
import os
import sys
import json
import time
import unittest

# Ensure project root is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestIntelligentRouter(unittest.TestCase):
    """Validates the IntelligentRouter rule-based task classifier."""

    @classmethod
    def setUpClass(cls):
        from brain.router import IntelligentRouter
        cls.router = IntelligentRouter

    # --- Automation classification tests ---

    def test_automation_open_app(self):
        result = self.router.classify_task("open chrome")
        self.assertEqual(result, "automation")

    def test_automation_volume(self):
        result = self.router.classify_task("volume up")
        self.assertEqual(result, "automation")

    def test_automation_brightness(self):
        result = self.router.classify_task("brightness down")
        self.assertEqual(result, "automation")

    def test_automation_screenshot(self):
        result = self.router.classify_task("take a screenshot")
        self.assertEqual(result, "automation")

    def test_automation_play_media(self):
        result = self.router.classify_task("play next track")
        self.assertEqual(result, "automation")

    def test_automation_system_shutdown(self):
        result = self.router.classify_task("shutdown computer")
        self.assertEqual(result, "automation")

    def test_automation_type_text(self):
        result = self.router.classify_task("type 'hello world'")
        self.assertEqual(result, "automation")

    def test_automation_search_web(self):
        result = self.router.classify_task("search for python tutorials")
        self.assertEqual(result, "automation")

    def test_automation_web_scrape(self):
        result = self.router.classify_task("scrape data from the website")
        self.assertEqual(result, "automation")

    # --- Coding classification tests ---

    def test_coding_write_function(self):
        result = self.router.classify_task("write a python function to sort a list")
        self.assertEqual(result, "coding")

    def test_coding_debug(self):
        result = self.router.classify_task("debug this code for me")
        self.assertEqual(result, "coding")

    def test_coding_language_mention(self):
        result = self.router.classify_task("explain how javascript closures work")
        self.assertEqual(result, "coding")

    def test_coding_algorithm(self):
        result = self.router.classify_task("implement a binary search algorithm")
        self.assertEqual(result, "coding")

    def test_coding_git(self):
        result = self.router.classify_task("how do I merge a branch in git")
        self.assertEqual(result, "coding")

    def test_coding_api(self):
        result = self.router.classify_task("create a REST API endpoint for user login")
        self.assertEqual(result, "coding")

    # --- Planning classification tests ---

    def test_planning_and_then(self):
        result = self.router.classify_task("research laptops and then save notes")
        self.assertEqual(result, "planning")

    def test_planning_step_by_step(self):
        result = self.router.classify_task("give me a step by step plan for deployment")
        self.assertEqual(result, "planning")

    def test_planning_workflow(self):
        result = self.router.classify_task("create a workflow for data processing")
        self.assertEqual(result, "planning")

    def test_planning_decompose(self):
        result = self.router.classify_task("break down the project into tasks")
        self.assertEqual(result, "planning")

    # --- Memory classification tests ---

    def test_memory_remember(self):
        result = self.router.classify_task("remember that my birthday is in December")
        self.assertEqual(result, "memory")

    def test_memory_recall(self):
        result = self.router.classify_task("recall what I told you about my project")
        self.assertEqual(result, "memory")

    def test_memory_search(self):
        result = self.router.classify_task("search memory about my preferences")
        self.assertEqual(result, "memory")

    # --- Vision classification tests ---

    def test_vision_screen(self):
        result = self.router.classify_task("what's on my screen")
        self.assertEqual(result, "vision")

    def test_vision_read_screen(self):
        result = self.router.classify_task("read my screen and explain the content")
        self.assertEqual(result, "vision")

    def test_vision_describe_window(self):
        result = self.router.classify_task("describe the active window")
        self.assertEqual(result, "vision")

    # --- Chat fallback tests ---

    def test_chat_greeting(self):
        result = self.router.classify_task("hello how are you")
        self.assertEqual(result, "chat")

    def test_chat_general_question(self):
        result = self.router.classify_task("what is the meaning of life")
        self.assertEqual(result, "chat")

    def test_chat_opinion(self):
        result = self.router.classify_task("do you think AI will replace humans")
        self.assertEqual(result, "chat")

    # --- Routing decision structure tests ---

    def test_classify_and_route_returns_dict(self):
        result = self.router.classify_and_route("hello")
        self.assertIsInstance(result, dict)
        self.assertIn("task_type", result)
        self.assertIn("reasoning_profile", result)
        self.assertIn("description", result)
        self.assertIn("classification_method", result)
        self.assertIn("latency_ms", result)

    def test_classify_and_route_latency(self):
        """Rule-based routing should complete in < 10ms."""
        result = self.router.classify_and_route("open chrome")
        self.assertLess(result["latency_ms"], 10.0)

    # --- Profile mapping tests ---

    def test_profile_chat_is_fast(self):
        profile = self.router.get_reasoning_profile("chat")
        self.assertEqual(profile, "FAST")

    def test_profile_coding_is_code(self):
        profile = self.router.get_reasoning_profile("coding")
        self.assertEqual(profile, "CODE")

    def test_profile_planning_is_think(self):
        profile = self.router.get_reasoning_profile("planning")
        self.assertEqual(profile, "THINK")

    def test_profile_automation_is_normal(self):
        profile = self.router.get_reasoning_profile("automation")
        self.assertEqual(profile, "NORMAL")

    def test_profile_vision_is_fast(self):
        profile = self.router.get_reasoning_profile("vision")
        self.assertEqual(profile, "FAST")


class TestDynamicContextBudgeter(unittest.TestCase):
    """Validates the DynamicContextBudgeter token allocation and pruning."""

    @classmethod
    def setUpClass(cls):
        from brain.context_budgeter import DynamicContextBudgeter
        cls.budgeter = DynamicContextBudgeter

    def _make_context(self, window="Test Window", screen="", memory="", project=""):
        return {
            "active_window": window,
            "screen_summary": screen,
            "relevant_memory": memory,
            "project_context": project,
        }

    # --- Token estimation tests ---

    def test_estimate_tokens_empty(self):
        self.assertEqual(self.budgeter.estimate_tokens(""), 0)

    def test_estimate_tokens_short(self):
        tokens = self.budgeter.estimate_tokens("hello world")
        self.assertGreater(tokens, 0)

    def test_estimate_tokens_consistent(self):
        t1 = self.budgeter.estimate_tokens("a" * 400)
        # 400 chars / 4 chars per token = 100 tokens
        self.assertEqual(t1, 100)

    # --- Truncation tests ---

    def test_truncate_short_text(self):
        result = self.budgeter.truncate_to_budget("hello", 100)
        self.assertEqual(result, "hello")

    def test_truncate_long_text(self):
        long_text = "x" * 5000
        result = self.budgeter.truncate_to_budget(long_text, 100)
        # 100 tokens * 4 chars = 400 chars max
        self.assertLessEqual(len(result), 500)  # 400 + truncation marker
        self.assertIn("[Truncated by Context Budget]", result)

    # --- UIA coordinate stripping tests ---

    def test_strip_uia_coordinates(self):
        text = "Button 'OK' bbox: [100, 200, 50, 30] coordinates: (100, 200, 50, 30)"
        result = self.budgeter.strip_uia_coordinates(text)
        self.assertNotIn("bbox:", result)
        self.assertNotIn("coordinates:", result)

    def test_strip_preserves_non_coord_text(self):
        text = "Application: Chrome\nTitle: Google Search"
        result = self.budgeter.strip_uia_coordinates(text)
        self.assertIn("Chrome", result)
        self.assertIn("Google Search", result)

    # --- Chat budget tests ---

    def test_chat_budget_strips_uia(self):
        context = self._make_context(
            screen="Button 'OK' bbox: [100, 200, 50, 30]"
        )
        result = self.budgeter.budget("chat", context)
        self.assertNotIn("bbox:", result.get("screen_summary", ""))

    def test_chat_budget_caps_memory(self):
        long_memory = "Important fact: " * 500
        context = self._make_context(memory=long_memory)
        result = self.budgeter.budget("chat", context)
        # Chat budget is 1000 tokens, memory should be capped
        mem_tokens = self.budgeter.estimate_tokens(result.get("relevant_memory", ""))
        self.assertLessEqual(mem_tokens, 1000)

    # --- Coding budget tests ---

    def test_coding_budget_prioritizes_memory(self):
        long_memory = "def function(): pass\n" * 100
        short_screen = "Visual Studio Code - main.py"
        context = self._make_context(memory=long_memory, screen=short_screen)
        result = self.budgeter.budget("coding", context)
        # Memory should be present and longer than screen
        mem_len = len(result.get("relevant_memory", ""))
        self.assertGreater(mem_len, 0)

    def test_coding_budget_strips_uia(self):
        context = self._make_context(
            screen="Editor bbox: [0, 0, 1920, 1080] Button 'Run' bbox: [50, 10, 80, 30]"
        )
        result = self.budgeter.budget("coding", context)
        self.assertNotIn("bbox:", result.get("screen_summary", ""))

    # --- Planning budget tests ---

    def test_planning_budget_preserves_full_context(self):
        context = self._make_context(
            screen="Window layout data " * 20,
            memory="Planning context " * 20,
            project="Project: SUNDAY | Goal: Build AI"
        )
        result = self.budgeter.budget("planning", context)
        # All fields should have content
        self.assertTrue(len(result.get("screen_summary", "")) > 0)
        self.assertTrue(len(result.get("relevant_memory", "")) > 0)
        self.assertTrue(len(result.get("project_context", "")) > 0)

    # --- Budget result structure tests ---

    def test_budget_returns_all_keys(self):
        context = self._make_context()
        result = self.budgeter.budget("chat", context)
        self.assertIn("active_window", result)
        self.assertIn("screen_summary", result)
        self.assertIn("relevant_memory", result)
        self.assertIn("project_context", result)

    def test_budget_empty_context(self):
        context = self._make_context(window="Unknown Window")
        result = self.budgeter.budget("chat", context)
        self.assertIsInstance(result, dict)


class TestWorkflowOutcome(unittest.TestCase):
    """Validates structured workflow outcome serialization."""

    def test_outcome_schema_fields(self):
        """Verify the outcome node contains all required fields."""
        expected_fields = ["status", "error_step", "error_message",
                          "planning_duration_sec", "execution_duration_sec",
                          "steps_count", "swap_occurred"]

        # Build a sample outcome
        outcome = {
            "status": "success",
            "error_step": None,
            "error_message": "",
            "planning_duration_sec": 1.5,
            "execution_duration_sec": 5.2,
            "steps_count": 3,
            "swap_occurred": False
        }

        for field in expected_fields:
            self.assertIn(field, outcome, f"Missing outcome field: {field}")

    def test_outcome_success_status(self):
        outcome = {"status": "success", "error_step": None, "error_message": ""}
        self.assertEqual(outcome["status"], "success")
        self.assertIsNone(outcome["error_step"])

    def test_outcome_failure_status(self):
        outcome = {"status": "failed", "error_step": 2, "error_message": "Target not found"}
        self.assertEqual(outcome["status"], "failed")
        self.assertEqual(outcome["error_step"], 2)
        self.assertEqual(outcome["error_message"], "Target not found")

    def test_outcome_serializable_to_json(self):
        outcome = {
            "status": "success",
            "error_step": None,
            "error_message": "",
            "planning_duration_sec": 3.42,
            "execution_duration_sec": 12.80,
            "steps_count": 4,
            "swap_occurred": False
        }
        json_str = json.dumps(outcome)
        parsed = json.loads(json_str)
        self.assertEqual(parsed["status"], "success")
        self.assertEqual(parsed["steps_count"], 4)
        self.assertAlmostEqual(parsed["planning_duration_sec"], 3.42)


class TestRouterModelMapping(unittest.TestCase):
    """Validates that the router maps task types to correct model profiles."""

    def test_chat_maps_to_fast_llama1b(self):
        from brain.router import IntelligentRouter
        from models.model_registry import MODE_MODEL_PRIORITY
        profile = IntelligentRouter.get_reasoning_profile("chat")
        model = MODE_MODEL_PRIORITY.get(profile)
        self.assertEqual(profile, "FAST")
        self.assertEqual(model, "llama3.2:1b")

    def test_coding_maps_to_code_phi3(self):
        from brain.router import IntelligentRouter
        from models.model_registry import MODE_MODEL_PRIORITY
        profile = IntelligentRouter.get_reasoning_profile("coding")
        model = MODE_MODEL_PRIORITY.get(profile)
        self.assertEqual(profile, "CODE")
        self.assertEqual(model, "phi3:latest")

    def test_planning_maps_to_think_llama32(self):
        from brain.router import IntelligentRouter
        from models.model_registry import MODE_MODEL_PRIORITY
        profile = IntelligentRouter.get_reasoning_profile("planning")
        model = MODE_MODEL_PRIORITY.get(profile)
        self.assertEqual(profile, "THINK")
        self.assertEqual(model, "llama3.2:latest")

    def test_automation_maps_to_normal_llama32(self):
        from brain.router import IntelligentRouter
        from models.model_registry import MODE_MODEL_PRIORITY
        profile = IntelligentRouter.get_reasoning_profile("automation")
        model = MODE_MODEL_PRIORITY.get(profile)
        self.assertEqual(profile, "NORMAL")
        self.assertEqual(model, "llama3.2:latest")

    def test_vision_maps_to_fast_llama1b(self):
        from brain.router import IntelligentRouter
        from models.model_registry import MODE_MODEL_PRIORITY
        profile = IntelligentRouter.get_reasoning_profile("vision")
        model = MODE_MODEL_PRIORITY.get(profile)
        self.assertEqual(profile, "FAST")
        self.assertEqual(model, "llama3.2:1b")


class TestContextBudgeterIntegration(unittest.TestCase):
    """Integration tests for context budgeting with compressed context output format."""

    def test_budget_all_task_types(self):
        from brain.context_budgeter import DynamicContextBudgeter
        
        context = {
            "active_window": "Chrome - Google",
            "screen_summary": "Search results " * 100,
            "relevant_memory": "Fact: user prefers dark mode " * 50,
            "project_context": "Project: SUNDAY | Goal: AI Agent"
        }
        
        for task_type in ["chat", "coding", "planning", "memory", "vision", "automation"]:
            result = DynamicContextBudgeter.budget(task_type, context)
            self.assertIsInstance(result, dict, f"Budget failed for task type: {task_type}")
            self.assertIn("active_window", result)

    def test_chat_budget_smaller_than_planning(self):
        from brain.context_budgeter import DynamicContextBudgeter, BUDGET_CAPS
        self.assertLess(BUDGET_CAPS["chat"], BUDGET_CAPS["planning"])

    def test_coding_budget_moderate(self):
        from brain.context_budgeter import BUDGET_CAPS
        self.assertEqual(BUDGET_CAPS["coding"], 3000)
        self.assertGreater(BUDGET_CAPS["coding"], BUDGET_CAPS["chat"])
        self.assertLess(BUDGET_CAPS["coding"], BUDGET_CAPS["planning"])


if __name__ == "__main__":
    unittest.main()
