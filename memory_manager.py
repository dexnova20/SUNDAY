import json
import os
import requests
from datetime import datetime

class MemoryManager:
    @staticmethod
    def _extract_topic(text: str) -> str:
        prompt = f"Extract a short 2-4 word topic title for the following text. Do not include any other words or punctuation.\n\nText: {text}"
        payload = {
            "model": "llama3.2",
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
            return topic if topic else "general_note"
        except Exception:
            return "general_note"

    @staticmethod
    def save_knowledge(content: str):
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
                    
        # Extract topic via Ollama
        topic = MemoryManager._extract_topic(content)
        
        new_entry = {
            "topic": topic,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        
        memory.append(new_entry)
        
        # Save back to file
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(memory, f, indent=4)
