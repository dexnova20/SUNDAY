# c:\Users\mshas\OneDrive\Desktop\SUNDAY\brain\context_budgeter.py
"""
Dynamic Context Budgeting Layer for SUNDAY.
Prunes and caps context inputs dynamically based on task classification
to prevent prompt bloat, reduce latency, and avoid RAM swapping on 8GB systems.

Budget Profiles:
  - chat / vision / FAST: 1,000 tokens. Strip all UIA coordinate lists.
  - coding / CODE: 3,000 tokens. Prioritize code file contents; omit irrelevant memories.
  - planning / automation / THINK: 4,096 tokens. Full UIA layout, historical context, tasks.

Token estimation uses a fast char-based heuristic (~4 chars/token for English text).
"""
import re
import logging
from typing import Dict, Any, Optional
from utils.logger import log_debug

logger = logging.getLogger("CONTEXT_BUDGETER")
logger.propagate = False

# Approximate characters per token (English text average)
CHARS_PER_TOKEN = 4

# Strict hard-limits on context sizes (in estimated tokens) to prevent context creep
BUDGET_CAPS = {
    "chat":       500,
    "memory":     1000,
    "planning":   2000,
    "vision":     1500,
    "coding":     3000,
    "automation": 4096,
}

# Default budget for unknown task types
DEFAULT_BUDGET = 1000


class DynamicContextBudgeter:
    """
    Receives a task type and raw context data, returns a budgeted
    and optimized context dictionary within the token cap.
    """

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """Fast character-based token estimation."""
        if not text:
            return 0
        return max(1, len(text) // CHARS_PER_TOKEN)

    @staticmethod
    def truncate_to_budget(text: str, max_tokens: int) -> str:
        """Truncates text to fit within the estimated token budget."""
        if not text:
            return ""
        max_chars = max_tokens * CHARS_PER_TOKEN
        if len(text) <= max_chars:
            return text
        return text[:max_chars] + " ... [Truncated by Context Budget]"

    @staticmethod
    def strip_uia_coordinates(text: str) -> str:
        """Removes UIA coordinate/bounding box data from text to reduce payload."""
        if not text:
            return ""
        # Remove patterns like: bbox: [x, y, w, h] or coordinates: (x, y, w, h)
        cleaned = re.sub(r"bbox:\s*\[[\d,\s]+\]", "", text)
        cleaned = re.sub(r"coordinates:\s*\([\d,\s]+\)", "", cleaned)
        cleaned = re.sub(r"\[\d+,\s*\d+,\s*\d+,\s*\d+\]", "", cleaned)
        # Remove control element list items with bounding box data
        cleaned = re.sub(r"^\s*\[\d+\]\s+.*?bbox:.*$", "", cleaned, flags=re.MULTILINE)
        # Clean up multiple blank lines
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        return cleaned.strip()

    @staticmethod
    def budget(task_type: str, compressed_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Applies dynamic budgeting to a pre-compressed context dictionary.
        
        Args:
            task_type: The classified task type (chat, coding, planning, etc.)
            compressed_context: Output from ContextCompressor.compress()
            
        Returns:
            A budgeted context dictionary with fields capped to the token budget.
        """
        budget_cap = BUDGET_CAPS.get(task_type, DEFAULT_BUDGET)
        
        budgeted = {
            "active_window": compressed_context.get("active_window", "Unknown Window"),
            "screen_summary": "",
            "relevant_memory": "",
            "project_context": "",
        }

        # Track remaining budget
        used_tokens = 0

        # Active window is always included (minimal cost)
        window_text = budgeted["active_window"]
        used_tokens += DynamicContextBudgeter.estimate_tokens(window_text)

        # --- Task-specific filtering strategies ---

        if task_type in ("chat", "vision"):
            # TIGHT BUDGET: Strip all UIA coordinates, cap everything aggressively
            screen_summary = compressed_context.get("screen_summary", "")
            if screen_summary:
                screen_summary = DynamicContextBudgeter.strip_uia_coordinates(screen_summary)
                max_screen = min(250, budget_cap - used_tokens)
                screen_summary = DynamicContextBudgeter.truncate_to_budget(screen_summary, max_screen)
                used_tokens += DynamicContextBudgeter.estimate_tokens(screen_summary)
                budgeted["screen_summary"] = screen_summary

            # Include only top memories if budget permits
            memory_text = compressed_context.get("relevant_memory", "")
            if memory_text:
                remaining = budget_cap - used_tokens
                if remaining > 100:
                    memory_text = DynamicContextBudgeter.truncate_to_budget(memory_text, min(200, remaining))
                    used_tokens += DynamicContextBudgeter.estimate_tokens(memory_text)
                    budgeted["relevant_memory"] = memory_text

            # Minimal project context
            proj_text = compressed_context.get("project_context", "")
            if proj_text:
                remaining = budget_cap - used_tokens
                if remaining > 50:
                    proj_text = DynamicContextBudgeter.truncate_to_budget(proj_text, min(150, remaining))
                    used_tokens += DynamicContextBudgeter.estimate_tokens(proj_text)
                    budgeted["project_context"] = proj_text

        elif task_type == "coding":
            # CODE BUDGET: Prioritize memories (which may contain code context),
            # omit screen summary and UIA data
            memory_text = compressed_context.get("relevant_memory", "")
            if memory_text:
                max_mem = min(1500, budget_cap - used_tokens)
                memory_text = DynamicContextBudgeter.truncate_to_budget(memory_text, max_mem)
                used_tokens += DynamicContextBudgeter.estimate_tokens(memory_text)
                budgeted["relevant_memory"] = memory_text

            # Include project context (may contain codebase info)
            proj_text = compressed_context.get("project_context", "")
            if proj_text:
                remaining = budget_cap - used_tokens
                if remaining > 100:
                    proj_text = DynamicContextBudgeter.truncate_to_budget(proj_text, min(800, remaining))
                    used_tokens += DynamicContextBudgeter.estimate_tokens(proj_text)
                    budgeted["project_context"] = proj_text

            # Screen summary stripped of coordinates for coding tasks
            screen_summary = compressed_context.get("screen_summary", "")
            if screen_summary:
                remaining = budget_cap - used_tokens
                if remaining > 100:
                    screen_summary = DynamicContextBudgeter.strip_uia_coordinates(screen_summary)
                    screen_summary = DynamicContextBudgeter.truncate_to_budget(screen_summary, min(400, remaining))
                    used_tokens += DynamicContextBudgeter.estimate_tokens(screen_summary)
                    budgeted["screen_summary"] = screen_summary

        elif task_type in ("planning", "automation"):
            # FULL BUDGET: Include everything, preserve UIA layout for automation
            screen_summary = compressed_context.get("screen_summary", "")
            if screen_summary:
                max_screen = min(1500, budget_cap - used_tokens)
                screen_summary = DynamicContextBudgeter.truncate_to_budget(screen_summary, max_screen)
                used_tokens += DynamicContextBudgeter.estimate_tokens(screen_summary)
                budgeted["screen_summary"] = screen_summary

            memory_text = compressed_context.get("relevant_memory", "")
            if memory_text:
                remaining = budget_cap - used_tokens
                if remaining > 100:
                    memory_text = DynamicContextBudgeter.truncate_to_budget(memory_text, min(1000, remaining))
                    used_tokens += DynamicContextBudgeter.estimate_tokens(memory_text)
                    budgeted["relevant_memory"] = memory_text

            proj_text = compressed_context.get("project_context", "")
            if proj_text:
                remaining = budget_cap - used_tokens
                if remaining > 100:
                    proj_text = DynamicContextBudgeter.truncate_to_budget(proj_text, min(1000, remaining))
                    used_tokens += DynamicContextBudgeter.estimate_tokens(proj_text)
                    budgeted["project_context"] = proj_text

        else:
            # MEMORY or unknown: Moderate budget, standard inclusion
            memory_text = compressed_context.get("relevant_memory", "")
            if memory_text:
                max_mem = min(600, budget_cap - used_tokens)
                memory_text = DynamicContextBudgeter.truncate_to_budget(memory_text, max_mem)
                used_tokens += DynamicContextBudgeter.estimate_tokens(memory_text)
                budgeted["relevant_memory"] = memory_text

            proj_text = compressed_context.get("project_context", "")
            if proj_text:
                remaining = budget_cap - used_tokens
                if remaining > 50:
                    proj_text = DynamicContextBudgeter.truncate_to_budget(proj_text, min(400, remaining))
                    used_tokens += DynamicContextBudgeter.estimate_tokens(proj_text)
                    budgeted["project_context"] = proj_text

        total_tokens = used_tokens
        log_debug(f"[CONTEXT BUDGET] Task: '{task_type}' | Cap: {budget_cap} | Used: {total_tokens} | {total_tokens/budget_cap*100:.1f}%")
        logger.info(f"Context budgeted for task '{task_type}': {total_tokens}/{budget_cap} tokens used")

        return budgeted
