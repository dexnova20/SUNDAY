# c:\Users\mshas\OneDrive\Desktop\SUNDAY\tools\ocr_region_tool.py
"""
OCR Region Tool for SUNDAY.
Parses text from specific coordinate monitor bounds [x, y, w, h] or [x1, y1, x2, y2].
"""
from tools.base_tool import BaseTool

class OcrRegionTool(BaseTool):
    def __init__(self, vision_session):
        super().__init__("ocr_region", 1, "Parses text from specific coordinate monitor bounds [x, y, w, h] or [x1, y1, x2, y2]")
        self.vision_session = vision_session

    def execute(self, parameters: dict, context: dict = None) -> dict:
        try:
            x1 = parameters.get("x1", parameters.get("x"))
            y1 = parameters.get("y1", parameters.get("y"))
            x2 = parameters.get("x2")
            y2 = parameters.get("y2")
            
            x = int(x1) if x1 is not None else 0
            y = int(y1) if y1 is not None else 0
            
            if x2 is not None and y2 is not None:
                w = int(x2) - x
                h = int(y2) - y
            else:
                w = int(parameters.get("w", 100))
                h = int(parameters.get("h", 100))
            
            text = self.vision_session.ocr_region(x, y, w, h)
            return {
                "success": True, 
                "message": f"Successfully parsed selective region OCR",
                "text": text
            }
        except Exception as e:
            return {"success": False, "message": f"Area OCR failed: {str(e)}"}
