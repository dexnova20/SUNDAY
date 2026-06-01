# c:\Users\mshas\OneDrive\Desktop\SUNDAY\tools\take_screenshot_tool.py
"""
Take Screenshot Tool for SUNDAY.
Captures the primary display screen using pyautogui and exports to Desktop.
"""
import os
import pyautogui
from datetime import datetime
from tools.base_tool import BaseTool
from interface.console_output import display_response
from config.settings import SCREENSHOT_PATH

class TakeScreenshotTool(BaseTool):
    def __init__(self):
        super().__init__("take_screenshot", 1, "Captures a full screenshot of the primary monitor and saves to Desktop")

    def execute(self, parameters: dict, context: dict = None) -> dict:
        try:
            filename = f"SUNDAY_Screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            filepath = os.path.join(SCREENSHOT_PATH, filename)
            pyautogui.screenshot(filepath)
            
            if os.path.exists(filepath):
                display_response("Screenshot saved to your desktop.")
                return {"success": True, "message": f"Screenshot saved successfully at {filepath}"}
            else:
                return {"success": False, "message": "Screenshot file was not created"}
        except Exception as e:
            return {"success": False, "message": f"Failed to capture screenshot: {str(e)}"}
