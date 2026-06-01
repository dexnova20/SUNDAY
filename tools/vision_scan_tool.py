# c:\Users\mshas\OneDrive\Desktop\SUNDAY\tools\vision_scan_tool.py
"""
Vision Scan Tool for SUNDAY.
Performs an on-demand screen layout and focused UIA element context scan.
"""
from tools.base_tool import BaseTool
from vision.ui_context import UIContextExtractor
from utils.constants import BLACKLISTED_APPS

class VisionScanTool(BaseTool):
    def __init__(self, vision_session):
        super().__init__("vision_scan", 1, "Performs an on-demand screen layout and focused UIA element context scan")
        self.vision_session = vision_session

    def execute(self, parameters: dict, context: dict = None) -> dict:
        try:
            extractor = UIContextExtractor()
            ui_data = extractor.extract_active_window()
            
            # Check blacklist titles
            app_name = ui_data.get("app_name", "")
            if app_name in BLACKLISTED_APPS:
                return {"success": False, "message": f"Scan aborted: active application '{app_name}' is blacklisted"}
                
            summary = self.vision_session._summarize_ui(ui_data)
            
            # Cache it in the session singleton
            self.vision_session.context = {
                "app": app_name,
                "title": ui_data.get("window_title", ""),
                "mouse": ui_data.get("mouse_position", [0, 0]),
                "summary": summary,
                "important_text": ui_data.get("important_text", ""),
                "elements": ui_data.get("elements", [])
            }
            
            return {
                "success": True, 
                "message": f"Successfully completed spatial screen scan on '{self.vision_session.context['title']}'",
                "data": self.vision_session.context
            }
        except Exception as e:
            return {"success": False, "message": f"Vision scan failed: {str(e)}"}
