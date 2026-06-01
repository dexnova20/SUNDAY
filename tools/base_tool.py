# c:\Users\mshas\OneDrive\Desktop\SUNDAY\tools\base_tool.py
"""
Base Tool Interface for SUNDAY.
Defines the abstract BaseTool class from which all discrete system automation tools inherit.
"""

class BaseTool:
    """Base class for all SUNDAY tools, enforcing standardized interfaces."""
    def __init__(self, name: str, sensitivity: int, description: str):
        self.name = name
        self.sensitivity = sensitivity
        self.description = description

    def execute(self, parameters: dict, context: dict = None) -> dict:
        """
        Runs the tool automation logic.
        Must return a standardized dictionary: {"success": bool, "message": str}
        """
        raise NotImplementedError("Each tool must implement the execute method.")
