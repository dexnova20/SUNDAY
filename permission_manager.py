from voice_output import speak
from audio_manager import AudioManager

class PermissionManager:
    def __init__(self, audio_manager: AudioManager):
        self.audio_manager = audio_manager

    def request_permission(self, intent: str, parameters: dict, sensitivity: int) -> bool:
        """
        Evaluates if an action is allowed.
        Returns True if allowed, False if denied.
        """
        if sensitivity == 0:
            return True
            
        if sensitivity == 1:
            # For level 1 (system apps), we can auto-approve safe ones.
            safe_apps = ["notepad", "calculator", "browser"]
            app_name = parameters.get("app_name", "").lower()
            if app_name in safe_apps:
                return True
            # Otherwise prompt

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
            prompt = f"Are you sure you want to {action}? Say 'yes confirm' to proceed."
        else:
            prompt = "This action requires your permission. Do you allow it?"

        speak(prompt)
        
        # Listen for response
        response = self.audio_manager.listen_and_transcribe().lower()
        
        # Strict validation for power commands
        if intent in ["system_shutdown", "system_restart", "system_sleep"]:
            import string
            normalized = response.translate(str.maketrans('', '', string.punctuation)).strip()
            if normalized == "yes confirm":
                speak("Confirmation received. Proceeding.")
                return True
            else:
                speak("Confirmation failed. Action aborted.")
                return False
        
        # Standard validation for other commands
        if "yes" in response or "allow" in response or "sure" in response or "okay" in response:
            speak("Permission granted.")
            return True
        else:
            speak("Permission denied.")
            return False
