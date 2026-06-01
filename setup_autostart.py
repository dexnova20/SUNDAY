import os
import sys
import winreg

def setup_autostart():
    """
    Adds a registry key to start SUNDAY automatically on system boot.
    Uses pythonw.exe to run without a console window.
    """
    app_name = "SUNDAY_Assistant"
    
    # Path to the python executable
    python_path = sys.executable
        
    main_script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "main.py"))
    
    # The command to execute on boot: start a minimized console window
    # Windows Privacy Settings block invisible background apps from using the microphone,
    # so we must spawn a minimized cmd window to be granted microphone access!
    command = f'cmd.exe /c start "SUNDAY Assistant" /min "{python_path}" "{main_script_path}" --boot'
    
    print(f"Setting up auto-start for: {command}")
    
    try:
        # Open the Run registry key
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE
        )
        
        # Set the value
        winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, command)
        winreg.CloseKey(key)
        
        print("Successfully added SUNDAY to Windows startup.")
    except Exception as e:
        print(f"Failed to add to startup: {e}")

def remove_autostart():
    """Removes the registry key."""
    app_name = "SUNDAY_Assistant"
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE
        )
        winreg.DeleteValue(key, app_name)
        winreg.CloseKey(key)
        print("Successfully removed SUNDAY from Windows startup.")
    except FileNotFoundError:
        print("SUNDAY is not in startup.")
    except Exception as e:
        print(f"Failed to remove from startup: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--remove":
        remove_autostart()
    else:
        setup_autostart()
