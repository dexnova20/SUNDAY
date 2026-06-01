# c:\Users\mshas\OneDrive\Desktop\SUNDAY\tools\read_file_tool.py
"""
Read File Tool for SUNDAY.
Reads the first 500 characters of a text document from the desktop directory.
"""
import os
from tools.base_tool import BaseTool
from interface.console_output import display_response
from config.settings import SCREENSHOT_PATH

class ReadFileTool(BaseTool):
    def __init__(self):
        super().__init__("read_file", 2, "Reads the beginning of a text file from the desktop folder")

    def execute(self, parameters: dict, context: dict = None) -> dict:
        file_path = parameters.get("file_name", parameters.get("file_path", ""))
        if not file_path:
            return {"success": False, "message": "No file path provided"}

        try:
            full_path = file_path if os.path.isabs(file_path) else os.path.join(SCREENSHOT_PATH, file_path)
            
            if not os.path.exists(full_path):
                display_response(f"I could not find the file {file_path} on your desktop.")
                return {"success": False, "message": f"File does not exist at {full_path}"}

            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read(500)
            display_response(f"The file begins with: {content}")
            return {"success": True, "message": f"Successfully read file from {full_path}"}
        except Exception as e:
            return {"success": False, "message": f"Failed to read file: {str(e)}"}
