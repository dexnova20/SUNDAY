import json
import re
import requests
import subprocess
import time
import threading
from typing import Dict, Any, List, Optional

# =====================================================================
# Extensible Modular Brain Handlers (Ready for splitting into separate files)
# =====================================================================

class ChatBrainHandler:
    """Handles general conversational routing, prompting, and parameter tuning."""
    def __init__(self, brain):
        self.brain = brain

    def build_payload(self, text: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        # Filter and minimize context payload size to prevent RAM overload
        # Task-relevant context injection only
        context_str = ""
        if context:
            min_context = {}
            if context.get("active_window") and context["active_window"] != "Unknown Window":
                min_context["active_window"] = context["active_window"]
            if context.get("screen_text") and "No selectable text" not in context["screen_text"] and "Failed to read" not in context["screen_text"]:
                min_context["screen_text"] = context["screen_text"][:500] # Kept short for speed
            
            if min_context:
                context_str = f"\nCurrent Screen Context:\n{json.dumps(min_context, indent=2)}"

        system_prompt = f"""You are SUNDAY, a private offline AI assistant. 
Answer the user's conversational query directly, calmly, and intelligently. Speak in a helpful and professional tone.
Avoid unnecessary verbosity. Keep your answer relatively concise.{context_str}"""

        return {
            "model": self.brain.active_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            "stream": False,
            "options": {
                "temperature": 0.5,       # Optimized for creative reasoning but grounded
                "num_predict": 600        # Max tokens to prevent rambling / freezes
            }
        }


class ActionBrainHandler:
    """Handles command parsing, parameter extraction, and strict JSON construction."""
    def __init__(self, brain):
        self.brain = brain

    def build_payload(self, text: str, context: Optional[Dict[str, Any]] = None, pending_task: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        # Minimize and keep context task-relevant to avoid context bloating
        context_str = ""
        if context:
            min_context = {}
            if context.get("active_window") and context["active_window"] != "Unknown Window":
                min_context["active_window"] = context["active_window"]
            if context.get("screen_text") and "No selectable text" not in context["screen_text"] and "Failed to read" not in context["screen_text"]:
                # Only inject screen text if user asks about the screen
                text_lower = text.lower()
                screen_words = ["screen", "visual", "read", "explain this", "this tab", "page"]
                if any(w in text_lower for w in screen_words):
                    min_context["screen_text"] = context["screen_text"][:500] # Strict 500 chars limit
            
            if min_context:
                context_str = f"\nRelevant Context:\n{json.dumps(min_context, indent=2)}"

        pending_str = json.dumps(pending_task, indent=2) if pending_task else "None"

        system_prompt = f"""You are SUNDAY, a strict offline command parser. Convert user input to JSON.
Intents: open_app(app_name), search_web(query), take_screenshot, read_file(file_path), type_text(text), play_media(title, platform), adjust_volume(action: up/down/mute), adjust_brightness(action: up/down), general_query.

Rules:
1. If info is missing for the intent, set "is_complete": false and write "follow_up_question".
2. Otherwise, set "is_complete": true.
3. Output STRICTLY VALID JSON ONLY. Do not include markdown codeblocks (e.g. no ```json). Do not include any explanation, conversational text, or wrapper.
4. JSON Schema: {{ "intent": "name", "parameters": {{}}, "is_complete": bool, "missing_info": str, "follow_up_question": str, "sensitivity": 0-2 }}

Context: {context_str}
Pending Task: {pending_str}"""

        return {
            "model": self.brain.active_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            "stream": False,
            "options": {
                "temperature": 0.1,       # Strict low temperature to prevent hallucinating commands
                "num_predict": 200        # Fast short response to avoid rambling
            }
        }


# =====================================================================
# Main Modular Brain Module
# =====================================================================

class BrainModule:
    def __init__(self):
        self.url = "http://localhost:11434/api/chat"
        self.preferred_model = "sundaybrain"
        self.fallback_chain = ["llama3:8b", "llama3.2:latest", "llama3.2:1b", "phi3:latest"]
        self.active_model = "llama3.2:1b"  # Default initial fallback
        
        # Initialize handlers
        self.chat_handler = ChatBrainHandler(self)
        self.action_handler = ActionBrainHandler(self)

        # Check Ollama and select active model
        self.refresh_active_model()
        
        print(f"[BRAIN] BrainModule initialized. Active Model: {self.active_model}")

        # Warm-up call in a background thread to load the model into VRAM
        threading.Thread(target=self.warmup_model, daemon=True).start()

    def refresh_active_model(self):
        """Checks available Ollama models and selects the best model from the fallback chain."""
        try:
            # First, check if Ollama is running
            requests.get("http://localhost:11434/", timeout=2)
        except requests.ConnectionError:
            # We attempt to auto-launch Ollama
            print("[OLLAMA] Ollama is not running. Attempting to start...")
            try:
                subprocess.Popen(["ollama", "serve"], creationflags=subprocess.CREATE_NO_WINDOW)
                # We give it a short time here, but we don't block too long.
                # The main startup script will handle deeper diagnostics.
                time.sleep(3)
            except Exception as e:
                print(f"[OLLAMA] Failed to auto-start Ollama: {e}")

        # Check available models
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=3)
            if response.status_code == 200:
                available_models = [m["name"] for m in response.json().get("models", [])]
                
                # Check for absolute matches first
                if self.preferred_model in available_models or any(self.preferred_model in m for m in available_models):
                    # Resolve exact name in tag list
                    matched = next((m for m in available_models if self.preferred_model in m), self.preferred_model)
                    self.active_model = matched
                    return
                
                # Try fallback chain
                for fallback in self.fallback_chain:
                    matched = next((m for m in available_models if fallback in m), None)
                    if matched:
                        print(f"[BRAIN] Preferred model '{self.preferred_model}' not found. Falling back to '{matched}'.")
                        self.active_model = matched
                        return
                
                # Failsafe: Use first available model if any exists
                if available_models:
                    self.active_model = available_models[0]
                    print(f"[BRAIN] Warning: No models in fallback chain found. Using first available: '{self.active_model}'")
            else:
                print(f"[OLLAMA] Server responded with error code {response.status_code}. Using fallback {self.active_model}")
        except Exception as e:
            print(f"[OLLAMA] Error listing models: {e}. Using fallback {self.active_model}")

    def warmup_model(self):
        """Performs a lightweight query to warm up the active model in memory."""
        try:
            print(f"[OLLAMA] Warming up active model '{self.active_model}' in background...")
            payload = {
                "model": self.active_model,
                "messages": [{"role": "user", "content": "Hi"}],
                "stream": False,
                "options": {"num_predict": 5}
            }
            requests.post(self.url, json=payload, timeout=10)
            print(f"[OLLAMA] Model '{self.active_model}' warmed up successfully.")
        except Exception as e:
            print(f"[OLLAMA] Warm-up failed: {e}")

    def classify_mode(self, text: str) -> str:
        """Determines whether a command is conversational (CHAT) or operational (ACTION)."""
        keywords = [
            "open", "run", "start", "close", "take", "search", "launch", "type", "write", "enter",
            "brightness", "volume", "mute", "unmute", "play", "pause", "next", "previous", "skip",
            "shutdown", "restart", "sleep", "screenshot", "maximize", "minimize"
        ]
        text_lower = text.lower()
        if any(kw in text_lower for kw in keywords):
            print(f"[BRAIN] Mode classified as ACTION (keyword match).")
            return "ACTION"
            
        # Fallback to LLM for classification
        prompt = f"Is this a command to perform a system action (like opening an app, searching, taking a screenshot) or just a conversational chat/question? Reply with exactly 'ACTION' or 'CHAT'. Do not include any other text.\n\nUser: {text}"
        payload = {
            "model": self.active_model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "options": {
                "temperature": 0.0,
                "num_predict": 10
            }
        }
        
        start_time = time.time()
        try:
            print(f"[BRAIN] Calling LLM to classify mode...")
            response = requests.post(self.url, json=payload, timeout=10)
            response.raise_for_status()
            result = response.json().get("message", {}).get("content", "").strip().upper()
            elapsed = time.time() - start_time
            print(f"[BRAIN] LLM classification took {elapsed:.2f}s. Result: '{result}'")
            
            if "ACTION" in result:
                return "ACTION"
            return "CHAT"
        except Exception as e:
            print(f"[BRAIN] Classification failed: {e}. Falling back to CHAT.")
            return "CHAT"

    def execute_ollama_call(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Executes the POST request to Ollama and records detailed timing telemetry."""
        print(f"[OLLAMA] Sending request to {self.url} using model '{payload['model']}'...")
        print(f"[OLLAMA] Parameters: temp={payload['options'].get('temperature')}, max_tokens={payload['options'].get('num_predict')}")
        
        start_time = time.time()
        try:
            response = requests.post(self.url, json=payload, timeout=60)
            elapsed = time.time() - start_time
            response.raise_for_status()
            
            data = response.json()
            raw_content = data.get("message", {}).get("content", "")
            
            print(f"[OLLAMA] Connection successful. HTTP Status: {response.status_code}")
            print(f"[MODEL RESPONSE] Raw Content: {raw_content.strip()}")
            
            # Print Telemetry metrics
            total_dur = data.get("total_duration", 0) / 1e9  # Convert ns to seconds
            eval_cnt = data.get("eval_count", 0)
            eval_dur = data.get("eval_duration", 0) / 1e9
            prompt_cnt = data.get("prompt_eval_count", 0)
            prompt_dur = data.get("prompt_eval_duration", 0) / 1e9
            
            print(f"[BRAIN] --- TELEMETRY ---")
            print(f"[BRAIN] Wall Time: {elapsed:.2f}s")
            if total_dur > 0:
                print(f"[BRAIN] Ollama Total Time: {total_dur:.2f}s")
            if prompt_cnt > 0 and prompt_dur > 0:
                print(f"[BRAIN] Prompt Eval: {prompt_cnt} tokens in {prompt_dur:.2f}s ({prompt_cnt/prompt_dur:.2f} tokens/sec)")
            if eval_cnt > 0 and eval_dur > 0:
                print(f"[BRAIN] Generation: {eval_cnt} tokens in {eval_dur:.2f}s ({eval_cnt/eval_dur:.2f} tokens/sec)")
            print(f"[BRAIN] -----------------")
            
            return {"content": raw_content, "success": True}
        except requests.exceptions.Timeout:
            elapsed = time.time() - start_time
            print(f"[OLLAMA] [ERROR] Request timed out after {elapsed:.2f}s.")
            return {"content": "", "success": False, "error": "timeout"}
        except Exception as e:
            print(f"[OLLAMA] [ERROR] Request failed: {e}")
            return {"content": "", "success": False, "error": str(e)}

    def process_chat(self, text: str, context: dict = None) -> dict:
        """Processes conversational queries using ChatBrainHandler."""
        payload = self.chat_handler.build_payload(text, context)
        result = self.execute_ollama_call(payload)
        
        if result["success"]:
            reply_text = result["content"].strip()
            return {"intent": "general_query", "parameters": {}, "sensitivity": 0, "reply_text": reply_text}
        else:
            err_msg = "I encountered a timeout while thinking." if result.get("error") == "timeout" else "I encountered an error while processing."
            return {"intent": "general_query", "parameters": {}, "sensitivity": 0, "reply_text": err_msg}

    def _extract_and_parse_json(self, text: str) -> Optional[dict]:
        """Tries to extract and parse JSON from verbose LLM responses."""
        clean_text = text.strip()
        
        # Step 1: Strip markdown block wrappers if present
        code_block_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", clean_text, re.DOTALL)
        if code_block_match:
            clean_text = code_block_match.group(1).strip()
        else:
            # Step 2: Extract text between the first '{' and last '}'
            start = clean_text.find('{')
            end = clean_text.rfind('}') + 1
            if start != -1 and end > start:
                clean_text = clean_text[start:end].strip()
        
        try:
            parsed = json.loads(clean_text)
            print(f"[JSON VALIDATION] JSON parsed successfully.")
            return parsed
        except json.JSONDecodeError as e:
            print(f"[JSON VALIDATION] [ERROR] JSON decode error: {e}")
            return None

    def process_action(self, text: str, context: dict = None, pending_task: dict = None) -> dict:
        """Processes operational actions, implements JSON self-repair and graceful failbacks."""
        payload = self.action_handler.build_payload(text, context, pending_task)
        result = self.execute_ollama_call(payload)
        
        if not result["success"]:
            # Connection or timeout error
            return {
                "intent": "general_query",
                "parameters": {},
                "sensitivity": 0,
                "reply_text": "Ollama timed out or connection failed. Try again.",
                "is_complete": True
            }
            
        raw_response = result["content"]
        parsed_json = self._extract_and_parse_json(raw_response)
        
        if parsed_json is not None:
            return parsed_json
            
        # JSON Repair Layer: Trigger a retry once with strict correction
        print("[JSON VALIDATION] Malformed JSON received. Triggering correction self-repair...")
        correction_prompt = f"""The previous response you generated was not valid JSON. Please correct it. 
Output ONLY valid JSON, with absolutely no markdown, no conversational text, and no extra text. 

Invalid response:
{raw_response}

Please output the corrected JSON directly:"""
        
        correction_payload = {
            "model": self.active_model,
            "messages": [
                {"role": "system", "content": "You are a precise JSON repair utility. You output strictly valid JSON conforming to the original intent schema."},
                {"role": "user", "content": correction_prompt}
            ],
            "stream": False,
            "options": {
                "temperature": 0.0,
                "num_predict": 200
            }
        }
        
        repair_result = self.execute_ollama_call(correction_payload)
        if repair_result["success"]:
            repaired_json = self._extract_and_parse_json(repair_result["content"])
            if repaired_json is not None:
                print("[JSON VALIDATION] Self-repair correction succeeded!")
                return repaired_json
                
        # Graceful fallback: If repair fails, fall back to CHAT mode
        print("[JSON VALIDATION] [CRITICAL] Self-repair failed. Falling back to CHAT mode.")
        fallback_reply = raw_response.strip()
        # Clean up code blocks from chat display if present
        fallback_reply = re.sub(r"```(?:json)?|```", "", fallback_reply).strip()
        
        return {
            "intent": "general_query",
            "parameters": {},
            "sensitivity": 0,
            "reply_text": fallback_reply,
            "is_complete": True
        }

    def process_command(self, text: str, context: dict = None, pending_task: dict = None) -> dict:
        """Takes the transcribed text and routes it through Dual-Mode Routing Intelligence."""
        # Refresh the active model in case Ollama recently finished building sundaybrain
        if self.active_model != self.preferred_model:
            self.refresh_active_model()
            
        # Force pending tasks to ACTION mode
        if pending_task:
            print("[BRAIN] [ACTION MODE] Resuming pending task...")
            return self.process_action(text, context, pending_task)
            
        mode = self.classify_mode(text)
        print(f"[BRAIN] [{mode} MODE] Routing command: '{text}'")
        
        if mode == "CHAT":
            return self.process_chat(text, context)
        else:
            return self.process_action(text, context)
