# c:\Users\mshas\OneDrive\Desktop\SUNDAY\tools\search_web_tool.py
"""
Search Web Tool for SUNDAY.
Performs web queries using Google Search.
"""
from tools.base_tool import BaseTool
from tools.open_website_tool import OpenWebsiteTool

class SearchWebTool(BaseTool):
    def __init__(self):
        super().__init__("search_web", 1, "Performs a web search via standard Google search")

    def execute(self, parameters: dict, context: dict = None) -> dict:
        query = parameters.get("query", "")
        if not query:
            return {"success": False, "message": "No query provided for web search"}
        web_tool = OpenWebsiteTool()
        return web_tool.execute({"site": f"https://www.google.com/search?q={query}"}, context)
