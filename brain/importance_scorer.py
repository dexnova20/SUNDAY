# c:\Users\mshas\OneDrive\Desktop\SUNDAY\brain\importance_scorer.py
"""
Importance Scorer for SUNDAY.
Evaluates every candidate memory and returns a score between 0.0 and 1.0.
Prevents memory pollution by enforcing a strict storage threshold (>= 0.75).
"""
import logging

class ImportanceScorer:
    THRESHOLD = 0.75

    @staticmethod
    def evaluate(candidate: dict) -> float:
        """
        Evaluates a candidate memory and returns its final importance score.
        candidate: {
            "type": "fact" / "preference" / "goal" / "knowledge" / "experience",
            "field" / "category" / "goal" / "topic" / "workflow": str,
            "value" / "content": str,
            "confidence" / "raw_score": float
        }
        """
        # Retrieve raw confidence/score (default to 0.5 if not provided)
        score = candidate.get("confidence", candidate.get("raw_score", 0.5))

        # 1. Clean and check the textual content
        val_str = str(candidate.get("value", candidate.get("content", candidate.get("goal", "")))).strip()
        val_lower = val_str.lower()

        # Extremely low value / conversational noise filter
        noise_words = {"hi", "hello", "hey", "yo", "thanks", "test", "ok", "okay", "bye", "goodbye"}
        if not val_str or val_lower in noise_words:
            return 0.01

        # 2. Rule-based boosts
        cand_type = candidate.get("type", "").lower()
        
        if cand_type == "fact":
            field = str(candidate.get("field", "")).lower()
            # Core personal facts receive maximum priority
            if field in ("name", "college", "branch", "occupation", "age", "location"):
                score = max(score, 0.95)
            else:
                score = max(score, 0.75)

        elif cand_type == "preference":
            cat = str(candidate.get("category", "")).lower()
            if cat in ("response_style", "interests", "preferred_tools", "preferred_workflow_patterns"):
                score = max(score, 0.90)
            else:
                score = max(score, 0.75)

        elif cand_type == "goal":
            score = max(score, 0.85)

        elif cand_type == "knowledge":
            topic = str(candidate.get("topic", "")).lower()
            # Explicit user requests like "remember this" trigger high scores
            if topic != "general_note":
                score = max(score, 0.80)
            else:
                score = max(score, 0.75)

        elif cand_type == "experience":
            score = max(score, 0.75)

        # Force bounds between 0.0 and 1.0
        return min(1.0, max(0.0, score))
