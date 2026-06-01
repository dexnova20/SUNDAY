# c:\Users\mshas\OneDrive\Desktop\SUNDAY\brain\router.py
"""
Intelligent Task & Model Router for SUNDAY.
Classifies user queries into task categories and maps them to the optimal
reasoning profile and model. Uses a hybrid approach:
  1. High-speed rule-based keyword/regex matchers (< 1ms)
  2. Optional lightweight LLM fallback for ambiguous queries

Task Categories:
  - chat: General conversation, greetings, opinions, open-ended questions
  - coding: Code generation, debugging, scripting, programming queries
  - planning: Multi-step workflows, compound requests, task decomposition
  - memory: Knowledge storage, recall, search operations
  - vision: Screen reading, UI inspection, visual context queries
  - automation: App launching, system controls, web actions, media controls

Reasoning Profiles:
  - FAST: Minimal tokens, speed-optimized (1B model)
  - NORMAL: Balanced speed and quality (3B model)
  - THINK: Deep analysis, full context (3B model with extended budget)
  - CODE: Precision engineering, low temperature (phi3)
"""
import re
import time
import logging
from typing import Dict, Any, Optional, Tuple
from utils.logger import log_debug

logger = logging.getLogger("ROUTER")
logger.propagate = False


# =====================================================================
# Rule-Based Classification Patterns
# =====================================================================

# Ordered by specificity: more specific patterns checked first

AUTOMATION_PATTERNS = [
    r"\b(open|launch|start|run|close|quit|exit)\s+(app|application|program|browser)?\s*\w+",
    r"\b(volume|brightness)\s*(up|down|mute|unmute|increase|decrease|max|min)",
    r"\b(mute|unmute)\b",
    r"\b(play|pause|stop|next|previous|skip)\s*(track|song|video|media)?",
    r"\b(shutdown|restart|sleep|hibernate|lock)\s*(computer|pc|system|machine)?",
    r"\b(take\s+a?\s*screenshot|screenshot|screencap|screen\s*capture)",
    r"\b(type|write|enter|input)\s+[\"']",
    r"\b(click|press|tap|select)\s+(on|the|button|link|control|element)?",
    r"\b(maximize|minimize|resize|move)\s+(window|app)?",
    r"\b(search\s+for|search\s+web|google|bing)\s+",
    r"\b(open\s+website|go\s+to|navigate\s+to|browse)\s+",
    r"\b(web\s*scrape|scrape|extract\s+from)\s+",
]

CODING_PATTERNS = [
    r"\b(write|create|generate|build|implement)\s+(a\s+)?(code|script|function|class|program|module|api|endpoint)",
    r"\b(debug|fix|refactor|optimize|review)\s+(this|the|my)?\s*(code|script|function|bug|error|issue)",
    r"\b(python|javascript|java|c\+\+|rust|go|html|css|sql|bash|powershell|typescript)\b",
    r"\b(algorithm|data\s*structure|recursion|sorting|binary\s*search|linked\s*list|tree|graph)\b",
    r"\b(compile|syntax\s*error|runtime\s*error|exception|traceback|stack\s*trace)\b",
    r"\b(import|def\s|class\s|function\s|const\s|let\s|var\s|return\s)",
    r"\b(git|github|commit|merge|branch|pull\s*request|repo)\b",
    r"\b(regex|regular\s*expression|pattern\s*matching)\b",
    r"\b(api|endpoint|rest|graphql|json|xml|http|request|response)\b",
    r"\b(database|sql|query|table|schema|migration|orm)\b",
    r"\b(docker|container|kubernetes|deploy|ci\s*/?\s*cd|pipeline)\b",
    r"\b(test|unittest|pytest|assert|mock|coverage)\b",
]

PLANNING_PATTERNS = [
    r"\b(plan|planning|strategy|roadmap|outline)\b",
    r"\band\s+then\b",
    r"\bfirst\s+.+\s+then\b",
    r"\bstep\s*by\s*step\b",
    r"\b(workflow|pipeline|sequence|process)\b",
    r"\b(research\s+.+\s+and|analyze\s+.+\s+and)\b",
    r"\b(break\s*down|decompose|multi[- ]step)\b",
    r"\b(schedule|organize|coordinate|prioritize)\b",
]

MEMORY_PATTERNS = [
    r"\b(remember|memorize|store|save)\s+(this|that|the|my)?\s*(fact|info|knowledge|note)?",
    r"\b(recall|retrieve|fetch|find)\s+(what|my|the|about)?\s*(you\s+know|i\s+told|saved|stored)?",
    r"\b(do\s+you\s+remember|what\s+did\s+i\s+(tell|say|teach))",
    r"\b(forget|delete|remove)\s+(this|that|the)?\s*(memory|knowledge|fact|note)?",
    r"\b(search\s+memory|search\s+knowledge|what\s+do\s+you\s+know)\b",
]

VISION_PATTERNS = [
    r"\b(what('s|\s+is)\s+on\s+my\s+screen)",
    r"\b(read|scan|analyze|inspect|look\s+at)\s+(my\s+)?(screen|display|monitor|window|ui)",
    r"\b(describe|explain)\s+(what|this|the)\s*(screen|window|page|app|interface)?",
    r"\b(ocr|text\s+recognition|read\s+text)\b",
    r"\b(ui\s+element|control|button|label|textbox|checkbox)\b",
    r"\b(focused\s+element|active\s+control|cursor\s+position)\b",
    r"\b(bounding\s*box|coordinates|position|layout)\b",
    r"\b(window\s+title|active\s+window|foreground)\b",
]

# Task type -> (default reasoning profile, description)
TASK_PROFILE_MAP = {
    "chat":       ("FAST",   "General conversational queries"),
    "coding":     ("CODE",   "Code generation, debugging, engineering"),
    "planning":   ("THINK",  "Multi-step workflows, task decomposition"),
    "memory":     ("FAST",   "Knowledge storage and retrieval"),
    "vision":     ("FAST",   "Screen reading and UI inspection"),
    "automation": ("NORMAL", "System controls, app launching, actions"),
}


class IntelligentRouter:
    """
    Classifies user queries into task categories and selects the optimal
    reasoning profile and model. Hybrid rule-based + optional LLM fallback.
    """

    @staticmethod
    def classify_task(text: str) -> str:
        """
        Rule-based task classification. Returns one of:
        'automation', 'coding', 'planning', 'memory', 'vision', 'chat'
        """
        text_lower = text.lower().strip()

        # Check patterns in priority order (most specific first)
        pattern_groups = [
            ("automation", AUTOMATION_PATTERNS),
            ("coding",     CODING_PATTERNS),
            ("planning",   PLANNING_PATTERNS),
            ("memory",     MEMORY_PATTERNS),
            ("vision",     VISION_PATTERNS),
        ]

        scores = {}
        for category, patterns in pattern_groups:
            match_count = 0
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    match_count += 1
            if match_count > 0:
                scores[category] = match_count

        if scores:
            # Return category with highest match count
            best = max(scores, key=scores.get)
            logger.info(f"Rule-based classification: '{best}' (scores: {scores})")
            return best

        # Default fallback to chat for unmatched queries
        return "chat"

    @staticmethod
    def get_reasoning_profile(task_type: str) -> str:
        """Returns the reasoning profile for a given task type."""
        profile_info = TASK_PROFILE_MAP.get(task_type)
        if profile_info:
            return profile_info[0]
        return "NORMAL"

    @staticmethod
    def classify_and_route(text: str) -> Dict[str, Any]:
        """
        Full classification pipeline. Returns a routing decision dictionary:
        {
            "task_type": str,
            "reasoning_profile": str,
            "description": str,
            "classification_method": str,
            "latency_ms": float
        }
        """
        start = time.time()

        task_type = IntelligentRouter.classify_task(text)
        profile = IntelligentRouter.get_reasoning_profile(task_type)
        description = TASK_PROFILE_MAP.get(task_type, ("NORMAL", "Unknown"))[1]

        elapsed_ms = (time.time() - start) * 1000

        result = {
            "task_type": task_type,
            "reasoning_profile": profile,
            "description": description,
            "classification_method": "rule_based",
            "latency_ms": round(elapsed_ms, 3),
        }

        from utils.logger import log_msg
        log_msg("ROUTER", f"Task: '{task_type}' | Profile: {profile} | Latency: {elapsed_ms:.3f}ms")
        logger.info(f"Routing decision: {result}")

        return result

    @staticmethod
    def get_model_for_task(task_type: str, available_models: list) -> str:
        """
        Resolves the best model for a classified task type using the model registry.
        Falls back through the standard priority chain if the ideal model is unavailable.
        """
        from models.model_registry import get_model_for_mode
        profile = IntelligentRouter.get_reasoning_profile(task_type)
        return get_model_for_mode(profile, available_models)
