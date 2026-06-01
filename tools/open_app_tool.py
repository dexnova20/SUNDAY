# c:\Users\mshas\OneDrive\Desktop\SUNDAY\tools\open_app_tool.py
"""
Open Application Tool for SUNDAY.
Launches system programs via aliases, path, or fallback web queries.
"""
import os
import subprocess
from tools.base_tool import BaseTool
from interface.console_output import display_response
from tools.open_website_tool import OpenWebsiteTool

class OpenAppTool(BaseTool):
    def __init__(self, aliases: dict):
        super().__init__("open_app", 1, "Opens a local desktop application by name or fallback system commands")
        self.aliases = aliases

    def execute(self, parameters: dict, context: dict = None) -> dict:
        app_name = parameters.get("app_name", "")
        if not app_name:
            return {"success": False, "message": "No app name provided"}
        try:
            display_response(f"Opening {app_name}.")
            app_name_lower = app_name.lower().strip()
            command = self.aliases.get(app_name_lower)
            success = False
            
            # Try absolute or command alias
            if command:
                subprocess.Popen(command, shell=True)
                success = True
                
            # Fallback to system start
            if not success:
                result = os.system(f'start "" "{app_name}"')
                if result == 0:
                    success = True
                    
            # Fallback to browser search
            if not success:
                display_response(f"I couldn't find {app_name} on your system, searching the web instead.")
                web_tool = OpenWebsiteTool()
                return web_tool.execute({"site": f"https://www.google.com/search?q={app_name}"}, context)
                
            return {"success": True, "message": f"Successfully launched app: '{app_name}'"}
        except Exception as e:
            return {"success": False, "message": f"Exception opening {app_name}: {str(e)}"}
