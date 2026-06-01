# c:\Users\mshas\OneDrive\Desktop\SUNDAY\tools\type_text_tool.py
"""
Type Text Tool for SUNDAY.
Types string text via clipboard copy-pasting pyautogui simulations.
"""
import pyautogui
import pyperclip
from tools.base_tool import BaseTool
from interface.console_output import display_response

class TypeTextTool(BaseTool):
    def __init__(self):
        super().__init__("type_text", 2, "Types text in the active window by mimicking clipboard copy and paste commands")

    def execute(self, parameters: dict, context: dict = None) -> dict:
        text = parameters.get("text", "")
        if not text:
            return {"success": False, "message": "No text content provided to type"}
        try:
            display_response("Typing in two seconds...")
            import time
            time.sleep(2) # Give user time to focus correct window
            
            pyperclip.copy(text)
            pyautogui.hotkey("ctrl", "v")
            return {"success": True, "message": "Successfully typed text via clipboard paste"}
        except Exception as e:
            return {"success": False, "message": f"Typing action failed: {str(e)}"}
