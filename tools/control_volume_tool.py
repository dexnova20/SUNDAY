# c:\Users\mshas\OneDrive\Desktop\SUNDAY\tools\control_volume_tool.py
"""
Control Volume Tool for SUNDAY.
Simulates volumeup, volumedown, and volumemute keystrokes via pyautogui.
"""
import pyautogui
from tools.base_tool import BaseTool

class ControlVolumeTool(BaseTool):
    def __init__(self, default_action: str = None):
        super().__init__("adjust_volume", 1, "Adjusts the system volume level (up, down, or mute)")
        self.default_action = default_action

    def execute(self, parameters: dict, context: dict = None) -> dict:
        action = parameters.get("action", self.default_action)
        if not action or action == "adjust":
            action = "up"
        try:
            if action == "up": 
                pyautogui.press("volumeup")
            elif action == "down": 
                pyautogui.press("volumedown")
            elif action == "mute": 
                pyautogui.press("volumemute")
            else:
                return {"success": False, "message": f"Unknown volume action: '{action}'"}
            return {"success": True, "message": f"Volume command executed: '{action}'"}
        except Exception as e:
            return {"success": False, "message": f"Failed to execute volume adjustment: {str(e)}"}
