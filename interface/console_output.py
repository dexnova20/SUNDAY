# c:\Users\mshas\OneDrive\Desktop\SUNDAY\interface\console_output.py
"""
Text-First Output Subsystem for SUNDAY.
Prints all responses directly to the console in a text-only interface.
"""

def display_response(text: str):
    """
    Prints the AI's response directly to the console.
    """
    if not text or not text.strip():
        return
    print(f"SUNDAY: {text}")
