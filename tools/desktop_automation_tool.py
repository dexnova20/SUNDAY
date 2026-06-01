# c:\Users\mshas\OneDrive\Desktop\SUNDAY\tools\desktop_automation_tool.py
"""
Desktop Click Control Tool for SUNDAY.
Scans active UIA coordinates, matches a target control (by name or automation ID),
revalidates its location immediately, and simulates cursor clicks and text entry.
"""
import time
import pyautogui
from tools.base_tool import BaseTool
from vision.ui_context import UIContextExtractor
from tools.type_text_tool import TypeTextTool

class DesktopClickControlTool(BaseTool):
    def __init__(self):
        super().__init__("click_control", 2, "Revalidates UIA layouts, hovers and clicks on screen elements, and types optional input texts")

    def execute(self, parameters: dict, context: dict = None) -> dict:
        target = parameters.get("target", "").strip()
        text_to_type = parameters.get("text", "").strip()
        double_click = parameters.get("double_click", False)
        
        if not target:
            return {"success": False, "message": "No control target name or ID provided for clicking"}

        try:
            # 1. Immediate pre-click UIA Revalidation (Approved Requirement)
            print(f"[AUTOMATION] Revalidating active window UIA controls for target: '{target}'...")
            extractor = UIContextExtractor()
            ui_data = extractor.extract_active_window()
            elements = ui_data.get("elements", [])
            
            target_lower = target.lower()
            matched_element = None
            
            # First pass: try exact match on name or automation ID
            for e in elements:
                e_name = e.get("name", "").strip().lower()
                e_auto_id = e.get("automation_id", "").strip().lower()
                
                if target_lower == e_name or target_lower == e_auto_id:
                    matched_element = e
                    break
                    
            # Second pass: try substring match if exact not found
            if not matched_element:
                for e in elements:
                    e_name = e.get("name", "").strip().lower()
                    if target_lower in e_name:
                        matched_element = e
                        break
                        
            if not matched_element:
                # Log list of visible elements to assist debugging
                visible = ", ".join([f"'{e.get('name')}'" for e in elements[:10]])
                return {
                    "success": False,
                    "message": f"Target element '{target}' not found during immediate pre-click revalidation. Visible elements: {visible}"
                }
                
            # 2. Extract bounding box [left, top, width, height]
            bbox = matched_element.get("bbox", [0, 0, 0, 0])
            if bbox == [0, 0, 0, 0]:
                return {"success": False, "message": f"Target element '{target}' found, but its coordinates bounding box is invalid [0,0,0,0]."}
                
            # Compute center of the element
            left, top, width, height = bbox
            click_x = left + (width // 2)
            click_y = top + (height // 2)
            
            print(f"[AUTOMATION] Located element '{matched_element.get('name')}' ({matched_element.get('type')}) at screen center X:{click_x}, Y:{click_y}.")
            
            # Save current cursor position for relative tracking diagnostics
            orig_x, orig_y = pyautogui.position()
            
            # 3. Simulate Mouse Action
            pyautogui.moveTo(click_x, click_y, duration=0.4)
            if double_click:
                pyautogui.doubleClick()
                action_desc = "Double-clicked"
            else:
                pyautogui.click()
                action_desc = "Clicked"
                
            # 4. Optional Text typing sequence
            if text_to_type:
                print(f"[AUTOMATION] Typing text: '{text_to_type}' inside the control element...")
                time.sleep(0.5)
                typer = TypeTextTool()
                # Run clipboard paste without sleep delay since element is already focused
                import pyperclip
                pyperclip.copy(text_to_type)
                pyautogui.hotkey("ctrl", "v")
                action_desc += f" and typed '{text_to_type}'"
                
            # Move cursor back out of the way for clean visuals
            pyautogui.moveTo(orig_x, orig_y, duration=0.2)
            
            return {
                "success": True,
                "message": f"Successfully {action_desc} on target control '{matched_element.get('name')}' at coordinates ({click_x}, {click_y})."
            }
            
        except Exception as e:
            return {"success": False, "message": f"Desktop click automation failed: {str(e)}"}
