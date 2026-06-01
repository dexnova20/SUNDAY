# c:\Users\mshas\OneDrive\Desktop\SUNDAY\planner\planner.py
"""
Cognitive Planner for SUNDAY.
Calls Ollama to decompose complex instructions into executable plan step JSON objects.
Enforces MAX_STEPS = 10. Supports Vision-based steps dynamically.
Includes dynamic plan confidence scoring.
"""
import json
import re
import requests
import logging
from typing import Dict, Any, List, Optional
from config.settings import OLLAMA_URL
from planner.execution_tracker import ExecutionTracker
from execution.action_executor import ActionExecutor

logger = logging.getLogger("PLANNER")

class CognitivePlanner:
    MAX_STEPS = 10

    def __init__(self, model: str = "llama3.2:1b"):
        self.model = model
        self.executor = ActionExecutor()
        # Retrieve valid intents from action registry keys
        self.valid_intents = set(self.executor.tools.keys())
        self.valid_intents.add("general_query")
        
        # Track plan confidence score (Approved Requirement)
        self.last_confidence_score = 0.90

    def decompose_request(self, user_request: str) -> List[Dict[str, Any]]:
        """
        Decomposes a complex request into a sequence of executable JSON steps by querying Ollama.
        """
        intents_list = ", ".join(self.valid_intents)
        
        system_prompt = f"""You are the SUNDAY Cognitive Planner. Decompose a complex user request into a structured sequence of discrete operational steps.
Available Tool Intents you can choose from:
{intents_list}

Rules:
1. Break the request down into sequential, simple steps (at most {self.MAX_STEPS} steps).
2. For each step, output:
   - "step_id": integer starting from 1
   - "description": clear human description of the step
   - "intent": the precise intent name from the available intents list above
   - "parameters": a dictionary of parameters for the tool (e.g. {{"query": "..."}} or {{"url": "..."}} or {{"target": "..."}})
3. If a step depends on the returned text output of a previous step, use the variable placeholder "{{output_step_X.subkey}}" (e.g. "{{output_step_1.text}}") or "{{output_step_X}}" where X is the preceding step_id.
4. Output a plan-wide "confidence_score" between 0.0 and 1.0 assessing how accurately the steps fulfill the request.
5. Output STRICTLY VALID JSON ONLY. Do not include markdown codeblocks (no ```json). Do not include conversational text or explanations.
6. JSON Output Schema:
{{
  "confidence_score": 0.95,
  "steps": [
    {{
      "step_id": 1,
      "description": "...",
      "intent": "...",
      "parameters": {{}}
    }}
  ]
}}"""

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_request}
            ],
            "stream": False,
            "options": {
                "temperature": 0.1,
                "num_predict": 1000
            }
        }

        try:
            url = OLLAMA_URL.rstrip('/') + "/api/chat"
            response = requests.post(url, json=payload, timeout=45)
            response.raise_for_status()
            
            raw_content = response.json().get("message", {}).get("content", "").strip()
            steps = self._parse_steps_json(raw_content)
            
            # Enforce max step limit
            if len(steps) > self.MAX_STEPS:
                logger.warning(f"Plan length {len(steps)} exceeds MAX_STEPS = {self.MAX_STEPS}. Truncating.")
                steps = steps[:self.MAX_STEPS]

            ExecutionTracker.log_plan_generated(user_request, len(steps))
            return steps
            
        except Exception as e:
            logger.error(f"Failed to decompose request: {e}")
            raise RuntimeError(f"Planner decomposition failed: {str(e)}")

    def _parse_steps_json(self, raw_text: str) -> List[Dict[str, Any]]:
        """Parses and strips markdown from LLM output, extracting steps and confidence."""
        clean_text = raw_text.strip()
        
        # Strip markdown json wrappers
        code_block = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", clean_text, re.DOTALL)
        if code_block:
            clean_text = code_block.group(1).strip()
        else:
            start = clean_text.find('{')
            end = clean_text.rfind('}') + 1
            if start != -1 and end > start:
                clean_text = clean_text[start:end].strip()

        try:
            data = json.loads(clean_text)
            self.last_confidence_score = float(data.get("confidence_score", 0.90))
            print(f"[PLANNER] Decomposed plan confidence score: {self.last_confidence_score:.2f}")
            return data.get("steps", [])
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode failed on planner output: {clean_text}")
            self.last_confidence_score = 0.50 # Low confidence on malformed returns
            # Dynamic fallback: create a single-step general query plan
            return [{
                "step_id": 1,
                "description": "Direct conversation query",
                "intent": "general_query",
                "parameters": {"prompt": raw_text}
            }]
