# c:\Users\mshas\OneDrive\Desktop\SUNDAY\brain\fact_extractor.py
"""
Fact and Preference Extractor for SUNDAY.
Performs pattern-based extraction using fast regular expressions
to detect profile facts and preferences without invoking the LLM.
"""
import re

class FactExtractor:
    # Pattern tuples: (compiled regex, field/category name, score)
    FACT_REGEXES = [
        (re.compile(r"\bmy name is\s+([a-zA-Z\s]+)", re.IGNORECASE), "name", 0.99),
        (re.compile(r"\bi study\s+([a-zA-Z\s\d\-\(\)]+)", re.IGNORECASE), "branch", 0.95),
        (re.compile(r"\bmy branch is\s+([a-zA-Z\s\d\-\(\)]+)", re.IGNORECASE), "branch", 0.95),
        (re.compile(r"\bmy college is\s+([a-zA-Z\s\d\-\(\)]+)", re.IGNORECASE), "college", 0.95),
        (re.compile(r"\bi work as a?\s*([a-zA-Z\s\d]+)", re.IGNORECASE), "occupation", 0.95),
        (re.compile(r"\bmy occupation is\s+([a-zA-Z\s\d]+)", re.IGNORECASE), "occupation", 0.95),
        (re.compile(r"\bi live in\s+([a-zA-Z\s\d,]+)", re.IGNORECASE), "location", 0.90),
        (re.compile(r"\bmy age is\s+(\d+)", re.IGNORECASE), "age", 0.95),
        (re.compile(r"\bi am\s+(\d+)\s+years?\s+old", re.IGNORECASE), "age", 0.95),
    ]

    PREF_REGEXES = [
        # Match response style preferences
        (re.compile(r"\bi prefer\s+([a-zA-Z]+)\s+(responses|answers|replies)", re.IGNORECASE), "response_style", 0.95),
        (re.compile(r"\bi prefer\s+(responses|answers|replies)\s+to\s+be\s+([a-zA-Z]+)", re.IGNORECASE), "response_style", 0.95),
        # Match interests
        (re.compile(r"\bi like\s+([a-zA-Z\s\d]+)", re.IGNORECASE), "interests", 0.85),
        (re.compile(r"\bi am interested in\s+([a-zA-Z\s\d]+)", re.IGNORECASE), "interests", 0.85),
        # Match preferred tools
        (re.compile(r"\bi prefer using\s+([a-zA-Z\s\d\.\:\-\_]+)", re.IGNORECASE), "preferred_tools", 0.90),
        (re.compile(r"\bmy preferred tool is\s+([a-zA-Z\s\d\.\:\-\_]+)", re.IGNORECASE), "preferred_tools", 0.90),
    ]

    @staticmethod
    def extract_facts(text: str) -> list:
        """
        Runs regex checks to extract profile facts from the input string.
        Returns a list of structured facts: [{"field": str, "value": str, "confidence": float}]
        """
        extracted = []
        for pattern, field, score in FactExtractor.FACT_REGEXES:
            match = pattern.search(text)
            if match:
                val = match.group(1).strip().rstrip(".!?,")
                if field == "name":
                    val = val.title()
                extracted.append({
                    "type": "fact",
                    "field": field,
                    "value": val,
                    "confidence": score
                })
        return extracted

    @staticmethod
    def extract_preferences(text: str) -> list:
        """
        Runs regex checks to extract preferences from the input string.
        Returns a list of structured preferences: [{"category": str, "value": str, "confidence": float}]
        """
        extracted = []
        for pattern, category, score in FactExtractor.PREF_REGEXES:
            match = pattern.search(text)
            if match:
                # Get the group containing the value
                # If there are multiple matching groups, pick the last non-empty one
                groups = [g for g in match.groups() if g]
                if category == "response_style":
                    # For response_style, pick the group matching concise/detailed/etc.
                    val = next((g for g in groups if g.lower() in ("concise", "detailed", "short", "long", "technical")), None)
                    if not val:
                        val = groups[0]
                else:
                    val = groups[0]
                
                val = val.strip().rstrip(".!?,")
                extracted.append({
                    "type": "preference",
                    "category": category,
                    "value": val,
                    "confidence": score
                })
        return extracted
