# c:\Users\mshas\OneDrive\Desktop\SUNDAY\tests\test_integration.py
"""
Automated Integration Verification Suite for SUNDAY Adaptive Model Selection.
Validates zero-dependency RAM diagnostics, mode-aware model routing, 
and recursive automatic model downgrade protection fallbacks.
"""
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Ensure project root is in python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.model_registry import get_system_ram_info, get_model_for_mode, FALLBACK_ORDER
from brain.brain import BrainModule

class TestSUNDAYModelIntegration(unittest.TestCase):
    
    def test_ctypes_ram_diagnostics(self):
        """Asserts Windows ctypes RAM diagnostics return correct numeric shapes."""
        ram_info = get_system_ram_info()
        print(f"\n[TEST INFO] System RAM Diagnostics:")
        print(f"            Total Physical RAM : {ram_info['total_gb']:.2f} GB")
        print(f"            Available RAM      : {ram_info['avail_gb']:.2f} GB")
        print(f"            Memory Load        : {ram_info['memory_load']}%")
        
        self.assertIn("total_gb", ram_info)
        self.assertIn("avail_gb", ram_info)
        self.assertIn("memory_load", ram_info)
        self.assertGreater(ram_info["total_gb"], 0.0)
        self.assertGreaterEqual(ram_info["avail_gb"], 0.0)
        self.assertTrue(0 <= ram_info["memory_load"] <= 100)
        print("[PASS] ctypes RAM diagnostics verified successfully.")

    def test_mode_aware_routing(self):
        """Asserts that brain modes map to exact models or fallback through the chain."""
        available_tags = ["llama3.2:1b", "llama3.2:latest", "phi3:latest"]
        
        # Test FAST Mode matches Llama 1B
        model_fast = get_model_for_mode("FAST", available_tags)
        self.assertEqual(model_fast, "llama3.2:1b")
        
        # Test NORMAL Mode matches Llama 3B
        model_normal = get_model_for_mode("NORMAL", available_tags)
        self.assertEqual(model_normal, "llama3.2:latest")
        
        # Test CODE Mode matches Phi-3 3.8B
        model_code = get_model_for_mode("CODE", available_tags)
        self.assertEqual(model_code, "phi3:latest")
        
        # Test THINK Mode (which prefers llama3:8b, missing here) falls back to llama3.2:latest
        model_think = get_model_for_mode("THINK", available_tags)
        self.assertEqual(model_think, "llama3.2:latest")
        
        print("[PASS] Mode-aware priority routing and fallback matching verified successfully.")

    @patch("requests.post")
    def test_dynamic_downgrade_protection(self, mock_post):
        """
        Simulates an Ollama server error (500 or timeout) on the active model,
        asserting the system automatically downgrades through the fallback chain
        and retries the query recursively until a healthy model responds.
        """
        # Create brain instance
        brain = BrainModule()
        
        # Configure fallback order for control
        # Let's mock the request:
        # First call: llama3.2:latest -> Fails with HTTP 500
        # Second call: phi3:latest -> Succeeds
        
        mock_fail_response = MagicMock()
        mock_fail_response.status_code = 500
        mock_fail_response.text = "Internal Server Error: Out of Memory"
        
        mock_success_response = MagicMock()
        mock_success_response.status_code = 200
        mock_success_response.json.return_value = {
            "message": {"content": "Success response text"},
            "total_duration": 1000000000,
            "eval_count": 10,
            "eval_duration": 500000000,
            "prompt_eval_count": 5,
            "prompt_eval_duration": 200000000
        }
        
        def mock_post_side_effect(url, json, **kwargs):
            model = json.get("model", "")
            if model == "llama3.2:latest":
                return mock_fail_response
            return mock_success_response
        
        mock_post.side_effect = mock_post_side_effect
        
        # Force initial active model to llama3.2:latest
        brain.active_model = "llama3.2:latest"
        
        payload = {
            "model": "llama3.2:latest",
            "messages": [{"role": "user", "content": "Hi"}],
            "options": {}
        }
        
        print("\n[TEST INFO] Simulating model query OOM error for 'llama3.2:latest'...")
        result = brain.execute_ollama_call(payload)
        
        # Verify call succeeded on retry
        self.assertTrue(result["success"])
        self.assertEqual(result["content"], "Success response text")
        
        # Verify the brain dynamically downgraded active model to the next fallback: phi3:latest
        self.assertEqual(brain.active_model, "phi3:latest")
        
        # Verify requests.post was called to perform the query and fallback retries
        self.assertGreaterEqual(mock_post.call_count, 2)
        print("[PASS] Dynamic model downgrade protection verified successfully.")

if __name__ == "__main__":
    unittest.main()
