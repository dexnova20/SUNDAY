# c:\Users\mshas\OneDrive\Desktop\SUNDAY\brain\context_compressor.py
"""
Context Compression Layer for SUNDAY.
Optimizes prompt size by deduplicating command histories, restricting memory injections
to top 3 relevant matches, truncating massive screen lists, and weeding out empty session variables.
"""
import re
import json
import logging
from typing import Dict, Any, Optional
from memory.memory_manager import MemoryManager

logger = logging.getLogger("CONTEXT_COMPRESSOR")

class ContextCompressor:
    @staticmethod
    def compress(query: str, raw_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Compresses and optimizes raw prompt context:
        - Keeps active window name if present.
        - Limits memory injection to the top 3 most relevant recency-weighted entries.
        - Truncates and summarizes screen texts to avoid prompt token overhead.
        - Deduplicates rolling history items and removes empty/stale parameters.
        """
        compressed = {
            "active_window": "Unknown Window",
            "screen_summary": "",
            "relevant_memory": "",
            "project_context": ""
        }
        
        if not raw_context:
            return compressed
            
        # 1. Active Window Pruning
        active_window = raw_context.get("active_window", "Unknown Window")
        if active_window and active_window != "Unknown Window":
            compressed["active_window"] = active_window

        # 2. Smart Memory Relevance Search (Top 3 Recency-Weighted Entries)
        try:
            relevant_entries = MemoryManager.relevance_search(query, limit=3)
            if relevant_entries:
                mem_blocks = []
                for entry in relevant_entries:
                    mem_blocks.append(f"- [{entry.get('topic', 'note')}]: {entry.get('content')}")
                compressed["relevant_memory"] = "\n".join(mem_blocks)
        except Exception as e:
            logger.warning(f"Memory relevance search failed: {e}")

        # 3. Trim Large Visual Screen Text
        screen_text = raw_context.get("screen_text", "")
        if screen_text:
            # Enforce dynamic truncation limit of 400 characters to keep it speed-optimal
            if len(screen_text) > 400:
                compressed["screen_summary"] = screen_text[:400] + " ... [Context Pruned for Performance]"
            else:
                compressed["screen_summary"] = screen_text

        # 4. Remove Stale Session Data & Deduplicate Rolling History
        project_mem = raw_context.get("project_memory", "")
        if project_mem:
            # Parse formatting like: "[PROJECT: X] [GOAL: Y] [ACTIVE TASKS: Z] [RECENT HISTORY: H]"
            history_match = re.search(r"\[RECENT HISTORY:\s*(.*?)\]", project_mem)
            clean_history = ""
            if history_match:
                history_items = [h.strip() for h in history_match.group(1).split("->")]
                # Deduplicate history sequentially while maintaining chronological ordering
                seen = set()
                deduped_history = []
                for item in history_items:
                    if item not in seen and item != "None" and item != "":
                        seen.add(item)
                        deduped_history.append(item)
                # Keep history capped strictly to the last 5 interactions (Phase 4 session cap)
                clean_history = " -> ".join(deduped_history[-5:]) if deduped_history else "None"
            
            proj_match = re.search(r"\[PROJECT:\s*(.*?)\]", project_mem)
            goal_match = re.search(r"\[GOAL:\s*(.*?)\]", project_mem)
            tasks_match = re.search(r"\[ACTIVE TASKS:\s*(.*?)\]", project_mem)
            
            proj = proj_match.group(1).strip() if proj_match else "None"
            goal = goal_match.group(1).strip() if goal_match else "None"
            tasks = tasks_match.group(1).strip() if tasks_match else "None"
            
            parts = []
            if proj and proj != "None":
                parts.append(f"Project: {proj}")
            if goal and goal != "None":
                parts.append(f"Goal: {goal}")
            if tasks and tasks != "None":
                parts.append(f"Active Tasks: {tasks}")
            if clean_history and clean_history != "None":
                parts.append(f"Recent History: {clean_history}")
                
            compressed["project_context"] = " | ".join(parts) if parts else ""
            
        return compressed
