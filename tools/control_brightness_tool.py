# c:\Users\mshas\OneDrive\Desktop\SUNDAY\tools\control_brightness_tool.py
"""
Control Brightness Tool for SUNDAY.
Adjusts the monitor screen brightness level up or down.
"""
from tools.base_tool import BaseTool

class ControlBrightnessTool(BaseTool):
    def __init__(self, default_action: str = None):
        super().__init__("adjust_brightness", 1, "Adjusts the monitor screen brightness level (up or down)")
        self.default_action = default_action

    def execute(self, parameters: dict, context: dict = None) -> dict:
        action = parameters.get("action", self.default_action)
        if not action or action == "adjust":
            action = "up"
        try:
            import screen_brightness_control as sbc
            current = sbc.get_brightness()
            if isinstance(current, list):
                current = current[0]
                
            if action == "up":
                target = min(100, current + 10)
                sbc.set_brightness(target)
            elif action == "down":
                target = max(0, current - 10)
                sbc.set_brightness(target)
            else:
                return {"success": False, "message": f"Unknown brightness action: '{action}'"}
            return {"success": True, "message": f"Brightness adjusted to {target}%"}
        except Exception as e:
            return {"success": False, "message": f"Failed to execute brightness adjustment: {str(e)}"}
