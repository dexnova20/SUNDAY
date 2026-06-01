# c:\Users\mshas\OneDrive\Desktop\SUNDAY\brain\brain.py
"""
LLM Brain & Cognitive Routing Layers for SUNDAY.
Implements the dual-mode operational brain, switchable brain modes (FAST/NORMAL/THINK/CODE),
mode-specific Ollama generation parameters, response caching, and timing benchmarks.
Includes dynamic model selection, dynamic resource checking, auto-downgrade fallback protection,
intelligent task routing, and dynamic context budgeting.
"""
import json
import re
import requests
import time
import threading
import logging
from typing import Dict, Any, List, Optional
from config.settings import OLLAMA_URL, PREFERRED_MODEL, FALLBACK_CHAIN
from utils.constants import SHORTCUT_KEYWORDS
from utils.helpers import safe_subprocess_popen
from utils.logger import log_debug
from brain.router import IntelligentRouter
from brain.context_budgeter import DynamicContextBudgeter

logger = logging.getLogger("BRAIN")
logger.propagate = False

# =====================================================================
# Response Caching Registry with Hit/Miss Telemetry
# =====================================================================

class ResponseCache:
    _cache = {}
    _hits = 0
    _misses = 0

    @staticmethod
    def get(key: str) -> Optional[str]:
        val = ResponseCache._cache.get(key)
        if val is not None:
            ResponseCache._hits += 1
            log_debug(f"[CACHE HIT] Key: '{key}' | Hits: {ResponseCache._hits}, Misses: {ResponseCache._misses} (Hit Rate: {ResponseCache.hit_rate():.2%})")
            return val
        else:
            ResponseCache._misses += 1
            log_debug(f"[CACHE MISS] Key: '{key}' | Hits: {ResponseCache._hits}, Misses: {ResponseCache._misses} (Hit Rate: {ResponseCache.hit_rate():.2%})")
            return None

    @staticmethod
    def set(key: str, value: str):
        ResponseCache._cache[key] = value

    @staticmethod
    def invalidate():
        ResponseCache._cache.clear()
        log_debug("[CACHE INVALIDATE] Cleared entire response cache.")

    @staticmethod
    def hit_rate() -> float:
        total = ResponseCache._hits + ResponseCache._misses
        return ResponseCache._hits / total if total > 0 else 0.0


# =====================================================================
# Extensible Modular Brain Handlers
# =====================================================================

class ChatBrainHandler:
    """Handles general conversational routing, prompting, and parameter tuning."""
    def __init__(self, brain):
        self.brain = brain

    def build_payload(self, text: str, context: Optional[Dict[str, Any]] = None, task_type: str = "chat") -> Dict[str, Any]:
        from brain.context_compressor import ContextCompressor
        
        # Compress and prune context via Context Compression Layer
        compressed = ContextCompressor.compress(text, context)
        
        # Apply Dynamic Context Budgeting based on task type
        budgeted = DynamicContextBudgeter.budget(task_type, compressed)
        
        context_str = ""
        if budgeted["active_window"] != "Unknown Window":
            context_str += f"\nActive Window: {budgeted['active_window']}"
        if budgeted["screen_summary"]:
            context_str += f"\nScreen Context: {budgeted['screen_summary']}"
            
        project_str = ""
        if budgeted["project_context"]:
            project_str = f"\nSystem Context:\n{budgeted['project_context']}"
            
        memory_str = ""
        if budgeted["relevant_memory"]:
            memory_str = f"\nRelevant Memories:\n{budgeted['relevant_memory']}"

        # Dynamic prompts based on active Brain Mode (FAST, NORMAL, THINK, CODE)
        mode_instruction = ""
        if self.brain.brain_mode == "FAST":
            mode_instruction = "\nInstruction: Be extremely concise, direct, and speed-optimized."
        elif self.brain.brain_mode == "THINK":
            mode_instruction = "\nInstruction: Approach this query with deep analytical reasoning. Focus on providing a highly thorough, detailed, and robust conceptual explanation or plan. Evaluate all parameters deeply and construct a comprehensive response."
        elif self.brain.brain_mode == "CODE":
            mode_instruction = "\nInstruction: Approach this query as an expert software engineer. Focus on writing clean, efficient, correct, and well-structured code. Adhere to coding best practices, add relevant documentation or comments, and explain logical steps concisely."

        system_prompt = f"""You are SUNDAY, a private offline AI assistant. 
Answer the user's conversational query directly, calmly, and intelligently. Speak in a helpful and professional tone.
Avoid unnecessary verbosity. Keep your answer relatively concise.{context_str}{project_str}{memory_str}{mode_instruction}"""

        # Mode-specific Parameter Tuning
        temp = 0.5
        predict = 600
        
        if self.brain.brain_mode == "FAST":
            temp = 0.3
            predict = 150
        elif self.brain.brain_mode == "THINK":
            temp = 0.7
            predict = 1000
        elif self.brain.brain_mode == "CODE":
            temp = 0.2
            predict = 800

        # Adjust dynamically to VISION MODE if screen summary is present
        if budgeted["screen_summary"]:
            temp = 0.2
            predict = 300

        return {
            "model": self.brain.active_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            "stream": False,
            "options": {
                "temperature": temp,
                "num_predict": predict
            }
        }


class ActionBrainHandler:
    """Handles command parsing, parameter extraction, and strict JSON construction."""
    def __init__(self, brain):
        self.brain = brain

    def build_payload(self, text: str, context: Optional[Dict[str, Any]] = None, pending_task: Optional[Dict[str, Any]] = None, task_type: str = "automation") -> Dict[str, Any]:
        from brain.context_compressor import ContextCompressor
        
        # Compress and prune context via Context Compression Layer
        compressed = ContextCompressor.compress(text, context)
        
        # Apply Dynamic Context Budgeting based on task type
        budgeted = DynamicContextBudgeter.budget(task_type, compressed)
        
        context_str = ""
        if budgeted["active_window"] != "Unknown Window":
            context_str += f"\nActive Window: {budgeted['active_window']}"
        if budgeted["screen_summary"]:
            context_str += f"\nScreen Context: {budgeted['screen_summary']}"
            
        project_str = ""
        if budgeted["project_context"]:
            project_str = f"\nSystem Context:\n{budgeted['project_context']}"
            
        memory_str = ""
        if budgeted["relevant_memory"]:
            memory_str = f"\nRelevant Memories:\n{budgeted['relevant_memory']}"

        pending_str = json.dumps(pending_task, indent=2) if pending_task else "None"

        # Action mode specific instructions
        mode_instruction = ""
        if self.brain.brain_mode == "FAST":
            mode_instruction = "\nMinimize response size; extract only direct matches."
        elif self.brain.brain_mode == "CODE":
            mode_instruction = "\nFocus on highly accurate programming parameters, script files, or shell commands."

        system_prompt = f"""You are SUNDAY, a strict offline command parser. Convert user input to JSON.
Intents: open_app(app_name), search_web(query), take_screenshot, read_file(file_path), type_text(text), play_media(title, platform), adjust_volume(action: up/down/mute), adjust_brightness(action: up/down), general_query.

Rules:
1. If info is missing for the intent, set "is_complete": false and write "follow_up_question".
2. Otherwise, set "is_complete": true.
3. Output STRICTLY VALID JSON ONLY. Do not include markdown codeblocks (e.g. no ```json). Do not include any explanation, conversational text, or wrapper.
4. JSON Schema: {{ "intent": "name", "parameters": {{}}, "is_complete": bool, "missing_info": str, "follow_up_question": str, "sensitivity": 0-2 }}

{project_str}{context_str}{memory_str}{mode_instruction}
Pending Task: {pending_str}"""

        # ACTION MODE Parameter Tuning
        temp = 0.1
        predict = 200
        
        if self.brain.brain_mode == "FAST":
            temp = 0.05
            predict = 120
        elif self.brain.brain_mode == "CODE":
            temp = 0.05
            predict = 300

        return {
            "model": self.brain.active_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            "stream": False,
            "options": {
                "temperature": temp,
                "num_predict": predict
            }
        }


# =====================================================================
# Main Modular Brain Module
# =====================================================================

class BrainModule:
    def __init__(self):
        self.url = OLLAMA_URL.rstrip('/') + "/api/chat"
        self.preferred_model = PREFERRED_MODEL
        self.fallback_chain = FALLBACK_CHAIN
        self.active_model = FALLBACK_CHAIN[0] if FALLBACK_CHAIN else "llama3.2:1b"
        self.brain_mode = "NORMAL"
        self.warmstart_latency = 0.0
        self.chat_handler = ChatBrainHandler(self)
        self.action_handler = ActionBrainHandler(self)
        self.refresh_active_model()
        log_debug(f"[BRAIN] BrainModule initialized in {self.brain_mode} Mode. Active Model: {self.active_model}")
        # Startup Warmup thread removed to prevent background VRAM contention

    def set_brain_mode(self, mode: str) -> bool:
        """Dynamically sets switchable reasoning modes (FAST / NORMAL / THINK / CODE)."""
        mode_upper = mode.strip().upper()
        if mode_upper in ["FAST", "NORMAL", "THINK", "CODE"]:
            self.brain_mode = mode_upper
            log_debug(f"[BRAIN] Brain Mode updated to: {self.brain_mode}")
            self.refresh_active_model()
            # Warmup thread removed
            return True
        return False

    def refresh_active_model(self):
        """Checks available Ollama models and selects the best model based on brain mode."""
        try:
            requests.get(OLLAMA_URL, timeout=2)
        except requests.ConnectionError:
            try:
                safe_subprocess_popen(["ollama", "serve"])
                time.sleep(3)
            except Exception:
                pass

        try:
            response = requests.get(OLLAMA_URL.rstrip('/') + "/api/tags", timeout=3)
            if response.status_code == 200:
                available_models = [m["name"] for m in response.json().get("models", [])]
                from models.model_registry import get_model_for_mode
                self.active_model = get_model_for_mode(self.brain_mode, available_models)
        except Exception:
            pass

    def warmup_model(self) -> float:
        """Warms up the active model in memory. Runs silently in background."""
        start_t = time.time()
        try:
            payload = {
                "model": self.active_model,
                "messages": [{"role": "user", "content": "Hi"}],
                "stream": False,
                "options": {"num_predict": 1}
            }
            response = requests.post(self.url, json=payload, timeout=25)
            elapsed = time.time() - start_t
            if response.status_code == 200:
                self.warmstart_latency = elapsed
                log_debug(f"[BRAIN] Warm-start complete. Model: '{self.active_model}' | Latency: {elapsed:.4f}s")
                return elapsed
        except Exception as e:
            log_debug(f"[BRAIN] Warm-start failed: {e}")
        self.warmstart_latency = time.time() - start_t
        return self.warmstart_latency

    def classify_mode(self, text: str, routing: dict = None) -> str:
        """
        Determines whether a command is conversational (CHAT) or operational (ACTION).
        Uses router result directly — no LLM call needed.
        """
        # If router already classified this, use it
        if routing:
            task_type = routing.get("task_type", "chat")
            if task_type in ("automation", "coding", "planning", "vision"):
                log_debug(f"[BRAIN] Mode: ACTION (router task_type={task_type})")
                return "ACTION"
            log_debug(f"[BRAIN] Mode: CHAT (router task_type={task_type})")
            return "CHAT"

        # Keyword fast-path fallback
        text_lower = text.lower()
        if any(kw in text_lower for kw in SHORTCUT_KEYWORDS):
            log_debug("[BRAIN] Mode: ACTION (keyword match)")
            return "ACTION"
        return "CHAT"

    def execute_ollama_call(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Executes the POST request to Ollama with timing telemetry (debug only).
        Includes automatic model downgrade protection on timeouts or failures.
        """
        current_model = payload.get("model", self.active_model)
        log_debug(f"[OLLAMA] Request → model='{current_model}' temp={payload['options'].get('temperature')} max_tokens={payload['options'].get('num_predict')}")

        start_time = time.time()
        try:
            response = requests.post(self.url, json=payload, timeout=30)
            elapsed = time.time() - start_time

            if response.status_code != 200:
                error_msg = f"HTTP status {response.status_code}"
                if response.status_code == 500 or "out of memory" in response.text.lower():
                    error_msg = "OOM / Internal Server Error"
                raise RuntimeError(error_msg)

            data = response.json()
            raw_content = data.get("message", {}).get("content", "")

            total_dur = data.get("total_duration", 0) / 1e9
            eval_cnt = data.get("eval_count", 0)
            eval_dur = data.get("eval_duration", 0) / 1e9
            prompt_dur = data.get("prompt_eval_duration", 0) / 1e9
            first_token_latency = prompt_dur if prompt_dur > 0 else elapsed * 0.1

            log_debug(f"[BENCHMARK] Wall: {elapsed:.4f}s | First token: {first_token_latency:.4f}s | Tokens: {eval_cnt} @ {eval_cnt/eval_dur:.1f}/s" if eval_cnt > 0 and eval_dur > 0 else f"[BENCHMARK] Wall: {elapsed:.4f}s")

            # Record success in health monitor
            try:
                from utils.ollama_health import record_success
                record_success(elapsed)
            except Exception:
                pass

            return {
                "content": raw_content,
                "success": True,
                "latency": elapsed,
                "first_token": first_token_latency,
                "eval_count": eval_cnt
            }

        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError, RuntimeError, Exception) as e:
            elapsed = time.time() - start_time
            error_type = "timeout" if isinstance(e, requests.exceptions.Timeout) else str(e)
            log_debug(f"[OLLAMA] Query failed on '{current_model}' after {elapsed:.2f}s: {error_type}")

            # Record failure in health monitor
            try:
                from utils.ollama_health import record_failure
                record_failure(is_timeout=isinstance(e, requests.exceptions.Timeout))
            except Exception:
                pass

            from models.model_registry import FALLBACK_ORDER
            current_clean = current_model.lower().replace(":latest", "").strip()
            fallback_clean = [f.lower().replace(":latest", "").strip() for f in FALLBACK_ORDER]

            next_model = None
            try:
                idx = fallback_clean.index(current_clean)
                if idx < len(FALLBACK_ORDER) - 1:
                    next_model = FALLBACK_ORDER[idx + 1]
            except ValueError:
                next_model = FALLBACK_ORDER[0]

            if next_model and next_model.lower() != current_clean:
                log_debug(f"[DOWNGRADE] '{current_model}' → '{next_model}'")
                self.active_model = next_model
                payload["model"] = next_model
                return self.execute_ollama_call(payload)

            return {"content": "", "success": False, "error": error_type}

    def process_chat(self, text: str, context: dict = None, task_type: str = "chat") -> dict:
        """Processes conversational queries using ChatBrainHandler."""
        payload = self.chat_handler.build_payload(text, context, task_type=task_type)
        result = self.execute_ollama_call(payload)

        if result["success"]:
            reply_text = result["content"].strip()
            reply_text = self.chat_quality_guard(text, reply_text)
            return {"intent": "general_query", "parameters": {}, "sensitivity": 0, "reply_text": reply_text}
        else:
            err_msg = "I encountered a timeout while thinking." if result.get("error") == "timeout" else "I encountered an error while processing."
            return {"intent": "general_query", "parameters": {}, "sensitivity": 0, "reply_text": err_msg}

    def chat_quality_guard(self, original_query: str, response: str) -> str:
        """
        Validates chat response quality. If the response is too short, empty,
        or is blacklisted, regenerates exactly once.
        """
        blacklist = {"sunday.", "i'm sunday.", "i am sunday.", "sunday", ""}

        def is_bad(text: str) -> bool:
            if not text:
                return True
            stripped = text.strip()
            if len(stripped) < 5:
                return True
            if stripped.lower() in blacklist:
                return True
            # Repeats only name variations
            if stripped.lower() in ("i'm sunday.", "i am sunday.", "i'm sunday", "i am sunday"):
                return True
            return False

        if not is_bad(response):
            return response

        log_debug(f"[QUALITY GUARD] Poor response detected: '{response}'. Regenerating...")
        
        # Regenerate exactly once
        retry_payload = self.chat_handler.build_payload(
            f"Please give a helpful, friendly response to: {original_query}",
            task_type="chat"
        )
        retry_result = self.execute_ollama_call(retry_payload)
        if retry_result["success"]:
            retried = retry_result["content"].strip()
            if not is_bad(retried):
                return retried
                
        # Return fallback if second attempt fails
        return "Sorry, I had trouble generating a response."

    def _extract_and_parse_json(self, text: str) -> Optional[dict]:
        """Tries to extract and parse JSON from verbose LLM responses."""
        clean_text = text.strip()
        code_block_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", clean_text, re.DOTALL)
        if code_block_match:
            clean_text = code_block_match.group(1).strip()
        else:
            start = clean_text.find('{')
            end = clean_text.rfind('}') + 1
            if start != -1 and end > start:
                clean_text = clean_text[start:end].strip()
        try:
            return json.loads(clean_text)
        except json.JSONDecodeError as e:
            log_debug(f"[JSON] Decode error: {e}")
            return None

    def process_action(self, text: str, context: dict = None, pending_task: dict = None, task_type: str = "automation") -> dict:
        """Processes operational actions, implements JSON self-repair and graceful fallbacks."""
        payload = self.action_handler.build_payload(text, context, pending_task, task_type=task_type)
        result = self.execute_ollama_call(payload)

        if not result["success"]:
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

        log_debug("[JSON] Malformed JSON. Triggering self-repair...")
        correction_prompt = f"""The previous response was not valid JSON. Output ONLY valid JSON, no markdown, no extra text.

Invalid response:
{raw_response}

Corrected JSON:"""

        correction_payload = {
            "model": self.active_model,
            "messages": [
                {"role": "system", "content": "You are a precise JSON repair utility. Output strictly valid JSON."},
                {"role": "user", "content": correction_prompt}
            ],
            "stream": False,
            "options": {"temperature": 0.0, "num_predict": 200}
        }

        repair_result = self.execute_ollama_call(correction_payload)
        if repair_result["success"]:
            repaired_json = self._extract_and_parse_json(repair_result["content"])
            if repaired_json is not None:
                log_debug("[JSON] Self-repair succeeded.")
                return repaired_json

        log_debug("[JSON] Self-repair failed. Falling back to CHAT mode.")
        fallback_reply = re.sub(r"```(?:json)?|```", "", raw_response).strip()
        return {
            "intent": "general_query",
            "parameters": {},
            "sensitivity": 0,
            "reply_text": fallback_reply,
            "is_complete": True
        }

    def process_command(self, text: str, context: dict = None, pending_task: dict = None) -> dict:
        """Routes text through Intelligent Task Router with dynamic model selection."""
        if self.active_model != self.preferred_model:
            self.refresh_active_model()

        norm_text = text.lower().strip().translate(str.maketrans('', '', '?!!.,;:'))

        # Check Response Cache
        cache_hit = ResponseCache.get(norm_text)
        if cache_hit is not None:
            return {"intent": "general_query", "parameters": {}, "sensitivity": 0, "reply_text": cache_hit}

        # Intelligent Task Router
        routing = IntelligentRouter.classify_and_route(text)
        task_type = routing["task_type"]
        recommended_profile = routing["reasoning_profile"]

        previous_mode = self.brain_mode
        if self.brain_mode == "NORMAL" and recommended_profile != "NORMAL":
            self.brain_mode = recommended_profile
            self.refresh_active_model()
            log_debug(f"[ROUTER] Auto-switched brain mode: {previous_mode} → {self.brain_mode} (task: {task_type})")

        if pending_task:
            result = self.process_action(text, context, pending_task, task_type=task_type)
            if self.brain_mode != previous_mode and previous_mode == "NORMAL":
                self.brain_mode = previous_mode
                self.refresh_active_model()
            return result

        # Use router result directly — no second LLM classification call
        mode = self.classify_mode(text, routing=routing)
        log_debug(f"[BRAIN] [{mode} MODE] '{text}' (task: {task_type})")

        res = self.process_chat(text, context, task_type=task_type) if mode == "CHAT" else self.process_action(text, context, task_type=task_type)

        if self.brain_mode != previous_mode and previous_mode == "NORMAL":
            self.brain_mode = previous_mode
            self.refresh_active_model()

        if res and res.get("intent") == "general_query" and res.get("reply_text"):
            cacheable_triggers = ["help", "status", "project", "task", "goal"]
            if any(t in norm_text for t in cacheable_triggers):
                ResponseCache.set(norm_text, res["reply_text"])

        return res
