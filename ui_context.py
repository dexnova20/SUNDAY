# ui_context.py
"""
Utility class that uses pygetwindow, pywinauto, and uiautomation to extract UI information from the active window.
"""
import logging
from typing import Dict, List

# Lazy imports to avoid heavy load if not used
try:
    import pygetwindow as gw
    from pywinauto import Desktop
    import uiautomation as auto
except ImportError:
    gw = Desktop = auto = None

logger = logging.getLogger("UI_CONTEXT")

class UIContextExtractor:
    def __init__(self):
        pass

    def extract_active_window(self) -> Dict:
        """Return a dictionary with app name, window title, important text, and UI elements.
        Limits element enumeration to first 100 items for performance.
        """
        if not (gw and Desktop and auto):
            raise RuntimeError("UI automation libraries not installed")
        result: Dict = {}
        try:
            # Retrieve active window title using pygetwindow; if unavailable, fallback to pywinauto
            active = gw.getActiveWindow()
            desktop = Desktop(backend="uia")
            if not active:
                # Fallback using pywinauto's active_window method
                try:
                    win_fallback = desktop.active_window()
                    if win_fallback:
                        active = type('Obj', (), {'title': win_fallback.element_info.name, '_hWnd': win_fallback.handle})
                except Exception:
                    pass
                if not active:
                    return {}
            result["window_title"] = active.title

            # Attempt to get the UIA element via pywinauto using window handle
            try:
                handle = getattr(active, "_hWnd", None) or getattr(active, "handle", None)
                if handle:
                    # Get the window specification and then the actual wrapper
                    win_spec = desktop.window(handle=handle)
                    win = win_spec.wrapper_object()
                else:
                    raise RuntimeError("Active window handle not available")
            except Exception as e:
                logger.warning(f"pywinauto window lookup failed: {e}")
                win = None

            if win is None:
                logger.warning("pywinauto could not locate the active window; proceeding with title only.")
                result["app_name"] = ""
                result["elements"] = []
                result["important_text"] = ""
                return result

            # Extract UI elements using pywinauto
            result["app_name"] = win.element_info.name or ""
            elements: List[Dict] = []
            for i, ctrl in enumerate(win.descendants()):
                if i >= 100:
                    break
                try:
                    elem_type = ctrl.friendly_class_name()
                except Exception:
                    elem_type = "Unknown"
                try:
                    name = ctrl.element_info.name or ctrl.window_text() or ""
                except Exception:
                    name = ""
                if name:
                    elements.append({"type": elem_type, "name": name})
            result["elements"] = elements
            texts = [e["name"] for e in elements if e["name"]]
            result["important_text"] = " ".join(texts[:5])
            logger.debug(f"UI extraction: {len(elements)} elements captured")
        except Exception as e:
            logger.error(f"UI extraction failed: {e}")
            raise
        return result
