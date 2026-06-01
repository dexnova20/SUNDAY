# c:\Users\mshas\OneDrive\Desktop\SUNDAY\tools\control_media_tool.py
"""
Control Media Tool for SUNDAY.
Triggers media playback hotkeys (play, pause, next, previous) via pyautogui.
"""
import pyautogui
from tools.base_tool import BaseTool

class ControlMediaTool(BaseTool):
    def __init__(self, action: str):
        super().__init__("control_media", 1, f"Triggers media playback hotkeys: {action}")
        self.action = action

    def execute(self, parameters: dict, context: dict = None) -> dict:
        try:
            pyautogui.press(self.action)
            return {"success": True, "message": f"Media command executed: '{self.action}'"}
        except Exception as e:
            return {"success": False, "message": f"Failed to execute media control: {str(e)}"}
