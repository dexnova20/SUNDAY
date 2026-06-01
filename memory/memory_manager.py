# c:\Users\mshas\OneDrive\Desktop\SUNDAY\memory\memory_manager.py
"""
Memory Manager for SUNDAY.
Handles factual knowledge saving, retrieval, and topic extraction using LLM.
"""
import requests
from datetime import datetime
from config.settings import OLLAMA_URL, MEMORY_PATH
from utils.file_utils import load_json, atomic_write_json

class MemoryManager:
    @staticmethod
    def _extract_topic(text: str, model: str) -> str:
        prompt = f"Extract a short 2-4 word topic title for the following text. Do not include any other words or punctuation.\n\nText: {text}"
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.0}
        }
        try:
            response = requests.post(
                OLLAMA_URL.rstrip('/') + "/api/generate",
                json=payload,
                timeout=15  # Don't hang forever if Ollama is slow
            )
            response.raise_for_status()
            topic = response.json().get("response", "").strip()
            # Clean up potential markdown formatting or quotes
            topic = topic.replace('"', '').replace("'", "").replace(".", "").strip()
            return topic if topic else "general_note"
        except Exception:
            return "general_note"

    @staticmethod
    def save_knowledge(content: str, model: str = "llama3.2:1b"):
        if not content:
            return
            
        file_path = MEMORY_PATH
        
        # Load existing memory dynamically via file_utils
        memory = load_json(file_path, list)
                    
        # Extract topic via Ollama using dynamic model
        topic = MemoryManager._extract_topic(content, model)
        
        new_entry = {
            "topic": topic,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        
        memory.append(new_entry)
        
        # Save back to file atomically
        atomic_write_json(file_path, memory)

    @staticmethod
    def recall_knowledge(topic: str) -> list:
        file_path = MEMORY_PATH
        memory = load_json(file_path, list)
                
        topic_lower = topic.strip().lower()
        # Find all entries where topic matches or partially matches
        matches = [entry for entry in memory if topic_lower in entry.get("topic", "").lower()]
        return matches

    @staticmethod
    def search_knowledge(query: str) -> list:
        file_path = MEMORY_PATH
        memory = load_json(file_path, list)
                
        query_lower = query.strip().lower()
        # Find entries where query is in content or topic
        matches = [
            entry for entry in memory 
            if query_lower in entry.get("content", "").lower() or query_lower in entry.get("topic", "").lower()
        ]
        return matches

    @staticmethod
    def relevance_search(query: str, limit: int = 3) -> list:
        """
        Retrieves the top N most relevant memory entries across structured memory stores:
        profile, preferences, goals, knowledge, and experiences.
        Uses exact keyword matching and token overlap to ensure that the retrieved memory is minimal
        and strictly matches the query intent (e.g. only injecting profile.name when asking about name).
        """
        from memory.profile_manager import ProfileManager
        from memory.preference_manager import PreferenceManager
        from memory.goal_manager import GoalManager
        from memory.knowledge_store import KnowledgeStore
        from memory.experience_store import ExperienceStore

        stop_words = {"what", "is", "my", "to", "the", "a", "an", "and", "or", "but", "in", "on", "at", "for", "with", "about", "how", "why", "do", "you", "know"}
        query_words = [w for w in query.strip().lower().split() if w not in stop_words]
        if not query_words:
            query_words = query.strip().lower().split()

        query_lower = query.strip().lower()
        scored_candidates = []
        now = datetime.now()

        # 1. Search Profile
        profile_raw = ProfileManager.load_profile()
        for field, item in profile_raw.items():
            if field == "last_updated" or not isinstance(item, dict):
                continue
            val = item.get("value", "")
            if not val:
                continue
            
            score = 0.0
            if field in query_words:
                score += 5.0
            if any(w in val.lower() for w in query_words):
                score += 3.0
            if field == "name" and any(w in query_lower for w in ("name", "who am i", "myself")):
                score += 5.0
            if field == "college" and any(w in query_lower for w in ("college", "study", "education")):
                score += 5.0
            if field == "branch" and any(w in query_lower for w in ("branch", "stream", "subject", "study")):
                score += 5.0
            if field == "occupation" and any(w in query_lower for w in ("work", "job", "occupation", "do for a living")):
                score += 5.0
            
            if score > 0:
                score *= item.get("confidence", 1.0)
                try:
                    last_acc = datetime.fromisoformat(item.get("last_accessed", now.isoformat()))
                    days_unaccessed = (now - last_acc).total_seconds() / 86400.0
                    score *= (1.0 / (1.0 + 0.01 * days_unaccessed))
                except Exception:
                    pass

                scored_candidates.append((
                    score,
                    {
                        "topic": f"profile.{field}",
                        "content": f"Your {field} is {val}.",
                        "timestamp": item.get("last_updated")
                    }
                ))

        # 2. Search Preferences
        prefs_raw = PreferenceManager.load_preferences()
        for cat, val_dict in prefs_raw.items():
            if not isinstance(val_dict, dict):
                continue
            for val_key, item in val_dict.items():
                val = item.get("value", "")
                if not val:
                    continue
                score = 0.0
                if cat in query_words:
                    score += 4.0
                if any(w in val.lower() for w in query_words):
                    score += 3.0
                if cat == "response_style" and any(w in query_lower for w in ("style", "responses", "answers", "write")):
                    score += 4.0
                if cat == "interests" and any(w in query_lower for w in ("interests", "like", "hobbies")):
                    score += 4.0

                if score > 0:
                    score *= item.get("confidence", 0.5)
                    try:
                        last_acc = datetime.fromisoformat(item.get("last_accessed", now.isoformat()))
                        days_unaccessed = (now - last_acc).total_seconds() / 86400.0
                        score *= (1.0 / (1.0 + 0.02 * days_unaccessed))
                    except Exception:
                        pass

                    scored_candidates.append((
                        score,
                        {
                            "topic": f"preference.{cat}",
                            "content": f"Preferred {cat.replace('_', ' ')}: {val}",
                            "timestamp": item.get("last_updated")
                        }
                    ))

        # 3. Search Goals
        goals_raw = GoalManager.load_goals()
        for g in goals_raw.get("active_goals", []):
            goal_text = g.get("goal", "")
            score = 0.0
            if any(w in query_lower for w in ("goal", "plan", "objective", "aim", "trying to")):
                score += 3.0
            if any(w in goal_text.lower() for w in query_words):
                score += 2.0
            
            if score > 0:
                score *= g.get("confidence", 0.8)
                try:
                    last_acc = datetime.fromisoformat(g.get("last_accessed", now.isoformat()))
                    days_unaccessed = (now - last_acc).total_seconds() / 86400.0
                    score *= (1.0 / (1.0 + 0.02 * days_unaccessed))
                except Exception:
                    pass

                scored_candidates.append((
                    score,
                    {
                        "topic": "goal.active",
                        "content": f"Active Goal: {goal_text}",
                        "timestamp": g.get("last_updated")
                    }
                ))

        # 4. Search Knowledge Store
        knowledge = KnowledgeStore.load_knowledge()
        for entry in knowledge:
            topic = entry.get("topic", "")
            content = entry.get("content", "")
            score = 0.0
            
            for w in query_words:
                if w in topic.lower():
                    score += 4.0
                if w in content.lower():
                    score += 1.5
                    
            for trip in entry.get("triples", []):
                if any(w in str(trip.get("subject")).lower() or w in str(trip.get("object")).lower() for w in query_words):
                    score += 2.5
            
            if score > 0:
                score *= entry.get("confidence", 0.95)
                try:
                    last_acc = datetime.fromisoformat(entry.get("last_accessed", now.isoformat()))
                    days_unaccessed = (now - last_acc).total_seconds() / 86400.0
                    score *= (1.0 / (1.0 + 0.01 * days_unaccessed))
                except Exception:
                    pass

                scored_candidates.append((
                    score,
                    {
                        "topic": f"knowledge.{topic}",
                        "content": content,
                        "timestamp": entry.get("last_updated")
                    }
                ))

        # 5. Search Experience Store
        experiences = ExperienceStore.load_experiences()
        for entry in experiences:
            wf = entry.get("workflow", "")
            score = 0.0
            if any(w in query_lower for w in ("workflow", "experience", "outcome", "success", "fail")):
                score += 2.0
            if any(w in wf.lower() for w in query_words):
                score += 3.0
                
            if score > 0:
                score *= entry.get("confidence", 1.0)
                scored_candidates.append((
                    score,
                    {
                        "topic": "experience.workflow",
                        "content": f"Workflow run: '{wf}', success={entry.get('success')}, confidence={entry.get('confidence')}",
                        "timestamp": entry.get("created_at")
                    }
                ))

        scored_candidates.sort(key=lambda x: x[0], reverse=True)

        selected = []
        seen_contents = set()
        for score, cand in scored_candidates:
            if cand["content"].lower() not in seen_contents:
                seen_contents.add(cand["content"].lower())
                selected.append(cand)
            if len(selected) >= limit:
                break
                
        return selected

    @staticmethod
    def memory_maintenance():
        """
        Cleans up memory database:
        1. Prunes empty/duplicate unstructured memory items.
        2. Merges similar user preferences.
        3. Runs memory aging/decay algorithms, archiving stale items.
        """
        now = datetime.now()
        
        # 1. Unstructured memory.json cleaning
        try:
            file_path = MEMORY_PATH
            memory = load_json(file_path, list)
            if memory and isinstance(memory, list):
                cleaned_memory = []
                seen_contents = set()
                for entry in memory:
                    if not isinstance(entry, dict):
                        continue
                    topic = entry.get("topic", "").strip()
                    content = entry.get("content", "").strip()
                    timestamp = entry.get("timestamp", "").strip()
                    if not content or not topic or not timestamp:
                        continue
                    content_lower = content.lower()
                    if content_lower in seen_contents:
                        continue
                    seen_contents.add(content_lower)
                    cleaned_memory.append(entry)
                if len(cleaned_memory) != len(memory):
                    atomic_write_json(file_path, cleaned_memory)
        except Exception:
            pass

        # 2. Preferences aging, cleaning & merging similar preferences
        try:
            from memory.preference_manager import PreferenceManager
            prefs = PreferenceManager.load_preferences()
            prefs_updated = False

            for cat in list(prefs.keys()):
                cat_data = prefs[cat]
                if not isinstance(cat_data, dict):
                    continue

                merged_data = {}
                for k, item in list(cat_data.items()):
                    val = item.get("value", "").strip()
                    if not val:
                        continue
                    val_lower = val.lower()
                    
                    if "concise" in val_lower or "short" in val_lower:
                        key = "concise"
                        val = "concise"
                    elif "detailed" in val_lower or "verbose" in val_lower:
                        key = "detailed"
                        val = "detailed"
                    else:
                        key = val_lower

                    if key not in merged_data:
                        merged_data[key] = {
                            "value": val,
                            "count": item.get("count", 1),
                            "confidence": item.get("confidence", 0.5),
                            "created_at": item.get("created_at", now.isoformat()),
                            "last_updated": item.get("last_updated", now.isoformat()),
                            "last_accessed": item.get("last_accessed", now.isoformat())
                        }
                    else:
                        merged_data[key]["count"] += item.get("count", 1)
                        merged_data[key]["confidence"] = min(1.0, merged_data[key]["confidence"] + 0.1)
                        if item.get("last_updated", "") > merged_data[key]["last_updated"]:
                            merged_data[key]["last_updated"] = item.get("last_updated")
                        if item.get("last_accessed", "") > merged_data[key]["last_accessed"]:
                            merged_data[key]["last_accessed"] = item.get("last_accessed")

                cleaned_cat = {}
                for key, item in merged_data.items():
                    try:
                        last_acc = datetime.fromisoformat(item.get("last_accessed", now.isoformat()))
                        days_unaccessed = (now - last_acc).days
                        
                        if days_unaccessed >= 15:
                            decay_multiplier = 0.9 ** (days_unaccessed // 15)
                            item["confidence"] = max(0.0, item["confidence"] * decay_multiplier)
                            prefs_updated = True
                            
                        if item["confidence"] < 0.4:
                            from utils.logger import log_debug
                            log_debug(f"[MEMORY MAINTENANCE] Archiving stale preference '{cat}.{key}' (confidence={item['confidence']:.2f})")
                            continue
                    except Exception:
                        pass
                    cleaned_cat[key] = item

                if len(cleaned_cat) != len(cat_data) or prefs_updated:
                    prefs[cat] = cleaned_cat
                    prefs_updated = True

            if prefs_updated:
                PreferenceManager.save_preferences(prefs)
        except Exception as e:
            from utils.logger import log_debug
            log_debug(f"[MEMORY MAINTENANCE] Error cleaning preferences: {e}")

        # 3. Goals, Knowledge, Profile checks
        try:
            from memory.goal_manager import GoalManager
            goals = GoalManager.load_goals()
            goals_updated = False
            
            cleaned_active = []
            for g in goals.get("active_goals", []):
                try:
                    last_acc = datetime.fromisoformat(g.get("last_accessed", now.isoformat()))
                    days_unaccessed = (now - last_acc).days
                    if days_unaccessed >= 30:
                        decay_multiplier = 0.95 ** (days_unaccessed // 30)
                        g["confidence"] = max(0.0, g.get("confidence", 0.9) * decay_multiplier)
                        goals_updated = True
                        
                    if g.get("confidence", 0.9) < 0.4:
                        g["abandoned_at"] = now.isoformat()
                        goals["abandoned_goals"].append(g)
                        goals_updated = True
                        from utils.logger import log_debug
                        log_debug(f"[MEMORY MAINTENANCE] Goal abandoned due to inactivity decay: '{g.get('goal')}'")
                        continue
                except Exception:
                    pass
                cleaned_active.append(g)
                
            if len(cleaned_active) != len(goals["active_goals"]) or goals_updated:
                goals["active_goals"] = cleaned_active
                GoalManager.save_goals(goals)
        except Exception:
            pass

