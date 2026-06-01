# c:\Users\mshas\OneDrive\Desktop\SUNDAY\tools\open_website_tool.py
"""
Open Website Tool for SUNDAY.
Opens a target website URL in the default browser.
"""
import webbrowser
from tools.base_tool import BaseTool
from interface.console_output import display_response

class OpenWebsiteTool(BaseTool):
    def __init__(self):
        super().__init__("open_website", 1, "Opens a website URL in the default system browser")

    def execute(self, parameters: dict, context: dict = None) -> dict:
        url = parameters.get("site", parameters.get("url", ""))
        if not url:
            return {"success": False, "message": "No website URL provided"}
        try:
            if not url.startswith("http"):
                url = f"https://{url}"
                if "." not in url:
                    url += ".com"
            if "google.com/search" not in url:
                display_response("Opening website.")
            webbrowser.open(url)
            return {"success": True, "message": f"Opened website: {url}"}
        except Exception as e:
            return {"success": False, "message": f"Failed to open website {url}: {str(e)}"}
