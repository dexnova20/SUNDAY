# c:\Users\mshas\OneDrive\Desktop\SUNDAY\memory\knowledge_store.py
"""
Knowledge Store for SUNDAY.
Stores explicitly taught user information.
Supports semantic triples (Subject-Predicate-Object) for future knowledge graph integration.
"""
import os
from datetime import datetime
from config.settings import BASE_DIR
from utils.file_utils import load_json, atomic_write_json

KNOWLEDGE_PATH = os.path.join(BASE_DIR, "data", "knowledge.json")

class KnowledgeStore:
    @staticmethod
    def load_knowledge() -> list:
        """Loads knowledge list from disk."""
        return load_json(KNOWLEDGE_PATH, list)

    @staticmethod
    def save_knowledge(data: list):
        """Atomically saves knowledge list to disk."""
        atomic_write_json(KNOWLEDGE_PATH, data)

    @staticmethod
    def add_knowledge(topic: str, content: str, confidence: float = 0.95, triples: list = None):
        """
        Stores explicitly taught knowledge.
        Prevents exact topic duplicates, merging or updating them.
        """
        if not topic or not content:
            return

        knowledge = KnowledgeStore.load_knowledge()
        topic_clean = topic.strip()
        content_clean = content.strip()
        now_str = datetime.now().isoformat()

        # Simple semantic triples builder for graph-readiness if not supplied
        if not triples:
            triples = []
            # Extract simple relations if possible
            if " is " in content_clean:
                parts = content_clean.split(" is ", 1)
                triples.append({
                    "subject": parts[0].strip(),
                    "predicate": "is",
                    "object": parts[1].strip().rstrip("."),
                    "confidence": confidence
                })

        found = None
        for entry in knowledge:
            if entry.get("topic", "").lower() == topic_clean.lower():
                found = entry
                break

        if found:
            old_content = found.get("content")
            found["content"] = content_clean
            found["confidence"] = max(found.get("confidence", 0.5), confidence)
            found["last_updated"] = now_str
            found["last_accessed"] = now_str
            # Merge triples
            existing_triples = found.get("triples", [])
            for trip in triples:
                if not any(t.get("subject") == trip.get("subject") and t.get("predicate") == trip.get("predicate") and t.get("object") == trip.get("object") for t in existing_triples):
                    existing_triples.append(trip)
            found["triples"] = existing_triples
            
            from brain.learning_engine import LearningTelemetry
            LearningTelemetry.log(f"[MEMORY UPDATED] Knowledge topic '{topic_clean}': '{old_content}' -> '{content_clean}'")
        else:
            new_entry = {
                "topic": topic_clean,
                "content": content_clean,
                "confidence": confidence,
                "created_at": now_str,
                "last_updated": now_str,
                "last_accessed": now_str,
                "triples": triples
            }
            knowledge.append(new_entry)
            from brain.learning_engine import LearningTelemetry
            LearningTelemetry.log(f"[MEMORY STORED] Knowledge topic '{topic_clean}': '{content_clean}'")

        # Synchronize relationship graph with extracted triples
        try:
            from memory.relationship_manager import RelationshipManager
            for trip in triples:
                RelationshipManager.add_relationship(
                    trip.get("subject", topic_clean),
                    trip.get("predicate", "info"),
                    trip.get("object", content_clean),
                    confidence=trip.get("confidence", confidence)
                )
        except Exception:
            pass

        KnowledgeStore.save_knowledge(knowledge)

    @staticmethod
    def recall_knowledge(topic: str) -> list:
        """Recalls knowledge matching topic, updating last accessed time."""
        knowledge = KnowledgeStore.load_knowledge()
        topic_lower = topic.strip().lower()
        now_str = datetime.now().isoformat()
        matches = []
        
        for entry in knowledge:
            if topic_lower in entry.get("topic", "").lower():
                entry["last_accessed"] = now_str
                matches.append(entry)
                
        if matches:
            KnowledgeStore.save_knowledge(knowledge)
        return matches

    @staticmethod
    def search_knowledge(query: str) -> list:
        """Searches knowledge entries matching content, topic, or triples."""
        knowledge = KnowledgeStore.load_knowledge()
        query_lower = query.strip().lower()
        now_str = datetime.now().isoformat()
        matches = []
        
        for entry in knowledge:
            in_content = query_lower in entry.get("content", "").lower()
            in_topic = query_lower in entry.get("topic", "").lower()
            in_triples = False
            for trip in entry.get("triples", []):
                if query_lower in trip.get("subject", "").lower() or query_lower in trip.get("object", "").lower() or query_lower in trip.get("predicate", "").lower():
                    in_triples = True
                    break
                    
            if in_content or in_topic or in_triples:
                entry["last_accessed"] = now_str
                matches.append(entry)
                
        if matches:
            KnowledgeStore.save_knowledge(knowledge)
        return matches
