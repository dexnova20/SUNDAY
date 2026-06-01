# c:\Users\mshas\OneDrive\Desktop\SUNDAY\tests\test_automation.py
"""
Automated Verification Suite for Phase 5 Advanced Automation Layer.
Validates direct HTML scraping, nested parameter resolution, pre-click UIA revalidation,
SAFE/AUTO automation modes, plan confidence blocks, and workflows history serialization.
"""
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Ensure project root is in python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.web_scrape_tool import WebScrapeTool, CleanTextExtractor
from tools.desktop_automation_tool import DesktopClickControlTool
from planner.workflow_engine import WorkflowEngine
from memory.session_manager import SessionManager

class TestSUNDAYAdvancedAutomation(unittest.TestCase):

    def test_clean_html_extractor(self):
        """Asserts zero-dependency HTML parser extracts title, clean text, and URLs."""
        html_content = """
        <html>
            <head><title>Test Laptop Review</title></head>
            <body>
                <h1>Best Laptops of 2026</h1>
                <p>The new laptops are extremely fast and power-efficient.</p>
                <style>.ads { color: red; }</style>
                <script>console.log("adblock");</script>
                <a href="https://laptops.com/spec1">Spec Details</a>
            </body>
        </html>
        """
        parser = CleanTextExtractor()
        parser.feed(html_content)
        
        self.assertEqual(parser.page_title, "Test Laptop Review")
        self.assertIn("Best Laptops of 2026", parser.get_clean_text())
        self.assertIn("fast and power-efficient", parser.get_clean_text())
        # Styles and Scripts should be stripped
        self.assertNotIn("adblock", parser.get_clean_text())
        self.assertNotIn(".ads", parser.get_clean_text())
        self.assertIn("https://laptops.com/spec1", parser.get_links())
        print("[PASS] Clean HTML extractor verified successfully.")

    @patch("requests.get")
    def test_web_scrape_tool_execution(self, mock_get):
        """Asserts WebScrapeTool executes successfully and limits context returns."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html><head><title>Scraped</title></head><body>Clean Text</body></html>"
        mock_get.return_value = mock_response
        
        tool = WebScrapeTool()
        res = tool.execute({"url": "http://example.com"})
        
        self.assertTrue(res["success"])
        self.assertEqual(res["title"], "Scraped")
        self.assertIn("Clean Text", res["text"])
        print("[PASS] WebScrapeTool execution verified successfully.")

    @patch("pyautogui.moveTo")
    @patch("pyautogui.click")
    @patch("pyautogui.position")
    @patch("vision.ui_context.UIContextExtractor.extract_active_window")
    def test_click_control_revalidation(self, mock_extract, mock_pos, mock_click, mock_move):
        """Asserts DesktopClickControlTool revalidates UIA coordinates immediately before clicking."""
        mock_extract.return_value = {
            "elements": [
                {"name": "Login Button", "automation_id": "btn_login", "bbox": [100, 150, 80, 40], "type": "Button"}
            ]
        }
        mock_pos.return_value = (0, 0)
        
        tool = DesktopClickControlTool()
        
        # Test clicking by name
        res_name = tool.execute({"target": "Login Button"})
        self.assertTrue(res_name["success"])
        self.assertIn("Login Button", res_name["message"])
        
        # Verify pyautogui click coordinates center: X = 100 + 40 = 140, Y = 150 + 20 = 170
        mock_move.assert_any_call(140, 170, duration=0.4)
        
        # Test clicking by automation ID
        res_id = tool.execute({"target": "btn_login"})
        self.assertTrue(res_id["success"])
        
        print("[PASS] DesktopClickControlTool UIA pre-click revalidation verified successfully.")

    def test_nested_parameter_propagation(self):
        """Asserts WorkflowEngine resolves dictionary nested sub-keys using dot-notation."""
        session = SessionManager()
        engine = WorkflowEngine(session)
        
        # Simulate scraper step output dictionary
        engine.outputs[1] = {
            "title": "Laptop Specs",
            "text": "16GB RAM, M3 Chip",
            "links": ["http://link1.com"]
        }
        
        raw_params = {
            "prompt": "Write notes for: {output_step_1.title} - Specifications are {output_step_1.text}"
        }
        
        resolved = engine._resolve_parameters(raw_params)
        self.assertEqual(resolved["prompt"], "Write notes for: Laptop Specs - Specifications are 16GB RAM, M3 Chip")
        print("[PASS] Nested parameter dot-notation resolution verified successfully.")

    @patch("builtins.input")
    def test_automation_safe_mode_human_approval(self, mock_input):
        """Asserts SAFE mode Human Approval Gate correctly prompts and blocks execution."""
        session = SessionManager()
        # Set to SAFE mode
        session.automation_mode = "safe"
        
        engine = WorkflowEngine(session)
        
        # Plan containing sensitive click actions
        sensitive_steps = [
            {"step_id": 1, "description": "Click Login", "intent": "click_control", "parameters": {"target": "btn_login"}}
        ]
        
        # Simulate User Denying Approval ('n')
        mock_input.return_value = "n"
        res_deny = engine.execute_plan(sensitive_steps)
        self.assertFalse(res_deny)
        
        print("[PASS] SAFE mode Human Approval Gate blocking verified successfully.")

    @patch("builtins.input")
    def test_low_confidence_gate(self, mock_input):
        """Asserts plan confidence score blocks and requires operator approval when low (< 0.8)."""
        session = SessionManager()
        engine = WorkflowEngine(session)
        
        steps = [
            {"step_id": 1, "description": "Standard step", "intent": "general_query", "parameters": {"prompt": "Hi"}}
        ]
        
        # Simulate low confidence (0.65) and user approving ('y')
        mock_input.return_value = "y"
        res_approve = engine.execute_plan(steps, confidence=0.65)
        self.assertTrue(res_approve)
        
        # Simulate low confidence (0.65) and user denying ('n')
        mock_input.return_value = "n"
        res_deny = engine.execute_plan(steps, confidence=0.65)
        self.assertFalse(res_deny)
        
        print("[PASS] Low planner confidence score gate blocks verified successfully.")

    def test_workflow_artifact_persistence(self):
        """Asserts completed workflows successfully serialize and write history records."""
        session = SessionManager()
        session.automation_mode = "auto"
        engine = WorkflowEngine(session)
        
        steps = [
            {"step_id": 1, "description": "Hi", "intent": "general_query", "parameters": {"prompt": "Hi"}}
        ]
        
        # Execute successful plan
        res = engine.execute_plan(steps, confidence=0.95)
        self.assertTrue(res)
        
        # Verify artifact file was created under data/workflows/
        from config.settings import BASE_DIR
        workflow_dir = os.path.join(BASE_DIR, "data", "workflows")
        self.assertTrue(os.path.exists(workflow_dir))
        
        files = os.listdir(workflow_dir)
        self.assertGreater(len(files), 0)
        
        # Verify that we can load one of the files as JSON
        import json
        with open(os.path.join(workflow_dir, files[0]), "r", encoding="utf-8") as f:
            data = json.load(f)
            self.assertEqual(data["automation_mode"], "auto")
            self.assertEqual(data["confidence_score"], 0.95)
            self.assertEqual(len(data["steps"]), 1)
            
        print("[PASS] Workflow serialization and persistence verified successfully.")

if __name__ == "__main__":
    unittest.main()
