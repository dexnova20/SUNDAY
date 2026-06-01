"""hotkey_manager.py
Registers safe global hot‑keys to activate VisionSession.
Supports ALT+S and CTRL+SHIFT+SPACE as activation shortcuts.
"""
import logging
import threading
import keyboard
from vision_engine import VisionSession

logger = logging.getLogger("HOTKEY")

class HotkeyManager:
    def __init__(self, session: VisionSession):
        self.session = session
        self._register_hotkeys()

    def _register_hotkeys(self):
        try:
            # Use daemon thread for the hotkey listener to avoid blocking on Windows
            threading.Thread(target=self._add_hotkeys, daemon=True).start()
        except Exception as e:
            logger.error(f"[HOTKEY] Failed to start hotkey thread: {e}")

    def _add_hotkeys(self):
        # ALT+S – primary safe shortcut
        keyboard.add_hotkey("alt+s", self._activate, suppress=True, trigger_on_release=False)
        # CTRL+SHIFT+SPACE – secondary shortcut
        keyboard.add_hotkey("ctrl+shift+space", self._activate, suppress=True, trigger_on_release=False)
        logger.info("[HOTKEY] Registered ALT+S and CTRL+SHIFT+SPACE for Vision mode activation")
        # Keep the thread alive while the program runs
        keyboard.wait()  # blocks until the program exits

    def _activate(self):
        logger.info("[HOTKEY] Activation shortcut pressed – starting Vision session")
        self.session.start()
