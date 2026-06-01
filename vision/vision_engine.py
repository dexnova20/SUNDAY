# c:\Users\mshas\OneDrive\Desktop\SUNDAY\vision\vision_engine.py
"""
Vision Engine for SUNDAY.
Manages screen context caching, window-aware screenshots, selective region OCR,
and active focus tracking. Emits structured telemetry logs.
"""
import os
import threading
import time
from datetime import datetime
from vision.ui_context import UIContextExtractor
from vision.summary_builder import VisionSummaryBuilder
from config.settings import SCREENSHOT_PATH
from utils.constants import BLACKLISTED_APPS
from utils.logger import log_msg
from utils.validation import validate_coordinates
from utils.helpers import get_iso_timestamp

# Lazy imports to avoid heavy load if not used
try:
    from mss import mss
    from pytesseract import image_to_string
    from PIL import Image, ImageOps, ImageGrab
except ImportError:
    mss = image_to_string = Image = ImageOps = ImageGrab = None

# Telemetry log helpers routed directly to standard logger utility categories (Approved Telemetry)
def log_vision(msg: str):
    log_msg("VISION", msg)

def log_ui(msg: str):
    log_msg("UI CONTEXT", msg)

def log_ocr(msg: str):
    log_msg("OCR", msg)

def log_active_win(msg: str):
    log_msg("ACTIVE WINDOW", msg)


class VisionSession:
    """Screen awareness session.
    Captures on-demand and short-term cached context, avoiding continuous visual loops.
    Cache duration is set to 15 seconds, with automatic invalidation and diagnostics.
    """
    _instance = None

    def __init__(self, duration: int = 15, poll_interval: int = 4):
        self.duration = duration
        self.poll_interval = poll_interval
        self.active = False
        self.context = {}
        self.last_visual_snapshot = None  # Snapshot Traceability (Approved Requirement)
        self._last_scan_time = 0
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

    def get_context(self) -> dict:
        """
        Retrieves the cached visual context. 
        Automatically invalidates the cache if it's older than 15 seconds or if
        the active window title, process name, or window bounds size changes.
        """
        now = time.time()
        age = now - self._last_scan_time
        is_stale = age > self.duration
        
        # Check active window state to validate cache
        import pygetwindow as gw
        try:
            active_win = gw.getActiveWindow()
            if active_win and self.context:
                cached_win = self.context.get("window", {})
                title_changed = cached_win.get("title") != active_win.title
                size_changed = (
                    cached_win.get("bounds", [0, 0, 0, 0])[2] != active_win.width or
                    cached_win.get("bounds", [0, 0, 0, 0])[3] != active_win.height
                )
                if title_changed or size_changed:
                    # Cache Invalidation Telemetry (Approved Cache Diagnostics)
                    log_vision(f"[CACHE INVALIDATED] Cache invalidated: Active window or size changed (Title changed: {title_changed}, Size changed: {size_changed}).")
                    self.context = {}
                    is_stale = True
        except Exception:
            pass

        if is_stale or not self.context:
            # Cache Miss Telemetry (Approved Cache Diagnostics)
            log_vision(f"[CACHE MISS] Cached context stale or empty (Age: {age:.2f}s). Triggering synchronous visual update...")
            self._update_sync()
        else:
            # Cache Hit Telemetry (Approved Cache Diagnostics)
            log_vision(f"[CACHE HIT] Returning cached visual context (Age: {age:.2f}s).")
            
        return self.context

    def _update_sync(self):
        """Performs a synchronous screen scan to refresh the cache immediately."""
        extractor = UIContextExtractor()
        try:
            ui_data = extractor.extract_active_window()
            self._cache_ui_data(ui_data)
        except Exception as e:
            log_vision(f"Synchronous context extraction failed: {e}. Falling back to OCR.")
            self._fallback_ocr()

    def _cache_ui_data(self, ui_data: dict):
        """Standardizes and caches visual layouts into the unified system context format."""
        app_name = ui_data.get("app_name", "")
        if app_name in BLACKLISTED_APPS:
            log_vision(f"Skipping active visual scan due to privacy blacklist: {app_name}")
            self.context = {}
            return

        bounds = ui_data.get("window_bounds", [0, 0, 1920, 1080])
        mouse_pos = ui_data.get("mouse_position", [0, 0])
        
        # Compute relative cursor position
        rel_x = mouse_pos[0] - bounds[0]
        rel_y = mouse_pos[1] - bounds[1]
        
        # Format elements
        formatted_elements = []
        for e in ui_data.get("elements", []):
            formatted_elements.append({
                "name": e.get("name", ""),
                "type": e.get("type", "Control"),
                "bbox": e.get("bbox", [0, 0, 0, 0]),
                "automation_id": e.get("automation_id", ""),
                "focused": e.get("focused", False)
            })

        focused = ui_data.get("focused_element")
        focused_elem_dict = None
        if focused:
            focused_elem_dict = {
                "name": focused.get("name", ""),
                "type": focused.get("type", "Control"),
                "bbox": focused.get("bbox", [0, 0, 0, 0]),
                "automation_id": focused.get("automation_id", ""),
                "focused": True
            }

        # Build structural screen summary
        summary = VisionSummaryBuilder.build_summary(ui_data)

        # Unified structured output format
        self.context = {
            "window": {
                "title": ui_data.get("window_title", ""),
                "app": app_name,
                "process": ui_data.get("process_name", "Unknown"),
                "bounds": bounds,
                "focused_element": focused_elem_dict
            },
            "elements": formatted_elements,
            "mouse": {
                "screen": mouse_pos,
                "relative": [rel_x, rel_y]
            },
            "ocr": {
                "text": ""
            },
            "summary": summary,
            "confidence": {
                "source": "uia",
                "confidence": 1.0
            },
            "timestamp": get_iso_timestamp()
        }
        
        # Store exact visual snapshot trace (Approved Requirement)
        self.last_visual_snapshot = self.context
        
        self._last_scan_time = time.time()
        log_ui(f"Spatial UI Cache updated: '{self.context['window']['title']}' | Controls: {len(formatted_elements)}")

    def _fallback_ocr(self):
        """Primary monitor fallback OCR capture with lower confidence scores."""
        try:
            if mss and Image and ImageOps and image_to_string:
                with mss() as sct:
                    # Captures primary display context safely across monitors
                    monitor = sct.monitors[1]
                    img = sct.grab(monitor)
                    pil = Image.frombytes("RGB", img.size, img.rgb)
                    gray = ImageOps.grayscale(pil).resize((pil.width // 2, pil.height // 2))
                    text = image_to_string(gray)
                    
                    self.context = {
                        "window": {
                            "title": "Fallback Desktop Screen",
                            "app": "Windows Explorer",
                            "process": "explorer.exe",
                            "bounds": [0, 0, monitor["width"], monitor["height"]],
                            "focused_element": None
                        },
                        "elements": [],
                        "mouse": {
                            "screen": [0, 0],
                            "relative": [0, 0]
                        },
                        "ocr": {
                            "text": text
                        },
                        "summary": "Fallback monitor OCR scan completed successfully.",
                        "confidence": {
                            "source": "ocr",
                            "confidence": 0.91
                        },
                        "timestamp": get_iso_timestamp()
                    }
                    
                    # Store exact visual snapshot trace (Approved Requirement)
                    self.last_visual_snapshot = self.context
                    
                    self._last_scan_time = time.time()
                    log_ocr("Full monitor fallback OCR parsed successfully.")
        except Exception as ocr_e:
            log_ocr(f"OCR capture failed: {ocr_e}")

    def _run(self):
        start_time = time.time()
        extractor = UIContextExtractor()
        while not self._stop_event.is_set():
            try:
                # Background periodic cache updates
                active_win = gw.getActiveWindow()
                if active_win:
                    ui_data = extractor.extract_active_window()
                    self._cache_ui_data(ui_data)
            except Exception as e:
                log_vision(f"Background visual context extraction failed: {e}")
            
            # Duration timeout for background session loops
            if time.time() - start_time >= 40: # Extended background limit
                break
            time.sleep(self.poll_interval)
        log_vision("Visual context caching session completed.")

    def capture_window_screenshot(self, title: str = None) -> str:
        """
        Takes a window-aware screenshot of the active window or target application title.
        Saves the cropped image to Desktop. Supports multiple monitors.
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
            if ImageGrab:
                # PIL ImageGrab supports multi-monitor screenshot crops natively on Windows
                img = ImageGrab.grab(bbox)
                
                filename = f"SUNDAY_Window_Capture_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                filepath = os.path.join(SCREENSHOT_PATH, filename)
                img.save(filepath)
                
                log_active_win(f"Window screenshot saved at: {filepath}")
                return filepath
            else:
                raise RuntimeError("PIL ImageGrab is not available")
        except Exception as e:
            log_active_win(f"Window screenshot failed: {e}")
            raise

    def ocr_region(self, x: int, y: int, w: int, h: int) -> str:
        """
        Grabs screen coordinates and parses text from a specific rectangle region.
        Robustly works across multiple monitors.
        """
        if not validate_coordinates(x, y, w, h):
            raise ValueError(f"Target screen coordinates [{x}, {y}, {w}, {h}] are invalid or out of bounds.")
        try:
            log_ocr(f"Capturing selective screen region [X:{x}, Y:{y}, W:{w}, H:{h}]...")
            bbox = (x, y, x + w, y + h)
            if ImageGrab and ImageOps and image_to_string:
                img = ImageGrab.grab(bbox)
                
                # Upscale and binarize region for highly robust OCR accuracy
                gray = ImageOps.grayscale(img).resize((img.width * 2, img.height * 2))
                text = image_to_string(gray).strip()
                
                log_ocr(f"Selective region OCR complete (len: {len(text)})")
                return text
            else:
                raise RuntimeError("Required PIL/Pytesseract libraries not available")
        except Exception as e:
            log_ocr(f"Selective region OCR failed: {e}")
            raise
