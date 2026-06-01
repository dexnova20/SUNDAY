import json
import os
import requests
from datetime import datetime

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
                "http://localhost:11434/api/generate",
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
            
        file_path = os.path.join(os.path.dirname(__file__), "memory.json")
        memory = []
        
        # Load existing memory if it exists
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                try:
                    memory = json.load(f)
                except json.JSONDecodeError:
                    pass
                    
        # Extract topic via Ollama using dynamic model
        topic = MemoryManager._extract_topic(content, model)
        
        new_entry = {
            "topic": topic,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        
        memory.append(new_entry)
        
        # Save back to file
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(memory, f, indent=4)

    @staticmethod
    def recall_knowledge(topic: str) -> list:
        file_path = os.path.join(os.path.dirname(__file__), "memory.json")
        if not os.path.exists(file_path):
            return []
            
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                memory = json.load(f)
            except json.JSONDecodeError:
                return []
                
        topic_lower = topic.strip().lower()
        # Find all entries where topic matches or partially matches
        matches = [entry for entry in memory if topic_lower in entry.get("topic", "").lower()]
        return matches

    @staticmethod
    def search_knowledge(query: str) -> list:
        file_path = os.path.join(os.path.dirname(__file__), "memory.json")
        if not os.path.exists(file_path):
            return []
            
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                memory = json.load(f)
            except json.JSONDecodeError:
                return []
                
        query_lower = query.strip().lower()
        # Find entries where query is in content or topic
        matches = [
            entry for entry in memory 
            if query_lower in entry.get("content", "").lower() or query_lower in entry.get("topic", "").lower()
        ]
        return matches

