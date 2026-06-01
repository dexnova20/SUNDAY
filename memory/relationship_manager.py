# c:\Users\mshas\OneDrive\Desktop\SUNDAY\memory\relationship_manager.py
"""
Relationship Manager for SUNDAY.
Implements a graph-ready semantic relationship layer (Subject-Predicate-Object)
stored in data/relationships.json. Supports traversal queries and path tracking.
"""
import os
from datetime import datetime
from config.settings import BASE_DIR
from utils.file_utils import load_json, atomic_write_json

RELATIONSHIPS_PATH = os.path.join(BASE_DIR, "data", "relationships.json")

class RelationshipManager:
    @staticmethod
    def load_relationships() -> list:
        """Loads relationships graph from disk."""
        return load_json(RELATIONSHIPS_PATH, list)

    @staticmethod
    def save_relationships(data: list):
        """Atomically saves relationships to disk."""
        atomic_write_json(RELATIONSHIPS_PATH, data)

    @staticmethod
    def add_relationship(subject: str, predicate: str, obj: str, confidence: float = 1.0):
        """Adds a relationship triple to the graph, avoiding exact duplicates."""
        if not subject or not predicate or not obj:
            return

        graph = RelationshipManager.load_relationships()
        sub_clean = subject.strip()
        pred_clean = predicate.strip()
        obj_clean = obj.strip()
        now_str = datetime.now().isoformat()

        # Check for duplicate
        found = None
        for rel in graph:
            if rel.get("subject", "").lower() == sub_clean.lower() and \
               rel.get("predicate", "").lower() == pred_clean.lower() and \
               rel.get("object", "").lower() == obj_clean.lower():
                found = rel
                break

        if found:
            found["confidence"] = max(found.get("confidence", 0.5), confidence)
            found["last_updated"] = now_str
        else:
            new_rel = {
                "subject": sub_clean,
                "predicate": pred_clean,
                "object": obj_clean,
                "confidence": confidence,
                "created_at": now_str,
                "last_updated": now_str
            }
            graph.append(new_rel)

        RelationshipManager.save_relationships(graph)

    @staticmethod
    def get_relations_by_subject(sub: str) -> list:
        """Retrieves all triples matching a subject."""
        graph = RelationshipManager.load_relationships()
        sub_lower = sub.strip().lower()
        return [r for r in graph if r.get("subject", "").lower() == sub_lower]

    @staticmethod
    def get_relations_by_predicate(pred: str) -> list:
        """Retrieves all triples matching a predicate."""
        graph = RelationshipManager.load_relationships()
        pred_lower = pred.strip().lower()
        return [r for r in graph if r.get("predicate", "").lower() == pred_lower]

    @staticmethod
    def get_relations_by_object(obj: str) -> list:
        """Retrieves all triples matching an object."""
        graph = RelationshipManager.load_relationships()
        obj_lower = obj.strip().lower()
        return [r for r in graph if r.get("object", "").lower() == obj_lower]

    @staticmethod
    def traverse_path(start_node: str, path_predicates: list) -> list:
        """
        Traverses the relationship graph starting at start_node along the sequence of path_predicates.
        Returns a list of matching leaf object nodes.
        Example: traverse_path("User", ["studies_at", "location"]) -> ["Bhopal"] (if User studies_at VIT Bhopal and VIT Bhopal location Bhopal)
        """
        current_nodes = [start_node.strip().lower()]
        
        for predicate in path_predicates:
            next_nodes = []
            pred_lower = predicate.strip().lower()
            relationships = RelationshipManager.load_relationships()
            
            for node in current_nodes:
                for rel in relationships:
                    if rel.get("subject", "").lower() == node and rel.get("predicate", "").lower() == pred_lower:
                        next_nodes.append(rel.get("object").strip())
            
            if not next_nodes:
                return []
            current_nodes = [n.lower() for n in next_nodes]
            
        # Return final node values maintaining original casing
        return next_nodes
