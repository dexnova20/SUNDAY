# c:\Users\mshas\OneDrive\Desktop\SUNDAY\action_executor.py
"""
Action Executor for SUNDAY (Text-First Rebuild - Tool Registry Edition).
Implements a highly decoupled, modular Tool Registry Architecture.
Every system operation is encapsulated in a discrete tool class inheriting from BaseTool,
returning standardized success/failure status dictionaries.
"""
import os
import subprocess
import webbrowser
import pyautogui
import string
import pyperclip
from datetime import datetime
from voice_output import speak
import requests

# Apps we never analyze for privacy/security reasons
BLACKLISTED_APPS = {"Bitwarden", "KeePass", "Windows Security"}

# =====================================================================
# 1. Base Tool Class and Interface
# =====================================================================

class BaseTool:
    """Base class for all SUNDAY tools, enforcing standardized interfaces."""
    def __init__(self, name: str, sensitivity: int, description: str):
        self.name = name
        self.sensitivity = sensitivity
        self.description = description

    def execute(self, parameters: dict, context: dict = None) -> dict:
        """
        Runs the tool automation logic.
        Must return a standardized dictionary: {"success": bool, "message": str}
        """
        raise NotImplementedError("Each tool must implement the execute method.")


# =====================================================================
# 2. Concrete System Tool Classes
# =====================================================================

class OpenAppTool(BaseTool):
    def __init__(self, aliases: dict):
        super().__init__("open_app", 1, "Opens a local desktop application by name or fallback system commands")
        self.aliases = aliases

    def execute(self, parameters: dict, context: dict = None) -> dict:
        app_name = parameters.get("app_name", "")
        if not app_name:
            return {"success": False, "message": "No app name provided"}
        try:
            speak(f"Opening {app_name}.")
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
                speak(f"I couldn't find {app_name} on your system, searching the web instead.")
                web_tool = OpenWebsiteTool()
                return web_tool.execute({"site": f"https://www.google.com/search?q={app_name}"}, context)
                
            return {"success": True, "message": f"Successfully launched app: '{app_name}'"}
        except Exception as e:
            return {"success": False, "message": f"Exception opening {app_name}: {str(e)}"}


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
                speak("Opening website.")
            webbrowser.open(url)
            return {"success": True, "message": f"Opened website: {url}"}
        except Exception as e:
            return {"success": False, "message": f"Failed to open website {url}: {str(e)}"}


class SearchWebTool(BaseTool):
    def __init__(self):
        super().__init__("search_web", 1, "Performs a web search via standard Google search")

    def execute(self, parameters: dict, context: dict = None) -> dict:
        query = parameters.get("query", "")
        if not query:
            return {"success": False, "message": "No query provided for web search"}
        web_tool = OpenWebsiteTool()
        return web_tool.execute({"site": f"https://www.google.com/search?q={query}"}, context)


class TakeScreenshotTool(BaseTool):
    def __init__(self):
        super().__init__("take_screenshot", 1, "Captures a full screenshot of the primary monitor and saves to Desktop")

    def execute(self, parameters: dict, context: dict = None) -> dict:
        try:
            desktop = os.path.join(os.path.expanduser("~"), "OneDrive", "Desktop")
            if not os.path.exists(desktop):
                desktop = os.path.join(os.path.expanduser("~"), "Desktop")
                
            filename = f"SUNDAY_Screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            filepath = os.path.join(desktop, filename)
            pyautogui.screenshot(filepath)
            
            if os.path.exists(filepath):
                speak("Screenshot saved to your desktop.")
                return {"success": True, "message": f"Screenshot saved successfully at {filepath}"}
            else:
                return {"success": False, "message": "Screenshot file was not created"}
        except Exception as e:
            return {"success": False, "message": f"Failed to capture screenshot: {str(e)}"}


class TypeTextTool(BaseTool):
    def __init__(self):
        super().__init__("type_text", 2, "Types text in the active window by mimicking clipboard copy and paste commands")

    def execute(self, parameters: dict, context: dict = None) -> dict:
        text = parameters.get("text", "")
        if not text:
            return {"success": False, "message": "No text content provided to type"}
        try:
            speak("Typing in two seconds...")
            import time
            time.sleep(2) # Give user time to focus correct window
            
            pyperclip.copy(text)
            pyautogui.hotkey("ctrl", "v")
            return {"success": True, "message": "Successfully typed text via clipboard paste"}
        except Exception as e:
            return {"success": False, "message": f"Typing action failed: {str(e)}"}


class ReadFileTool(BaseTool):
    def __init__(self):
        super().__init__("read_file", 2, "Reads the beginning of a text file from the desktop folder")

    def execute(self, parameters: dict, context: dict = None) -> dict:
        file_path = parameters.get("file_name", parameters.get("file_path", ""))
        if not file_path:
            return {"success": False, "message": "No file path provided"}

        try:
            desktop = os.path.join(os.path.expanduser("~"), "OneDrive", "Desktop")
            if not os.path.exists(desktop):
                desktop = os.path.join(os.path.expanduser("~"), "Desktop")
                
            full_path = file_path if os.path.isabs(file_path) else os.path.join(desktop, file_path)
            
            if not os.path.exists(full_path):
                speak(f"I could not find the file {file_path} on your desktop.")
                return {"success": False, "message": f"File does not exist at {full_path}"}

            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read(500)
            speak(f"The file begins with: {content}")
            return {"success": True, "message": f"Successfully read file from {full_path}"}
        except Exception as e:
            return {"success": False, "message": f"Failed to read file: {str(e)}"}


class ControlVolumeTool(BaseTool):
    def __init__(self, default_action: str = None):
        super().__init__("adjust_volume", 1, "Adjusts the system volume level (up, down, or mute)")
        self.default_action = default_action

    def execute(self, parameters: dict, context: dict = None) -> dict:
        action = parameters.get("action", self.default_action)
        if not action or action == "adjust":
            action = "up"
        try:
            if action == "up": 
                pyautogui.press("volumeup")
            elif action == "down": 
                pyautogui.press("volumedown")
            elif action == "mute": 
                pyautogui.press("volumemute")
            else:
                return {"success": False, "message": f"Unknown volume action: '{action}'"}
            return {"success": True, "message": f"Volume command executed: '{action}'"}
        except Exception as e:
            return {"success": False, "message": f"Failed to execute volume adjustment: {str(e)}"}


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


class ControlMediaTool(BaseTool):
    def __init__(self, action: str):
        super().__init__("control_media", 1, f"Triggers media playback hotkeys: {action}")
        self.action = action

    def execute(self, parameters: dict, context: dict = None) -> dict:
        try:
            pyautogui.press(self.action)
            return {"success": True, "message": f"Media command executed: '{self.action}'"}
        except Exception as e:
            return {"success": False, "message": f"Failed to execute media control: {str(e)}"}


class SystemPowerTool(BaseTool):
    def __init__(self, action: str):
        super().__init__("system_power", 2, f"Triggers system power state modifications: {action}")
        self.action = action

    def execute(self, parameters: dict, context: dict = None) -> dict:
        try:
            speak(f"Executing {self.action} sequence.")
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


class PlayMediaTool(BaseTool):
    def __init__(self):
        super().__init__("play_media", 1, "Plays an online song or video query on YouTube or Spotify")

    def execute(self, parameters: dict, context: dict = None) -> dict:
        title = parameters.get("title", "")
        platform = parameters.get("platform", "YouTube")
        if not title:
            return {"success": False, "message": "No media query title provided"}
            
        try:
            speak(f"Playing {title} on {platform}.")
            import urllib.parse
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


# =====================================================================
# 3. Concrete Vision Tool Classes (Upgraded Spatial Vision)
# =====================================================================

class VisionScanTool(BaseTool):
    def __init__(self, vision_session):
        super().__init__("vision_scan", 1, "Performs an on-demand screen layout and focused UIA element context scan")
        self.vision_session = vision_session

    def execute(self, parameters: dict, context: dict = None) -> dict:
        try:
            from ui_context import UIContextExtractor
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


class OcrRegionTool(BaseTool):
    def __init__(self, vision_session):
        super().__init__("ocr_region", 1, "Parses text from specific coordinate monitor bounds [x, y, w, h]")
        self.vision_session = vision_session

    def execute(self, parameters: dict, context: dict = None) -> dict:
        try:
            x = int(parameters.get("x", 0))
            y = int(parameters.get("y", 0))
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


class WindowScreenshotTool(BaseTool):
    def __init__(self, vision_session):
        super().__init__("window_screenshot", 1, "Takes a window-aware cropped screenshot of a specific target window")
        self.vision_session = vision_session

    def execute(self, parameters: dict, context: dict = None) -> dict:
        try:
            title = parameters.get("title", "")
            filepath = self.vision_session.capture_window_screenshot(title if title else None)
            return {
                "success": True, 
                "message": f"Successfully captured window screenshot saved to {filepath}",
                "filepath": filepath
            }
        except Exception as e:
            return {"success": False, "message": f"Window screenshot failed: {str(e)}"}


# =====================================================================
# 4. Main Action Executor Class
# =====================================================================

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
        from vision_engine import VisionSession
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

        return None

    def execute(self, intent: str, parameters: dict, context: dict = None) -> dict:
        """
        Executes the requested action intent safely using our centralized Tool Registry.
        Returns a standardized dictionary: {"success": bool, "message": str}
        """
        try:
            tool = self.tools.get(intent)
            if not tool:
                speak("Action not implemented.")
                return {"success": False, "message": f"Action intent '{intent}' not registered in Tool Registry"}
            
            return tool.execute(parameters, context)
        except Exception as e:
            return {"success": False, "message": f"Registry execution routine crashed: {str(e)}"}
