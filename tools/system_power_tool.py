# c:\Users\mshas\OneDrive\Desktop\SUNDAY\tools\system_power_tool.py
"""
System Power Tool for SUNDAY.
Triggers system power state modifications: shutdown, restart, sleep.
"""
import os
from tools.base_tool import BaseTool
from interface.console_output import display_response

class SystemPowerTool(BaseTool):
    def __init__(self, action: str):
        super().__init__("system_power", 2, f"Triggers system power state modifications: {action}")
        self.action = action

    def execute(self, parameters: dict, context: dict = None) -> dict:
        try:
            display_response(f"Executing {self.action} sequence.")
            if self.action == "shutdown":
                os.system("shutdown /s /t 1")
            elif self.action == "restart":
                os.system("shutdown /r /t 1")
            elif self.action == "sleep":
                os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
            else:
                return {"success": False, "message": f"Unknown power command: '{self.action}'"}
            return {"success": True, "message": f"System power sequence '{self.action}' triggered"}
        except Exception as e:
            return {"success": False, "message": f"Failed to trigger system power action: {str(e)}"}
