# c:\Users\mshas\OneDrive\Desktop\SUNDAY\vision\ui_context.py
"""
Utility class that uses pygetwindow, pywinauto, uiautomation, and pyautogui
to extract UI elements, active focus status, bounding boxes, mouse cursor locations,
and active window bounds and process metadata.
"""
import logging
from typing import Dict, List
from utils.helpers import get_process_name_by_pid

# Lazy imports to avoid heavy load if not used
try:
    import pygetwindow as gw
    from pywinauto import Desktop
    import pyautogui
except ImportError:
    gw = Desktop = pyautogui = None

logger = logging.getLogger("UI_CONTEXT")

class UIContextExtractor:
    def __init__(self):
        pass

    def extract_active_window(self) -> Dict:
        """
        Return a dictionary with app name, process ID, process name, window title,
        window bounds (x, y, width, height), mouse position, elements list, and focused controls.
        Limits element enumeration to first 100 items for performance.
        """
        if not (gw and Desktop and pyautogui):
            raise RuntimeError("Required UI automation libraries (pygetwindow, pywinauto, pyautogui) not installed")
        
        result: Dict = {
            "app_name": "",
            "process_id": -1,
            "process_name": "Unknown",
            "window_title": "Unknown Window",
            "window_bounds": [0, 0, 0, 0],
            "mouse_position": [0, 0],
            "elements": [],
            "focused_element": None,
            "important_text": ""
        }
        
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
                        active = type('Obj', (), {
                            'title': win_fallback.element_info.name,
                            '_hWnd': win_fallback.handle,
                            'left': win_fallback.rectangle().left,
                            'top': win_fallback.rectangle().top,
                            'width': win_fallback.rectangle().width(),
                            'height': win_fallback.rectangle().height()
                        })
                except Exception:
                    pass
                if not active:
                    return result
            
            result["window_title"] = active.title
            
            # Extract window dimensions
            try:
                result["window_bounds"] = [
                    int(active.left),
                    int(active.top),
                    int(active.width),
                    int(active.height)
                ]
            except Exception:
                pass

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
                return result

            # 4. Extract active application details
            result["app_name"] = win.element_info.name or ""
            
            try:
                pid = win.process_id()
                result["process_id"] = pid
                result["process_name"] = get_process_name_by_pid(pid)
            except Exception:
                pass

            elements: List[Dict] = []
            
            # BFS traversal using immediate .children() to avoid building the full win.descendants() list
            # which hangs/blocks on large windows. Capped at 100 elements, with a strict time budget.
            import time
            start_time = time.time()
            max_seconds = 1.2
            
            queue = [win]
            element_count = 0
            
            while queue and element_count < 100:
                # Enforce strict maximum search time to prevent UI latency
                if (time.time() - start_time) > max_seconds:
                    logger.warning("UI context extraction timeout reached; stopping traversal.")
                    break
                    
                curr = queue.pop(0)
                
                # Exclude the root active window wrapper itself from elements list
                if curr != win:
                    try:
                        elem_type = curr.friendly_class_name()
                    except Exception:
                        elem_type = "Unknown"
                    try:
                        name = curr.element_info.name or curr.window_text() or ""
                    except Exception:
                        name = ""
                    
                    # Fetch spatial coordinates bounding box
                    try:
                        rect = curr.rectangle()
                        left = rect.left
                        top = rect.top
                        width = rect.right - rect.left
                        height = rect.bottom - rect.top
                        bbox = [left, top, width, height]
                    except Exception:
                        bbox = [0, 0, 0, 0]

                    # Fetch keyboard active focus status
                    try:
                        is_focused = curr.is_focused()
                    except Exception:
                        is_focused = False
                        
                    # Fetch Automation ID for clicking automation hooks
                    try:
                        auto_id = curr.element_info.automation_id or ""
                    except Exception:
                        auto_id = ""

                    if name:
                        elements.append({
                            "type": elem_type,
                            "name": name,
                            "bbox": bbox,
                            "focused": is_focused,
                            "automation_id": auto_id
                        })
                        element_count += 1
                
                # Fetch children of current control and add to queue
                try:
                    children = curr.children()
                    if children:
                        queue.extend(children)
                except Exception:
                    pass
                    
            result["elements"] = elements
            
            # Identify focused control element
            focused_elem = next((e for e in elements if e["focused"]), None)
            if focused_elem:
                result["focused_element"] = {
                    "name": focused_elem["name"],
                    "type": focused_elem["type"],
                    "bbox": focused_elem["bbox"],
                    "automation_id": focused_elem["automation_id"]
                }
                
            texts = [e["name"] for e in elements if e["name"]]
            result["important_text"] = " ".join(texts[:5])
            
            logger.debug(f"UI extraction: {len(elements)} elements captured")
            
        except Exception as e:
            logger.error(f"UI extraction failed: {e}")
            raise
            
        return result
