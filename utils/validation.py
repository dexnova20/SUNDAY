# c:\Users\mshas\OneDrive\Desktop\SUNDAY\utils\validation.py
"""
Validation Utility Library for SUNDAY.
Provides robust checks for tool input parameters, coordinate boundaries, and Brain intent payloads.
"""
from typing import Dict, Any, Tuple

def validate_intent_payload(payload: Dict[str, Any]) -> bool:
    """
    Validates if an LLM-generated or rule-based intent conforms to standard schemas.
    Schema: { "intent": str, "parameters": dict, "is_complete": bool, "sensitivity": int }
    """
    if not isinstance(payload, dict):
        return False
        
    required_keys = {"intent"}
    if not required_keys.issubset(payload.keys()):
        return False
        
    # Ensure parameter and completion attributes are valid types
    if "parameters" in payload and not isinstance(payload["parameters"], dict):
        return False
    if "is_complete" in payload and not isinstance(payload["is_complete"], bool):
        return False
    if "sensitivity" in payload and not isinstance(payload["sensitivity"], int):
        return False
        
    return True

def validate_tool_parameters(intent: str, parameters: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validates that necessary parameter keys exist for specific operational tool intents.
    Returns: (is_valid: bool, error_message: str)
    """
    if not isinstance(parameters, dict):
        return False, "Parameters must be a dictionary"
        
    if intent in {"open_app"}:
        if not parameters.get("app_name"):
            return False, "Missing 'app_name' parameter"
            
    elif intent in {"open_website"}:
        if not parameters.get("site") and not parameters.get("url"):
            return False, "Missing 'site' or 'url' parameter"
            
    elif intent in {"search_web"}:
        if not parameters.get("query"):
            return False, "Missing 'query' parameter"
            
    elif intent in {"read_file"}:
        if not parameters.get("file_name") and not parameters.get("file_path"):
            return False, "Missing 'file_name' or 'file_path' parameter"
            
    elif intent in {"type_text"}:
        if not parameters.get("text"):
            return False, "Missing 'text' parameter"
            
    elif intent in {"play_media"}:
        if not parameters.get("title"):
            return False, "Missing media query 'title' parameter"
            
    elif intent in {"ocr_region"}:
        for coord in ["x", "y", "w", "h"]:
            if coord not in parameters:
                return False, f"Missing coordinate '{coord}' parameter for OCR"
            try:
                int(parameters[coord])
            except (ValueError, TypeError):
                return False, f"Coordinate '{coord}' parameter must be an integer"
                
    return True, ""

def validate_coordinates(x: int, y: int, w: int, h: int, max_w: int = 7680, max_h: int = 4320) -> bool:
    """
    Validates monitor coordinate rectangles, preventing out-of-bound errors.
    Protects automation loops from negative numbers or extreme coordinate limits.
    """
    try:
        x_val, y_val = int(x), int(y)
        w_val, h_val = int(w), int(h)
    except (ValueError, TypeError):
        return False
        
    if x_val < 0 or y_val < 0:
        return False
    if w_val <= 0 or h_val <= 0:
        return False
    if x_val + w_val > max_w or y_val + h_val > max_h:
        return False
        
    return True
