# c:\Users\mshas\OneDrive\Desktop\SUNDAY\tools\window_screenshot_tool.py
"""
Window Screenshot Tool for SUNDAY.
Takes a window-aware cropped screenshot of a specific target window.
"""
from tools.base_tool import BaseTool

class WindowScreenshotTool(BaseTool):
    def __init__(self, vision_session):
        super().__init__("window_screenshot", 1, "Takes a window-aware cropped screenshot of a specific target window")
        self.vision_session = vision_session

    def execute(self, parameters: dict, context: dict = None) -> dict:
        try:
            title = parameters.get("title", "")
            filepath = self.vision_session.capture_window_screenshot(title if title else None)
            return {
                "success": True, 
                "message": f"Successfully captured window screenshot saved to {filepath}",
                "filepath": filepath
            }
        except Exception as e:
            return {"success": False, "message": f"Window screenshot failed: {str(e)}"}
