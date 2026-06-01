# c:\Users\mshas\OneDrive\Desktop\SUNDAY\execution\permission_manager.py
"""
Permission Manager for SUNDAY (Text-First Mode).
Handles authorization requests via terminal console input.
"""
from interface.console_output import display_response

class PermissionManager:
    def __init__(self):
        pass

    def request_permission(self, intent: str, parameters: dict, sensitivity: int) -> bool:
        """
        Evaluates if an action is allowed.
        Prompts the user via CLI if authorization is required.
        Returns True if allowed, False if denied.
        """
        if sensitivity == 0:
            return True
            
        if sensitivity == 1:
            # For level 1 (system apps), safe ones are auto-approved
            safe_apps = ["notepad", "calculator", "browser"]
            app_name = parameters.get("app_name", "").lower()
            if app_name in safe_apps:
                return True

        # Level 2 or unsafe Level 1: Prompt user
        if intent == "read_file":
            target = parameters.get("file_name", parameters.get("file_path", "a file"))
            prompt = f"You are asking me to read {target}. Do you grant permission?"
        elif intent in ["open_app", "open"]:
            app = parameters.get("app_name", "an application")
            prompt = f"You are asking me to open {app}. Do you grant permission?"
        elif intent in ["type_text", "type", "write", "write_text"]:
            text_to_type = parameters.get("text", "")
            if len(text_to_type) > 50 or "\n" in text_to_type:
                prompt = "Should I type this code?"
            else:
                prompt = f"Should I type: {text_to_type}?"
        elif intent in ["system_shutdown", "system_restart", "system_sleep"]:
            action = intent.split("_")[1]
            prompt = f"Are you sure you want to {action}?"
        else:
            prompt = "This action requires your permission. Do you allow it?"

        # Output confirmation block
        print("\n" + "="*50)
        print(" [CONFIRMATION REQUIRED]")
        print("="*50)
        print(f"Prompt: {prompt}\n")
        print("Type:")
        print("YES")
        print("to proceed.")
        print("or")
        print("NO")
        print("to cancel.")
        print("="*50)

        try:
            response = input("Confirm (YES/NO): ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            print("\nPermission prompt interrupted. Aborting.")
            return False

        # Strict validation for power commands
        if intent in ["system_shutdown", "system_restart", "system_sleep"]:
            if response == "yes confirm" or response == "yes":
                display_response("Confirmation received. Proceeding.")
                return True
            else:
                display_response("Confirmation failed. Action aborted.")
                return False

        # Standard validation for other commands
        if response in ["yes", "y", "allow", "ok", "okay", "sure"]:
            display_response("Permission granted.")
            return True
        else:
            display_response("Permission denied.")
            return False
