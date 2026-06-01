# c:\Users\mshas\OneDrive\Desktop\SUNDAY\vision\context_manager.py
"""
Utility class that manages the window active title, top window lists, and 
hacky text clipboard reader (simulating select all + copy).
"""
import time
import pygetwindow as gw
import pyautogui
import pyperclip

class ContextManager:
    @staticmethod
    def get_active_window_title() -> str:
        try:
            window = gw.getActiveWindow()
            if window:
                return window.title
        except Exception as e:
            print(f"Error getting active window: {e}")
        return "Unknown Window"

    @staticmethod
    def get_all_window_titles() -> list:
        try:
            # Filter out empty or hidden titles and limit to top 8 to keep context small
            titles = [w.title for w in gw.getAllWindows() if w.title.strip()]
            return titles[:8]
        except Exception as e:
            print(f"Error getting all windows: {e}")
            return []

    @staticmethod
    def _safe_paste(retries=5, delay=0.1):
        for _ in range(retries):
            try:
                return pyperclip.paste()
            except Exception:
                time.sleep(delay)
        return ""

    @staticmethod
    def _safe_copy(text, retries=5, delay=0.1):
        for _ in range(retries):
            try:
                pyperclip.copy(text)
                return
            except Exception:
                time.sleep(delay)

    @staticmethod
    def read_screen_text() -> str:
        """
        Attempts to read text from the active window by simulating Ctrl+A, Ctrl+C.
        This is a hacky but extremely effective offline way to 'read a tab'.
        """
        print("Attempting to read screen text via clipboard...")
        
        # Prevent self-termination: If the terminal is active, Ctrl+C will kill the Python script!
        active_title = ContextManager.get_active_window_title().lower()
        terminal_names = ["powershell", "cmd", "terminal", "command prompt"]
        if any(term in active_title for term in terminal_names):
            print("Terminal active. Skipping screen read to prevent script shutdown.")
            return "Terminal window is active. No visual context available."
            
        try:
            # Save current clipboard to restore it later
            old_clipboard = ContextManager._safe_paste()
            
            # Clear clipboard to ensure we get fresh data
            ContextManager._safe_copy("")
            
            # Simulate Ctrl+A, Ctrl+C
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.1)
            pyautogui.hotkey('ctrl', 'c')
            time.sleep(0.2)
            
            # Deselect the text
            pyautogui.press('right')
            
            new_clipboard = ContextManager._safe_paste()
            
            # Restore old clipboard so we don't mess up the user's workflow
            ContextManager._safe_copy(old_clipboard)
            
            if new_clipboard and new_clipboard.strip():
                # If the text is massive, truncate it to avoid overloading the LLM and causing massive freezes.
                # 1000 characters is enough context for the LLM to understand the page while keeping prompt-eval fast.
                if len(new_clipboard) > 1000:
                    return new_clipboard[:1000] + "\n...[Text Truncated]..."
                return new_clipboard
            else:
                return "No selectable text found on screen."
                
        except Exception as e:
            print(f"Error reading screen text: {e}")
            return "Failed to read screen text."
