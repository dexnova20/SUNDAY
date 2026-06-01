import threading
import time
import logging
from ui_context import UIContextExtractor
from mss import mss
from pytesseract import image_to_string
from PIL import Image, ImageOps

logger = logging.getLogger("VISION")

# Apps we never analyze for privacy/security reasons
BLACKLISTED_APPS = {"Bitwarden", "KeePass", "Windows Security"}

class VisionSession:
    """Temporary screen‑awareness session.
    Captures context every few seconds, stores a concise summary instead of raw UI trees.
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
        if self.active:
            logger.info("Vision session already active")
            return
        self.active = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        logger.info("[VISION] Vision mode activated")

    def stop(self):
        if not self.active:
            return
        self._stop_event.set()
        self._thread.join()
        self.active = False
        logger.info("[VISION] Vision mode stopped")

    def _run(self):
        start_time = time.time()
        extractor = UIContextExtractor()
        while not self._stop_event.is_set():
            try:
                ui_data = extractor.extract_active_window()
                # Filter blacklisted apps
                if ui_data.get("app_name") in BLACKLISTED_APPS:
                    logger.info(f"[VISION] Skipping blacklisted app {ui_data.get('app_name')}")
                    self.context = {}
                else:
                    # Build a lightweight summary
                    summary = self._summarize_ui(ui_data)
                    self.context = {
                        "app": ui_data.get("app_name", ""),
                        "title": ui_data.get("window_title", ""),
                        "summary": summary,
                        "important_text": ui_data.get("important_text", ""),
                        "elements": ui_data.get("elements", [])[:20]  # cap size
                    }
                    logger.debug("[VISION] Context updated")
            except Exception as e:
                logger.warning(f"[VISION] UI extraction failed: {e}")
                # OCR fallback on active window only
                try:
                    with mss() as sct:
                        monitor = sct.monitors[1]  # primary monitor
                        img = sct.grab(monitor)
                        pil = Image.frombytes("RGB", img.size, img.rgb)
                        gray = ImageOps.grayscale(pil).resize((pil.width // 2, pil.height // 2))
                        text = image_to_string(gray)
                        self.context = {"ocr_text": text}
                        logger.debug("[VISION] OCR fallback completed")
                except Exception as ocr_e:
                    logger.error(f"[VISION] OCR failed: {ocr_e}")
            # Session timeout
            if time.time() - start_time >= self.duration:
                break
            time.sleep(self.poll_interval)
        logger.info("[VISION] Vision session completed")

    def _summarize_ui(self, ui_data: dict) -> str:
        """Create a short human‑readable summary from raw UI data.
        This avoids sending huge element trees to the LLM.
        """
        app = ui_data.get("app_name", "")
        title = ui_data.get("window_title", "")
        elems = ui_data.get("elements", [])
        # Extract up to 5 textual elements for the summary
        texts = [e.get("name") for e in elems if e.get("name")]
        snippet = ", ".join(texts[:5])
        summary = f"{app} – {title}. Visible items: {snippet}" if snippet else f"{app} – {title}."
        return summary
