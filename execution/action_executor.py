# c:\Users\mshas\OneDrive\Desktop\SUNDAY\execution\action_executor.py
"""
Action Executor for SUNDAY (Text-First Rebuild - Tool Registry Edition).
Implements a highly decoupled, modular Tool Registry Architecture.
Every system operation is encapsulated in a discrete tool class inheriting from BaseTool,
returning standardized success/failure status dictionaries.
"""
import string
from interface.console_output import display_response
from vision.vision_engine import VisionSession

# Import concrete tools
from tools.open_app_tool import OpenAppTool
from tools.open_website_tool import OpenWebsiteTool
from tools.search_web_tool import SearchWebTool
from tools.take_screenshot_tool import TakeScreenshotTool
from tools.type_text_tool import TypeTextTool
from tools.read_file_tool import ReadFileTool
from tools.control_volume_tool import ControlVolumeTool
from tools.control_brightness_tool import ControlBrightnessTool
from tools.control_media_tool import ControlMediaTool
from tools.system_power_tool import SystemPowerTool
from tools.play_media_tool import PlayMediaTool
from tools.vision_scan_tool import VisionScanTool
from tools.ocr_region_tool import OcrRegionTool
from tools.window_screenshot_tool import WindowScreenshotTool
from tools.mouse_tool import MouseTool
from tools.web_scrape_tool import WebScrapeTool
from tools.desktop_automation_tool import DesktopClickControlTool

class ActionExecutor:
    def __init__(self):
        # Map common spoken app names to system commands
        self.app_aliases = {
            "chrome": r'"C:\Program Files\Google\Chrome\Application\chrome.exe"',
            "edge": "msedge",
            "notepad": "notepad",
            "calculator": "calc",
            "vscode": "code",
            "visual studio code": "code",
            "terminal": "cmd",
            "discord": "discord",
            "spotify": "spotify"
        }
        
        # Initialize singleton VisionSession reference
        self.vision_session = VisionSession.get_instance()
        if not self.vision_session:
            # Fallback initialization in case session is queried prior to interface load
            self.vision_session = VisionSession()

        # Centralized Tool Registry Mapping
        self.tools = {
            "open_app": OpenAppTool(self.app_aliases),
            "open_website": OpenWebsiteTool(),
            "search_web": SearchWebTool(),
            "take_screenshot": TakeScreenshotTool(),
            "type_text": TypeTextTool(),
            "type": TypeTextTool(),
            "write": TypeTextTool(),
            "write_text": TypeTextTool(),
            "read_file": ReadFileTool(),
            "volume_up": ControlVolumeTool("up"),
            "volume_down": ControlVolumeTool("down"),
            "volume_mute": ControlVolumeTool("mute"),
            "adjust_volume": ControlVolumeTool("adjust"),
            "brightness_up": ControlBrightnessTool("up"),
            "brightness_down": ControlBrightnessTool("down"),
            "adjust_brightness": ControlBrightnessTool("adjust"),
            "media_play_pause": ControlMediaTool("playpause"),
            "media_next": ControlMediaTool("nexttrack"),
            "media_prev": ControlMediaTool("prevtrack"),
            "play_media": PlayMediaTool(),
            "system_shutdown": SystemPowerTool("shutdown"),
            "system_restart": SystemPowerTool("restart"),
            "system_sleep": SystemPowerTool("sleep"),
            
            # Dynamic Vision Tools
            "vision_scan": VisionScanTool(self.vision_session),
            "ocr_region": OcrRegionTool(self.vision_session),
            "window_screenshot": WindowScreenshotTool(self.vision_session),
            
            # Cursor / Mouse tracker tools
            "mouse": MouseTool(),
            "cursor": MouseTool(),
            
            # Advanced Web Research & Desktop UIA Clicking
            "web_scrape": WebScrapeTool(),
            "click_control": DesktopClickControlTool()
        }

    def evaluate_shortcut(self, command_text: str) -> dict:
        """
        Fast rule-based matching to bypass LLM for common commands.
        Normalizes text and checks for strict patterns.
        """
        if not command_text:
            return None
            
        # Normalize: lowercase and remove punctuation
        text = command_text.lower()
        text = text.translate(str.maketrans('', '', string.punctuation)).strip()
        
        # 1. Take Screenshot
        screenshot_phrases = ["take screenshot", "take a screenshot", "screenshot", "capture screen"]
        if text in screenshot_phrases:
            return {"intent": "take_screenshot", "sensitivity": 1}
            
        # 2. Search Web
        if text.startswith("search ") or text.startswith("search for "):
            query = text.replace("search for ", "").replace("search ", "").strip()
            if query:
                return {"intent": "search_web", "parameters": {"query": query}, "sensitivity": 1}
                
        # 3. Smart Open App/Website routing
        if text.startswith("open ") or text.startswith("launch ") or text.startswith("start "):
            app_name = text
            for prefix in ["open ", "launch ", "start "]:
                if text.startswith(prefix):
                    app_name = text[len(prefix):].strip()
                    break
                    
            for suffix in [" app", " application", " browser", " program"]:
                if app_name.endswith(suffix):
                    app_name = app_name[:-len(suffix)].strip()
                    
            # Check if it exactly matches an alias
            if app_name in self.app_aliases:
                return {"intent": "open_app", "parameters": {"app_name": app_name}, "sensitivity": 1}
                
            # If it contains a dot, treat it as a raw site
            if "." in app_name:
                return {"intent": "open_website", "parameters": {"site": app_name}, "sensitivity": 1}
                
            # Otherwise construct standard domain
            return {"intent": "open_website", "parameters": {"site": f"https://www.{app_name}.com"}, "sensitivity": 1}

        # 4. Type Text (Shortcut)
        original_text_lower = command_text.lower().strip()
        if original_text_lower.startswith("type "):
            content = command_text.strip()[5:].strip()
            return {"intent": "type_text", "parameters": {"text": content}, "sensitivity": 2}
        elif original_text_lower.startswith("enter "):
            content = command_text.strip()[6:].strip()
            return {"intent": "type_text", "parameters": {"text": content}, "sensitivity": 2}

        # 5. Volume Control
        if text in ["increase volume", "volume up", "turn up volume"]: 
            return {"intent": "volume_up", "sensitivity": 1}
        if text in ["decrease volume", "volume down", "turn down volume"]: 
            return {"intent": "volume_down", "sensitivity": 1}
        if text in ["mute", "mute volume", "unmute"]: 
            return {"intent": "volume_mute", "sensitivity": 1}
        
        # 6. Brightness Control
        if text in ["increase brightness", "brightness up", "turn up brightness"]: 
            return {"intent": "brightness_up", "sensitivity": 1}
        if text in ["decrease brightness", "brightness down", "turn down brightness"]: 
            return {"intent": "brightness_down", "sensitivity": 1}
        
        # 7. Media Control
        if text in ["play", "pause", "play music", "pause music", "play song", "pause song"]: 
            return {"intent": "media_play_pause", "sensitivity": 1}
        if text in ["next song", "next track", "skip song"]: 
            return {"intent": "media_next", "sensitivity": 1}
        if text in ["previous song", "previous track", "last song"]: 
            return {"intent": "media_prev", "sensitivity": 1}
        
        # 8. Power Commands (Sensitive = 2)
        if text in ["shutdown", "shut down", "shut down computer", "shutdown computer"]: 
            return {"intent": "system_shutdown", "sensitivity": 2}
        if text in ["restart", "restart computer"]: 
            return {"intent": "system_restart", "sensitivity": 2}
        if text in ["sleep", "sleep computer", "go to sleep"]: 
            return {"intent": "system_sleep", "sensitivity": 2}

        # 9. Mouse Tracker Shortcuts
        if text in ["mouse", "cursor", "where is my mouse", "get mouse position", "get cursor position"]:
            return {"intent": "mouse", "sensitivity": 1}

        return None

    def execute(self, intent: str, parameters: dict, context: dict = None) -> dict:
        """
        Executes the requested action intent safely using our centralized Tool Registry.
        Returns a standardized dictionary: {"success": bool, "message": str}
        """
        try:
            tool = self.tools.get(intent)
            if not tool:
                display_response("Action not implemented.")
                return {"success": False, "message": f"Action intent '{intent}' not registered in Tool Registry"}
            
            return tool.execute(parameters, context)
        except Exception as e:
            return {"success": False, "message": f"Registry execution routine crashed: {str(e)}"}
