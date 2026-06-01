# c:\Users\mshas\OneDrive\Desktop\SUNDAY\tools\mouse_tool.py
"""
Mouse Tracker Tool for SUNDAY.
Returns screen coordinates and window-relative coordinates for cursor tracking.
"""
import pyautogui
from tools.base_tool import BaseTool
from vision.vision_engine import VisionSession

class MouseTool(BaseTool):
    def __init__(self):
        super().__init__("mouse_tracker", 1, "Returns active screen cursor coordinates and relative window offsets")

    def execute(self, parameters: dict, context: dict = None) -> dict:
        try:
            # 1. Fetch screen cursor coordinates
            mouse_x, mouse_y = pyautogui.position()
            
            # 2. Query active window bounds from the VisionSession Cache
            session = VisionSession.get_instance()
            if not session:
                session = VisionSession()
                
            cached_context = session.get_context()
            win_bounds = cached_context.get("window", {}).get("bounds", [0, 0, 1920, 1080])
            
            # Calculate window-relative cursor coordinates
            rel_x = mouse_x - win_bounds[0]
            rel_y = mouse_y - win_bounds[1]
            
            msg = f"Mouse:\nScreen: ({mouse_x}, {mouse_y})\nWindow Relative: ({rel_x}, {rel_y})"
            
            return {
                "success": True,
                "message": msg,
                "data": {
                    "screen": [mouse_x, mouse_y],
                    "relative": [rel_x, rel_y]
                }
            }
        except Exception as e:
            return {"success": False, "message": f"Failed to track cursor position: {str(e)}"}
