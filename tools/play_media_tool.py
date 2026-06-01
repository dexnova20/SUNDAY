# c:\Users\mshas\OneDrive\Desktop\SUNDAY\tools\play_media_tool.py
"""
Play Media Tool for SUNDAY.
Plays an online song or video query on YouTube or Spotify.
"""
import urllib.parse
from tools.base_tool import BaseTool
from interface.console_output import display_response
from tools.open_website_tool import OpenWebsiteTool

class PlayMediaTool(BaseTool):
    def __init__(self):
        super().__init__("play_media", 1, "Plays an online song or video query on YouTube or Spotify")

    def execute(self, parameters: dict, context: dict = None) -> dict:
        title = parameters.get("title", "")
        platform = parameters.get("platform", "YouTube")
        if not title:
            return {"success": False, "message": "No media query title provided"}
            
        try:
            display_response(f"Playing {title} on {platform}.")
            web_tool = OpenWebsiteTool()
            if platform.lower() in ["youtube", "yt"]:
                query = urllib.parse.quote(title)
                return web_tool.execute({"site": f"https://www.youtube.com/results?search_query={query}"}, context)
            elif platform.lower() == "spotify":
                query = urllib.parse.quote(title)
                return web_tool.execute({"site": f"https://open.spotify.com/search/{query}"}, context)
            else:
                query = urllib.parse.quote(f"play {title} on {platform}")
                return web_tool.execute({"site": f"https://www.google.com/search?q={query}"}, context)
        except Exception as e:
            return {"success": False, "message": f"Failed to initiate media search play: {str(e)}"}
