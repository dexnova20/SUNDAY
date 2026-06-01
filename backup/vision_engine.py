# vision_engine.py
"""
Vision Engine for SUNDAY (Text-First Rebuild).
Manages screen context caching, window-aware screenshots, selective region OCR,
and active focus tracking. Emits structured telemetry logs.
"""
import os
import threading
import time
import logging
from datetime import datetime
from ui_context import UIContextExtractor
from mss import mss
from pytesseract import image_to_string
from PIL import Image, ImageOps, ImageGrab

logger = logging.getLogger("VISION")

# Telemetry log helpers
def log_vision(msg: str):
    logger.info(f"[VISION] {msg}")

def log_ui(msg: str):
    logger.info(f"[UI CONTEXT] {msg}")

def log_ocr(msg: str):
    logger.info(f"[OCR] {msg}")

def log_active_win(msg: str):
    logger.info(f"[ACTIVE WINDOW] {msg}")

# Apps we never analyze for privacy/security reasons
BLACKLISTED_APPS = {"Bitwarden", "KeePass", "Windows Security"}

class VisionSession:
    """Screen awareness session.
    Captures on-demand and short-term cached context, avoiding continuous visual loops.
    """
    _instance = None

    def __init__(self, duration: int = 30, poll_interval: int = 6):
        self.duration = duration
        self.poll_interval = poll_interval
        self.active = False
        self.context = {}
        self._stop_event = threading.Event()
        self._thread = None
        VisionSession._instance = self

    @staticmethod
    def get_instance():
        return VisionSession._instance

    def start(self):
        """Starts a temporary visual caching background thread."""
        if self.active:
            log_vision("Vision session already active")
            return
        self.active = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        log_vision("Visual context caching loop started.")

    def stop(self):
        """Stops the visual caching thread."""
        if not self.active:
            return
        self._stop_event.set()
        if self._thread:
            self._thread.join()
        self.active = False
        log_vision("Visual context caching loop stopped.")

    def _run(self):
        start_time = time.time()
        extractor = UIContextExtractor()
        while not self._stop_event.is_set():
            try:
                # Capture active UI elements structure
                ui_data = extractor.extract_active_window()
                
                # Check for blacklisted titles/apps
                app_name = ui_data.get("app_name", "")
                if app_name in BLACKLISTED_APPS:
                    log_vision(f"Skipping active visual scan due to privacy blacklist: {app_name}")
                    self.context = {}
                else:
                    summary = self._summarize_ui(ui_data)
                    self.context = {
                        "app": app_name,
                        "title": ui_data.get("window_title", ""),
                        "mouse": ui_data.get("mouse_position", [0, 0]),
                        "summary": summary,
                        "important_text": ui_data.get("important_text", ""),
                        "elements": ui_data.get("elements", [])
                    }
                    log_ui(f"Spatial UI updated: '{self.context['title']}' | Controls: {len(self.context['elements'])}")
            except Exception as e:
                log_vision(f"Background context extraction failed: {e}")
                # Primary monitor fallback OCR capture
                try:
                    with mss() as sct:
                        monitor = sct.monitors[1]
                        img = sct.grab(monitor)
                        pil = Image.frombytes("RGB", img.size, img.rgb)
                        gray = ImageOps.grayscale(pil).resize((pil.width // 2, pil.height // 2))
                        text = image_to_string(gray)
                        self.context = {"ocr_text": text}
                        log_ocr("Full monitor fallback OCR parsed successfully.")
                except Exception as ocr_e:
                    log_ocr(f"OCR capture failed: {ocr_e}")
            
            # Session duration timeout
            if time.time() - start_time >= self.duration:
                break
            time.sleep(self.poll_interval)
        log_vision("Visual context caching session completed.")

    def _summarize_ui(self, ui_data: dict) -> str:
        """Create a highly structured screen layout summary for LLM injection."""
        app = ui_data.get("app_name", "")
        title = ui_data.get("window_title", "")
        elems = ui_data.get("elements", [])
        mouse_pos = ui_data.get("mouse_position", [0, 0])
        
        # Track focused element
        focused_elem = next((e for e in elems if e.get("focused")), None)
        focused_str = f"Focused: '{focused_elem['name']}' ({focused_elem['type']}) at coordinates {focused_elem['bbox']}" if focused_elem else "Focused: None"
        
        # Format elements bounding box list concisely
        item_strings = []
        for e in elems[:8]:
            item_strings.append(f"'{e.get('name')}' [{e.get('type')}] bbox {e.get('bbox')}")
        snippet = "; ".join(item_strings)
        
        summary = f"App: {app} | Title: {title} | Cursor: {mouse_pos} | {focused_str} | Active Layout: {snippet}"
        return summary

    def capture_window_screenshot(self, title: str = None) -> str:
        """
        Takes a window-aware screenshot of the active window or target application title.
        Saves the cropped image to Desktop. Returns the filepath.
        """
        import pygetwindow as gw
        target_win = None
        
        try:
            if title:
                log_active_win(f"Locating target window by title: '{title}'...")
                wins = gw.getWindowsWithTitle(title)
                if wins:
                    target_win = wins[0]
            else:
                target_win = gw.getActiveWindow()
                
            if not target_win:
                raise RuntimeError("No target window located")
                
            log_active_win(f"Capturing screenshot shape for window: '{target_win.title}'")
            
            # Crop box (left, top, right, bottom)
            bbox = (target_win.left, target_win.top, target_win.right, target_win.bottom)
            img = ImageGrab.grab(bbox)
            
            desktop = os.path.join(os.path.expanduser("~"), "OneDrive", "Desktop")
            if not os.path.exists(desktop):
                desktop = os.path.join(os.path.expanduser("~"), "Desktop")
                
            filename = f"SUNDAY_Window_Capture_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            filepath = os.path.join(desktop, filename)
            img.save(filepath)
            
            log_active_win(f"Window screenshot saved at: {filepath}")
            return filepath
        except Exception as e:
            log_active_win(f"Window screenshot failed: {e}")
            raise

    def ocr_region(self, x: int, y: int, w: int, h: int) -> str:
        """
        Grabs screen coordinates and parses text from a specific rectangle region.
        Returns the parsed text.
        """
        try:
            log_ocr(f"Capturing selective screen region [X:{x}, Y:{y}, W:{w}, H:{h}]...")
            bbox = (x, y, x + w, y + h)
            img = ImageGrab.grab(bbox)
            
            # Upscale and binarize region for highly robust OCR accuracy
            gray = ImageOps.grayscale(img).resize((img.width * 2, img.height * 2))
            text = image_to_string(gray).strip()
            
            log_ocr(f"Selective region OCR complete (len: {len(text)})")
            return text
        except Exception as e:
            log_ocr(f"Selective region OCR failed: {e}")
            raise
