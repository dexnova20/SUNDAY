# c:\Users\mshas\OneDrive\Desktop\SUNDAY\vision\summary_builder.py
"""
Vision Summary Builder for SUNDAY.
Translates UIA control coordinate structures, window metadata, process names,
and active focused controls into detailed, human-readable screen descriptions.
"""
from typing import Dict

class VisionSummaryBuilder:
    @staticmethod
    def build_summary(ui_data: Dict) -> str:
        """
        Processes UIA extraction results and constructs a professional, highly readable paragraph.
        Conforms to spatial layout summaries expected by cognitively routing Brain prompts.
        """
        if not ui_data:
            return "No active screen window or elements are currently visible."
            
        app = ui_data.get("app_name", "Unknown Application")
        title = ui_data.get("window_title", "Unknown Window")
        proc_name = ui_data.get("process_name", "Unknown Process")
        bounds = ui_data.get("window_bounds", [0, 0, 0, 0])
        mouse = ui_data.get("mouse_position", [0, 0])
        elements = ui_data.get("elements", [])
        focused = ui_data.get("focused_element")
        
        # 1. Base window context
        summary = f"The active application is '{app}' (Process: '{proc_name}', Window: '{title}'). "
        summary += f"The application window is located at bounds X:{bounds[0]}, Y:{bounds[1]} with a size of {bounds[2]}x{bounds[3]} pixels. "
        
        # 2. Mouse context
        summary += f"The user's cursor is currently at screen coordinate position ({mouse[0]}, {mouse[1]}). "
        
        # 3. Focus context
        if focused:
            summary += f"Focused control: '{focused['name']}' of type '{focused['type']}' at boundaries {focused['bbox']}. "
        else:
            summary += "There is currently no keyboard-focused control detected. "
            
        # 4. Elements layout context
        if elements:
            summary += f"We detected {len(elements)} structural layout controls. "
            
            # Group by control types for readable summaries
            type_counts = {}
            for e in elements:
                t = e.get("type", "Control")
                type_counts[t] = type_counts.get(t, 0) + 1
                
            groups = [f"{count} {t_name}s" for t_name, count in type_counts.items()]
            summary += f"The interface contains: {', '.join(groups[:5])}. "
            
            # Detail key visible text landmarks
            key_names = [f"'{e['name']}' ({e['type']})" for e in elements[:6] if e.get("name")]
            if key_names:
                summary += f"Key landmarks include: {'; '.join(key_names)}. "
        else:
            summary += "No interactive buttons, textboxes, or standard layouts were resolved from the active window descendants."
            
        return summary.strip()
