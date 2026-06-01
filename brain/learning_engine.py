# c:\Users\mshas\OneDrive\Desktop\SUNDAY\brain\learning_engine.py
"""
Learning Engine for SUNDAY.
Evaluates user messages to extract facts, preferences, goals, and knowledge.
Utilizes fast pre-filtering and rule-based extraction to avoid Ollama calls,
falling back to LLM processing only for ambiguous or complex learning statements.
"""
import re
import json
import requests
from config.settings import OLLAMA_URL
from utils.logger import log_debug
from brain.fact_extractor import FactExtractor
from brain.importance_scorer import ImportanceScorer
from memory.profile_manager import ProfileManager
from memory.preference_manager import PreferenceManager
from memory.goal_manager import GoalManager
from memory.knowledge_store import KnowledgeStore
from memory.experience_store import ExperienceStore

# Triggers indicating the message may contain learnable information
LEARNING_TRIGGERS = [
    # Facts triggers
    "name is", "i study", "my college", "my branch", "i live", "my age", "my occupation", "i work as", "i am a ", "i am an ",
    # Preferences triggers
    "i prefer", "i like", "i love", "my preference", "interests", "response style", "don't like", "dislike",
    # Goals triggers
    "i want to", "i plan to", "my goal is", "trying to achieve", "objective is", "aim to", "i want a",
    # Knowledge triggers
    "remember this", "note that", "store this", "remember that", "write down that",
    # Experiences triggers
    "workflow", "success", "failed", "worked", "did not work", "outreach", "proposal"
]

class LearningEngine:
    @staticmethod
    def process_message(text: str, model: str = "llama3.2:1b"):
        """
        Main pipeline.
        1. Pre-filter keywords (return in <1ms if no trigger).
        2. Fast rule-based extraction. If match, store and return without LLM.
        3. Fallback to Ollama LLM call ONLY for ambiguous/complex learning triggers.
        """
        text_lower = text.lower().strip()

        # Phase 1: Pre-filter keywords to avoid checking clean text or LLM calls entirely
        has_trigger = any(t in text_lower for t in LEARNING_TRIGGERS)
        if not has_trigger:
            return

        LearningTelemetry.log(f"[LEARNING] Evaluating message for learning triggers: '{text}'")

        # Phase 2: Fast Rule-based Extraction (No LLM call)
        regex_facts = FactExtractor.extract_facts(text)
        regex_prefs = FactExtractor.extract_preferences(text)
        
        rule_stored = False

        # Process facts found by regex
        for fact in regex_facts:
            score = ImportanceScorer.evaluate(fact)
            if score >= ImportanceScorer.THRESHOLD:
                # Log telemetry
                LearningTelemetry.log(f"[FACT DETECTED] field='{fact['field']}', value='{fact['value']}' (regex)")
                ProfileManager.update_profile(fact["field"], fact["value"], confidence=score)
                rule_stored = True

        # Process preferences found by regex
        for pref in regex_prefs:
            score = ImportanceScorer.evaluate(pref)
            if score >= ImportanceScorer.THRESHOLD:
                LearningTelemetry.log(f"[PREFERENCE DETECTED] category='{pref['category']}', value='{pref['value']}' (regex)")
                PreferenceManager.add_preference(pref["category"], pref["value"], weight=0.2)
                rule_stored = True

        # If rule-based extraction successfully handled the statement, we exit.
        # This completely prevents Ollama calls for standard profile facts & preferences!
        if rule_stored:
            LearningTelemetry.log("[LEARNING] Stored successfully via rule-based extraction. Skipping LLM call.")
            return

        # Phase 3: Ollama Fallback for Ambiguous or Complex Statements
        # Let's verify if the statement is complex enough to merit an LLM call.
        # Avoid LLM calls for very short statements or questions
        if len(text_lower.split()) < 4 or "?" in text_lower:
            return

        LearningTelemetry.log("[LEARNING] Ambiguous or complex statement detected. Triggering Ollama fallback...")

        prompt = f"""You are a cognitive memory extractor for a personal AI named SUNDAY.
Analyze the user's message and extract any new or updated:
1. Facts: structured profile fields (name, college, branch, occupation, age, location).
2. Preferences: response style, interests (e.g. fitness, coding), preferred tools, preferred workflow patterns.
3. Goals: long-term user objectives.
4. Knowledge: specific information the user explicitly tells you to remember/note/store.
5. Experiences: outcomes of workflows or actions if mentioned.

For each item, assign an importance score between 0.0 and 1.0:
- Casual talk/greetings: 0.01 - 0.1
- Important preferences/goals: 0.8 - 0.95
- Core personal facts: 0.9 - 1.0

User message: "{text}"

Output strictly valid JSON only matching this schema:
{{
  "facts": [
    {{"field": "name/college/branch/occupation/age/location/etc", "value": "extracted value", "importance": 0.99}}
  ],
  "preferences": [
    {{"category": "response_style/interests/preferred_tools/preferred_workflow_patterns", "value": "extracted value", "importance": 0.95}}
  ],
  "goals": [
    {{"goal": "extracted goal text", "importance": 0.90}}
  ],
  "knowledge": [
    {{"topic": "extracted short topic name", "content": "extracted content to store", "importance": 0.85}}
  ],
  "experiences": [
    {{"workflow": "name of workflow", "success": true/false, "confidence": 0.92, "importance": 0.80}}
  ]
}}
Do NOT wrap the output in markdown codeblocks. Do NOT add extra conversational text."""

        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.0,
                "num_predict": 300
            }
        }

        try:
            response = requests.post(
                OLLAMA_URL.rstrip('/') + "/api/generate",
                json=payload,
                timeout=10
            )
            if response.status_code == 200:
                raw_response = response.json().get("response", "").strip()
                
                # Parse JSON, cleaning markdown blocks
                clean_text = raw_response
                code_block_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", clean_text, re.DOTALL)
                if code_block_match:
                    clean_text = code_block_match.group(1).strip()
                else:
                    start = clean_text.find('{')
                    end = clean_text.rfind('}') + 1
                    if start != -1 and end > start:
                        clean_text = clean_text[start:end].strip()

                data = json.loads(clean_text)

                # Process LLM Facts
                for f in data.get("facts", []):
                    field = f.get("field")
                    value = f.get("value")
                    importance = f.get("importance", 0.5)
                    if not field or not value:
                        continue
                    
                    candidate = {
                        "type": "fact",
                        "field": field,
                        "value": value,
                        "raw_score": importance
                    }
                    score = ImportanceScorer.evaluate(candidate)
                    if score >= ImportanceScorer.THRESHOLD:
                        LearningTelemetry.log(f"[FACT DETECTED] field='{field}', value='{value}'")
                        ProfileManager.update_profile(field, value, confidence=score)

                # Process LLM Preferences
                for p in data.get("preferences", []):
                    cat = p.get("category")
                    val = p.get("value")
                    importance = p.get("importance", 0.5)
                    if not cat or not val:
                        continue

                    # Normalize categories
                    cat_clean = cat.strip().lower()
                    if "style" in cat_clean:
                        cat_clean = "response_style"
                    elif "interest" in cat_clean:
                        cat_clean = "interests"
                    elif "tool" in cat_clean:
                        cat_clean = "preferred_tools"
                    elif "workflow" in cat_clean:
                        cat_clean = "preferred_workflow_patterns"
                    else:
                        continue

                    candidate = {
                        "type": "preference",
                        "category": cat_clean,
                        "value": val,
                        "raw_score": importance
                    }
                    score = ImportanceScorer.evaluate(candidate)
                    if score >= ImportanceScorer.THRESHOLD:
                        LearningTelemetry.log(f"[PREFERENCE DETECTED] category='{cat_clean}', value='{val}'")
                        PreferenceManager.add_preference(cat_clean, val, weight=0.2)

                # Process LLM Goals
                for g in data.get("goals", []):
                    goal_text = g.get("goal")
                    importance = g.get("importance", 0.5)
                    if not goal_text:
                        continue
                    candidate = {
                        "type": "goal",
                        "goal": goal_text,
                        "raw_score": importance
                    }
                    score = ImportanceScorer.evaluate(candidate)
                    if score >= ImportanceScorer.THRESHOLD:
                        LearningTelemetry.log(f"[GOAL DETECTED] goal='{goal_text}'")
                        GoalManager.add_goal(goal_text, confidence=score)

                # Process LLM Knowledge
                for k in data.get("knowledge", []):
                    topic = k.get("topic")
                    content = k.get("content")
                    importance = k.get("importance", 0.5)
                    if not topic or not content:
                        continue
                    candidate = {
                        "type": "knowledge",
                        "topic": topic,
                        "content": content,
                        "raw_score": importance
                    }
                    score = ImportanceScorer.evaluate(candidate)
                    if score >= ImportanceScorer.THRESHOLD:
                        KnowledgeStore.add_knowledge(topic, content, confidence=score)

                # Process LLM Experiences
                for e in data.get("experiences", []):
                    workflow = e.get("workflow")
                    success = e.get("success", True)
                    confidence = e.get("confidence", 1.0)
                    importance = e.get("importance", 0.5)
                    if not workflow:
                        continue
                    candidate = {
                        "type": "experience",
                        "workflow": workflow,
                        "raw_score": importance
                    }
                    score = ImportanceScorer.evaluate(candidate)
                    if score >= ImportanceScorer.THRESHOLD:
                        ExperienceStore.add_experience(workflow, success, confidence=confidence)

        except Exception as e:
            log_debug(f"[LEARNING] Ollama learning exception: {e}")

class LearningTelemetry:
    @staticmethod
    def log(message: str):
        """Prints learning logs only in debug mode, always saving to filesystem."""
        from utils.logger import get_log_level, get_system_logger
        if get_log_level() >= 2:
            print(message)
        get_system_logger().info(message)
        
# Import FactExtractor here to ensure clean registration
from brain.fact_extractor import FactExtractor
