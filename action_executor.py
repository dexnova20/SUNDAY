import os
import subprocess
import webbrowser
import pyautogui
import string
import pyperclip
from datetime import datetime
from voice_output import speak
import requests

class ActionExecutor:
    def __init__(self):
        # Map common spoken app names to their system commands with absolute paths where useful
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
                
        # 3. Open App or Website (Smart routing)
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
        if text in ["increase volume", "volume up", "turn up volume"]: return {"intent": "volume_up", "sensitivity": 1}
        if text in ["decrease volume", "volume down", "turn down volume"]: return {"intent": "volume_down", "sensitivity": 1}
        if text in ["mute", "mute volume", "unmute"]: return {"intent": "volume_mute", "sensitivity": 1}
        
        # 6. Brightness Control
        if text in ["increase brightness", "brightness up", "turn up brightness"]: return {"intent": "brightness_up", "sensitivity": 1}
        if text in ["decrease brightness", "brightness down", "turn down brightness"]: return {"intent": "brightness_down", "sensitivity": 1}
        
        # 7. Media Control
        if text in ["play", "pause", "play music", "pause music", "play song", "pause song"]: return {"intent": "media_play_pause", "sensitivity": 1}
        if text in ["next song", "next track", "skip song"]: return {"intent": "media_next", "sensitivity": 1}
        if text in ["previous song", "previous track", "last song"]: return {"intent": "media_prev", "sensitivity": 1}
        
        # 8. Power Commands (Sensitive = 2)
        if text in ["shutdown", "shut down", "shut down computer", "shutdown computer"]: return {"intent": "system_shutdown", "sensitivity": 2}
        if text in ["restart", "restart computer"]: return {"intent": "system_restart", "sensitivity": 2}
        if text in ["sleep", "sleep computer", "go to sleep"]: return {"intent": "system_sleep", "sensitivity": 2}

        return None

    def execute(self, intent: str, parameters: dict, context: dict = None):
        """
        Executes the requested action safely with robust fallbacks.
        """
        if intent == "open_app":
            self._open_app(parameters.get("app_name", ""))
        elif intent == "open_website":
            site = parameters.get("site", parameters.get("url", ""))
            self._open_website(site)
        elif intent == "search_web":
            query = parameters.get("query", "")
            self._open_website(f"https://www.google.com/search?q={query}")
        elif intent == "take_screenshot":
            self._take_screenshot()
        elif intent in ["type_text", "type", "write", "write_text"]:
            self._type_text(parameters.get("text", ""))
        elif intent == "solve_query":
            self._solve_query(parameters.get("query", ""), context)
        elif intent == "read_file":
            self._read_file(parameters.get("file_name", parameters.get("file_path", "")))
        elif intent == "volume_up": self._control_volume("up")
        elif intent == "volume_down": self._control_volume("down")
        elif intent == "volume_mute": self._control_volume("mute")
        elif intent == "brightness_up": self._control_brightness("up")
        elif intent == "brightness_down": self._control_brightness("down")
        elif intent == "adjust_volume":
            self._control_volume(parameters.get("action", "up"))
        elif intent == "adjust_brightness":
            self._control_brightness(parameters.get("action", "up"))
        elif intent == "media_play_pause": self._control_media("playpause")
        elif intent == "media_next": self._control_media("nexttrack")
        elif intent == "media_prev": self._control_media("prevtrack")
        elif intent == "play_media":
            self._play_media(parameters.get("title", ""), parameters.get("platform", "YouTube"))
        elif intent in ["system_shutdown", "system_restart", "system_sleep"]:
            self._system_power(intent.split("_")[1])
        elif intent == "unknown":
            speak("I'm not sure how to do that yet.")
        else:
            speak("Action not implemented.")

    def _open_app(self, app_name: str):
        if not app_name:
            speak("I didn't catch the app name.")
            return

        speak(f"Opening {app_name}.")
        app_name_lower = app_name.lower().strip()
        command = self.app_aliases.get(app_name_lower)

        success = False
        
        # 1. Try dictionary command/path
        if command:
            try:
                subprocess.Popen(command, shell=True)
                success = True
            except Exception as e:
                print(f"Popen failed for {app_name}: {e}")
                
        # 2. Fallback to OS system start (works well for things in PATH like spotify/discord)
        if not success:
            try:
                # Start returns 0 on success, but since it's async we just try it
                result = os.system(f'start "" "{app_name}"')
                if result == 0:
                    success = True
            except Exception as e:
                print(f"OS start failed for {app_name}: {e}")
                
        # 3. Ultimate Fallback to Web Search
        if not success:
            print(f"Failed to open app {app_name}. Falling back to web search.")
            speak(f"I couldn't find {app_name} on your system, searching the web instead.")
            self._open_website(f"https://www.google.com/search?q={app_name}")

    def _open_website(self, url: str):
        if not url:
            speak("I didn't catch the website URL.")
            return
            
        # Ensure proper URL formatting
        if not url.startswith("http"):
            url = f"https://{url}"
            if "." not in url:
                url += ".com"
                
        # Only speak "Opening website" if it's not a background fallback
        if "google.com/search" not in url:
            speak("Opening website.")
            
        try:
            webbrowser.open(url)
        except Exception as e:
            print(f"Failed to open website {url}: {e}")
            speak("I couldn't open the browser. Searching the web instead.")
            # Prevent infinite recursion if search fails
            if "google.com/search" not in url:
                self._open_website(f"https://www.google.com/search?q={url}")

    def _take_screenshot(self):
        try:
            desktop = os.path.join(os.path.expanduser("~"), "OneDrive", "Desktop")
            if not os.path.exists(desktop):
                desktop = os.path.join(os.path.expanduser("~"), "Desktop")
                
            filename = f"SUNDAY_Screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            filepath = os.path.join(desktop, filename)
            
            pyautogui.screenshot(filepath)
            speak("Screenshot saved to your desktop.")
        except Exception as e:
            print(f"Screenshot error: {e}")
            speak("I was unable to take a screenshot.")

    def _solve_query(self, query: str, context: dict):
        if not query:
            speak("I didn't catch your question.")
            return
            
        speak("Let me think about that.")
        
        context_text = f"Context (Active Window: {context.get('active_window', 'Unknown')})\n"
        if context and context.get("screen_text") and context["screen_text"] != "No selectable text found on screen.":
            context_text += f"Screen Text:\n{context['screen_text']}\n\n"
            
        prompt = f"{context_text}User query: {query}\nProvide a concise, spoken answer (1-3 sentences). Do not use markdown."
        
        payload = {
            "model": "llama3.2",
            "prompt": prompt,
            "stream": False
        }
        
        try:
            response = requests.post("http://localhost:11434/api/generate", json=payload)
            response.raise_for_status()
            answer = response.json().get("response", "I don't have an answer for that right now.")
            speak(answer)
        except Exception as e:
            print(f"Ollama Error in solve_query: {e}")
            speak("My brain encountered an error while trying to solve that.")

    def _read_file(self, file_path: str):
        if not file_path:
            speak("No file path provided.")
            return

        desktop = os.path.join(os.path.expanduser("~"), "OneDrive", "Desktop")
        if not os.path.exists(desktop):
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            
        full_path = os.path.join(desktop, file_path)
        
        if not os.path.exists(full_path):
            speak(f"I could not find the file {file_path} on your desktop.")
            return

        try:
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read(500)
            speak(f"The file begins with: {content}")
        except Exception as e:
            print(f"Failed to read file: {e}")
            speak("I could not read the file due to an error.")

    def _type_text(self, text: str):
        if not text:
            speak("I didn't catch what to type.")
            return
            
        speak("Typing in two seconds...")
        import time
        time.sleep(2) # Give user time to focus correct window
        
        try:
            pyperclip.copy(text)
            pyautogui.hotkey("ctrl", "v")
            print("Successfully pasted text via clipboard.")
        except Exception as e:
            print(f"Typing error: {e}")
            speak("Typing failed.")

    def _control_volume(self, action: str):
        if action == "up": pyautogui.press("volumeup")
        elif action == "down": pyautogui.press("volumedown")
        elif action == "mute": pyautogui.press("volumemute")

    def _control_brightness(self, action: str):
        try:
            import screen_brightness_control as sbc
            current = sbc.get_brightness()
            if isinstance(current, list):
                current = current[0]
                
            if action == "up":
                sbc.set_brightness(min(100, current + 10))
            elif action == "down":
                sbc.set_brightness(max(0, current - 10))
        except Exception as e:
            print(f"Brightness control failed: {e}")
            speak("I could not adjust the brightness.")

    def _control_media(self, action: str):
        pyautogui.press(action)

    def _system_power(self, action: str):
        speak(f"Executing {action} sequence.")
        if action == "shutdown":
            os.system("shutdown /s /t 1")
        elif action == "restart":
            os.system("shutdown /r /t 1")
        elif action == "sleep":
            os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")

    def _play_media(self, title: str, platform: str):
        speak(f"Playing {title} on {platform}.")
        import urllib.parse
        if platform.lower() in ["youtube", "yt"]:
            query = urllib.parse.quote(title)
            self._open_website(f"https://www.youtube.com/results?search_query={query}")
        elif platform.lower() == "spotify":
            # Will try to open via browser for now, can be expanded to local spotify URI
            query = urllib.parse.quote(title)
            self._open_website(f"https://open.spotify.com/search/{query}")
        else:
            query = urllib.parse.quote(f"play {title} on {platform}")
            self._open_website(f"https://www.google.com/search?q={query}")
