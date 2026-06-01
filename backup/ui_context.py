# ui_context.py
"""
Utility class that uses pygetwindow, pywinauto, uiautomation, and pyautogui
to extract UI elements, active focus status, bounding boxes, and mouse cursor locations.
"""
import logging
from typing import Dict, List

# Lazy imports to avoid heavy load if not used
try:
    import pygetwindow as gw
    from pywinauto import Desktop
    import uiautomation as auto
    import pyautogui
except ImportError:
    gw = Desktop = auto = pyautogui = None

logger = logging.getLogger("UI_CONTEXT")

class UIContextExtractor:
    def __init__(self):
        pass

    def extract_active_window(self) -> Dict:
        """Return a dictionary with app name, window title, mouse position, elements and focused controls.
        Limits element enumeration to first 100 items for performance.
        """
        if not (gw and Desktop and auto and pyautogui):
            raise RuntimeError("Required UI automation libraries (pygetwindow, pywinauto, pyautogui) not installed")
        
        result: Dict = {}
        try:
            # 1. Capture cursor position
            mouse_x, mouse_y = pyautogui.position()
            result["mouse_position"] = [mouse_x, mouse_y]

            # 2. Retrieve active window title
            active = gw.getActiveWindow()
            desktop = Desktop(backend="uia")
            if not active:
                try:
                    win_fallback = desktop.active_window()
                    if win_fallback:
                        active = type('Obj', (), {'title': win_fallback.element_info.name, '_hWnd': win_fallback.handle})
                except Exception:
                    pass
                if not active:
                    return {}
            
            result["window_title"] = active.title

            # 3. Retrieve window UIA wrapper via handle
            try:
                handle = getattr(active, "_hWnd", None) or getattr(active, "handle", None)
                if handle:
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

            # 4. Extract active application details
            result["app_name"] = win.element_info.name or ""
            elements: List[Dict] = []
            
            # Iterate through UI descendants (capped at 100 for safety)
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
                
                # Fetch spatial coordinates bounding box
                try:
                    rect = ctrl.rectangle()
                    left = rect.left
                    top = rect.top
                    width = rect.right - rect.left
                    height = rect.bottom - rect.top
                    bbox = [left, top, width, height]
                except Exception:
                    bbox = [0, 0, 0, 0]

                # Fetch keyboard active focus status
                try:
                    is_focused = ctrl.is_focused()
                except Exception:
                    is_focused = False

                if name:
                    elements.append({
                        "type": elem_type,
                        "name": name,
                        "bbox": bbox,
                        "focused": is_focused
                    })
                    
            result["elements"] = elements
            texts = [e["name"] for e in elements if e["name"]]
            result["important_text"] = " ".join(texts[:5])
            
            logger.debug(f"UI extraction: {len(elements)} elements captured")
            
        except Exception as e:
            logger.error(f"UI extraction failed: {e}")
            raise
            
        return result
