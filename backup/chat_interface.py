# c:\Users\mshas\OneDrive\Desktop\SUNDAY\chat_interface.py
"""
Chat Interface Layer for SUNDAY (Text-First Rebuild).
Manages CLI inputs/outputs, implements slash commands, handles text permissions,
integrates project session memory, and routes commands to brain and action executor.
"""
import os
import sys
import string
import time
import logging
from vision_engine import VisionSession
from hotkey_manager import HotkeyManager
from brain import BrainModule
from permission_manager import PermissionManager
from action_executor import ActionExecutor
from context_manager import ContextManager
from voice_output import speak
from memory_manager import MemoryManager
from session_manager import SessionManager

# Configure logger matching main.py setup
log = logging.getLogger("SUNDAY")

def log_msg(category: str, message: str):
    """
    Prints a structured telemetry log to the terminal and records it in sunday.log.
    Categories: INPUT, ACTION, BRAIN, VISION, MEMORY, EXECUTOR, PROJECT, SESSION
    """
    formatted = f"[{category}] {message}"
    print(formatted)
    log.info(formatted)

class ChatInterface:
    def __init__(self):
        log_msg("BRAIN", "Initializing SUNDAY components...")
        self.brain = BrainModule()
        self.permission_manager = PermissionManager()
        self.executor = ActionExecutor()
        
        # Initialize Persistent Session Manager
        self.session_manager = SessionManager()
        self.session_manager.load_session()
        log_msg("SESSION", "Persistent session state loaded successfully.")
        log_msg("PROJECT", f"Active Project: '{self.session_manager.current_project or 'None'}' | Goal: '{self.session_manager.active_goal or 'None'}'")
        
        # Initialize background Vision session and global Hotkeys
        self.vision_session = VisionSession()
        self.hotkey_manager = HotkeyManager(self.vision_session)
        
        # Track multi-turn conversational command assembly
        self.pending_task = None
        self.task_turns = 0

    def run(self):
        """Starts the main interactive text-first execution loop."""
        log_msg("BRAIN", "SUNDAY Text-First Agent is fully online.")
        print("\n" + "="*60)
        print("               WELCOME TO SUNDAY (TEXT-FIRST AGENT)")
        print("="*60)
        print("Type /help to see all available commands.")
        print("Press Ctrl+C or type /exit to shut down.")
        print("="*60 + "\n")

        try:
            while True:
                try:
                    command_text = input("You: ").strip()
                except (KeyboardInterrupt, EOFError):
                    print()
                    self.shutdown()
                    break

                if not command_text:
                    continue

                # 1. Telemetry Log of User Input
                log_msg("INPUT", command_text)

                # 2. Check for Slash Commands
                if command_text.startswith("/"):
                    self.handle_slash_command(command_text)
                    continue

                # 3. Process Standard command
                self.process_command(command_text)

        except Exception as e:
            log_msg("BRAIN", f"Critical interface loop exception: {e}")
            import traceback
            traceback.print_exc()

    def handle_slash_command(self, cmd_text: str):
        """Parses and executes slash commands."""
        parts = cmd_text.split(" ", 1)
        command = parts[0].lower()
        args = parts[1].strip() if len(parts) > 1 else ""

        if command in ["/exit", "/quit"]:
            self.shutdown()
            sys.exit(0)

        elif command == "/help":
            print("\n" + "-"*40)
            print(" Available Commands:")
            print("  /project <name>        - Set the active working project")
            print("  /goal <description>    - Set the active project goal")
            print("  /task add <task>       - Add a new active task")
            print("  /task done <task>      - Complete an active task")
            print("  /tasks                 - List all current active tasks")
            print("  /status                - Render the current session status board")
            print("  /learn <info>          - Remember new facts or instructions (Sage Mode)")
            print("  /remember <info>       - Alias for /learn")
            print("  /recall <topic>        - Fetch precise learned knowledge by topic")
            print("  /searchmemory <query>  - Search learned context by keyword")
            print("  /vision                - Extract and display the current screen context")
            print("  /help                  - Show this help reference sheet")
            print("  /exit or /quit         - Gracefully exit the assistant")
            print("-"*40 + "\n")

        elif command == "/project":
            if not args:
                speak("Usage: /project <project_name>")
                return
            self.session_manager.set_project(args)
            log_msg("PROJECT", f"Active project updated: '{args}'")
            speak(f"Project set to: {args}")

        elif command == "/goal":
            if not args:
                speak("Usage: /goal <goal_description>")
                return
            self.session_manager.set_goal(args)
            log_msg("PROJECT", f"Active goal updated: '{args}'")
            speak(f"Active goal set to: {args}")

        elif command == "/task":
            if not args:
                speak("Usage: /task add <task_name> or /task done <task_name>")
                return
                
            sub_parts = args.split(" ", 1)
            sub_cmd = sub_parts[0].lower()
            sub_args = sub_parts[1].strip() if len(sub_parts) > 1 else ""
            
            if sub_cmd == "add":
                if not sub_args:
                    speak("Usage: /task add <task_description>")
                    return
                self.session_manager.add_task(sub_args)
                log_msg("PROJECT", f"Added task: '{sub_args}'")
                speak(f"Task added: {sub_args}")
                
            elif sub_cmd == "done":
                if not sub_args:
                    speak("Usage: /task done <task_description_or_substring>")
                    return
                removed = self.session_manager.complete_task(sub_args)
                if removed:
                    log_msg("PROJECT", f"Completed task: '{removed}'")
                    speak(f"Task completed: {removed}")
                else:
                    speak(f"No active task found matching '{sub_args}'.")
            else:
                speak(f"Unknown task action '{sub_cmd}'. Use 'add' or 'done'.")

        elif command == "/tasks":
            print("\n" + "-"*45)
            print(" SUNDAY ACTIVE TASK LIST:")
            if self.session_manager.open_tasks:
                for idx, t in enumerate(self.session_manager.open_tasks):
                    print(f"  [{idx+1}] {t}")
            else:
                print("  No active tasks found. Type /task add <task> to begin.")
            print("-"*45 + "\n")

        elif command == "/status":
            print("\n" + "="*60)
            print("              SUNDAY ACTIVE SESSION STATUS")
            print("="*60)
            print(f"Project:        {self.session_manager.current_project or 'None'}")
            print(f"Active Goal:    {self.session_manager.active_goal or 'None'}")
            
            print("Open Tasks:     ", end="")
            if self.session_manager.open_tasks:
                for idx, t in enumerate(self.session_manager.open_tasks):
                    prefix = "" if idx == 0 else "                "
                    print(f"{prefix}{idx+1}. {t}")
            else:
                print("None")
                
            print(f"Recent Context: {' -> '.join(self.session_manager.recent_context) if self.session_manager.recent_context else 'None'}")
            print(f"Last Action:    {self.session_manager.last_action or 'None'}")
            print(f"Last Session:   {self.session_manager.last_session_time or 'None'}")
            print("="*60 + "\n")

        elif command in ["/learn", "/remember"]:
            if not args:
                speak("Usage: /learn <information you want me to remember>")
                return
            log_msg("MEMORY", f"Storing knowledge: '{args}'")
            MemoryManager.save_knowledge(args, model=self.brain.active_model)
            speak("Knowledge stored.")

        elif command == "/recall":
            if not args:
                speak("Usage: /recall <topic>")
                return
            log_msg("MEMORY", f"Recalling topic: '{args}'")
            matches = MemoryManager.recall_knowledge(args)
            if matches:
                speak(f"Here is what I found for '{args}':")
                for entry in matches:
                    print(f" - [{entry['topic']}] {entry['content']} (saved {entry.get('timestamp', 'unknown')[:10]})")
            else:
                speak(f"I couldn't recall anything about '{args}'.")

        elif command == "/searchmemory":
            if not args:
                speak("Usage: /searchmemory <query>")
                return
            log_msg("MEMORY", f"Searching memory for query: '{args}'")
            matches = MemoryManager.search_knowledge(args)
            if matches:
                speak(f"Found {len(matches)} matching memories:")
                for entry in matches:
                    print(f" - [{entry['topic']}] {entry['content']}")
            else:
                speak(f"I couldn't find any memories matching '{args}'.")

        elif command == "/vision":
            # Parse sub-command arguments
            sub_args = args.strip().split(" ", 1)
            sub_cmd = sub_args[0].lower() if sub_args[0] else ""
            rem_args = sub_args[1].strip() if len(sub_args) > 1 else ""
            
            # If no sub-command, run a basic spatial scan
            if not sub_cmd:
                log_msg("VISION", "Executing standard active window scan...")
                result = self.executor.execute("vision_scan", {})
                if isinstance(result, dict) and result.get("success"):
                    data = result.get("data", {})
                    print("\n" + "="*50)
                    print("         SUNDAY ON-DEMAND SPATIAL SCAN")
                    print("="*50)
                    print(f"Active Application: {data.get('app', 'None')}")
                    print(f"Active Window:      {data.get('title', 'None')}")
                    print(f"Cursor Position:    {data.get('mouse', [0,0])}")
                    print(f"Element count:      {len(data.get('elements', []))}")
                    print("="*50 + "\n")
                else:
                    speak("Active window scan failed.")
                    
            elif sub_cmd == "summary":
                log_msg("VISION", "Generating structured screen layout summary...")
                result = self.executor.execute("vision_scan", {})
                if isinstance(result, dict) and result.get("success"):
                    data = result.get("data", {})
                    print(f"\n[VISION SUMMARY]:\n{data.get('summary')}\n")
                else:
                    speak("Failed to generate screen summary.")
                    
            elif sub_cmd == "element":
                log_msg("VISION", "Scanning visible control element bounding boxes...")
                result = self.executor.execute("vision_scan", {})
                if isinstance(result, dict) and result.get("success"):
                    data = result.get("data", {})
                    elements = data.get("elements", [])
                    print("\n" + "-"*55)
                    print(" Tracked UI Element Controls:")
                    if elements:
                        # Display up to 15 items for readability
                        for idx, e in enumerate(elements[:15]):
                            focused_marker = " [FOCUSED]" if e.get("focused") else ""
                            print(f"  [{idx+1}] {e.get('name')} ({e.get('type')}) - bbox: {e.get('bbox')}{focused_marker}")
                        if len(elements) > 15:
                            print(f"  ... and {len(elements) - 15} more controls.")
                    else:
                        print("  No visible controls detected.")
                    print("-"*55 + "\n")
                else:
                    speak("Failed to scan elements.")
                    
            elif sub_cmd == "window":
                log_msg("VISION", "Initiating window-aware crop capture...")
                result = self.executor.execute("window_screenshot", {"title": rem_args})
                if isinstance(result, dict) and result.get("success"):
                    speak(f"Screenshot complete: {result.get('message')}")
                else:
                    speak("Window screenshot capture failed.")
                    
            elif sub_cmd == "region":
                if not rem_args:
                    speak("Usage: /vision region <x> <y> <w> <h>")
                    return
                try:
                    coords = [int(c) for c in rem_args.split()]
                    if len(coords) < 4:
                        speak("Usage: /vision region <x> <y> <w> <h>")
                        return
                    x, y, w, h = coords[:4]
                    result = self.executor.execute("ocr_region", {"x": x, "y": y, "w": w, "h": h})
                    if isinstance(result, dict) and result.get("success"):
                        print(f"\n[REGION OCR TEXT]:\n{result.get('text')}\n")
                    else:
                        speak("Selective area OCR failed.")
                except Exception as e:
                    speak(f"Usage error: {str(e)}")

        else:
            speak(f"Unknown command '{command}'. Type /help to see all options.")

    def process_command(self, command_text: str):
        """Processes standard natural language commands."""
        normalized_cmd = command_text.lower().translate(str.maketrans('', '', string.punctuation)).strip()

        # Update rolling session contexts
        self.session_manager.add_context(command_text)

        # Capture active window and system titles context
        context = {
            "active_window": ContextManager.get_active_window_title(),
            "open_windows": ContextManager.get_all_window_titles(),
            "screen_text": "",
            "project_memory": self.session_manager.get_prompt_context() # Inject active project state!
        }

        # Check for visual context triggers
        screen_triggers = ["what is on my screen", "whats on my screen", "explain this", "read my screen"]
        if any(t in normalized_cmd for t in screen_triggers):
            log_msg("VISION", "Screen query detected. Capturing visual context...")
            if self.vision_session.context:
                summary = self.vision_session.context.get("summary", "")
                important = self.vision_session.context.get("important_text", "")
                context["screen_text"] = f"{summary}\nImportant: {important}" if summary else self.vision_session.context.get("ocr_text", "")
            else:
                context["screen_text"] = ContextManager.read_screen_text()
            log_msg("VISION", f"Visual context updated (length: {len(context['screen_text'])} chars)")

        # Evaluate rules/shortcut engine to bypass LLM latency
        intent_data = None
        if not self.pending_task:
            intent_data = self.executor.evaluate_shortcut(command_text)
            if intent_data:
                log_msg("ACTION", f"Shortcut match: {intent_data['intent']}")
                intent_data["is_complete"] = True

        # Process through Ollama Brain Module if shortcut was not found
        if not intent_data:
            brain_start = time.time()
            if self.pending_task:
                self.task_turns += 1
                if self.task_turns > 3:
                    speak("Task taking too long. Resetting task context.")
                    self.pending_task = None
                    self.task_turns = 0
                    return
                log_msg("BRAIN", "Processing follow-up command for pending task.")
                intent_data = self.brain.process_command(command_text, context, self.pending_task)
            else:
                log_msg("BRAIN", f"Querying Ollama with active model '{self.brain.active_model}'...")
                intent_data = self.brain.process_command(command_text, context)
            brain_elapsed = time.time() - brain_start
            log_msg("BRAIN", f"Reasoning analysis complete. Brain latency: {brain_elapsed:.2f}s")

        if not isinstance(intent_data, dict):
            intent_data = {"intent": "unknown", "is_complete": True}

        is_complete = intent_data.get("is_complete", True)

        if not is_complete:
            self.pending_task = intent_data
            log_msg("BRAIN", f"Information incomplete. Prompting follow-up: '{intent_data.get('follow_up_question')}'")
            speak(intent_data.get("follow_up_question", "Please provide more details."))
            return

        self.pending_task = None
        self.task_turns = 0

        intent = intent_data.get("intent", "unknown")
        parameters = intent_data.get("parameters", {})
        sensitivity = intent_data.get("sensitivity", 0)
        reply_text = intent_data.get("reply_text", "")

        log_msg("ACTION", f"Parsed Intent: '{intent}' (Sensitivity: {sensitivity})")

        # Update last executed action in session manager
        self.session_manager.set_last_action(intent)

        if intent == "unknown":
            speak("I didn't understand that command.")
            return

        if intent == "general_query" and reply_text:
            speak(reply_text)
            return

        # Perform authorization checks
        permission_granted = self.permission_manager.request_permission(
            intent=intent, parameters=parameters, sensitivity=sensitivity
        )

        if permission_granted:
            log_msg("EXECUTOR", f"Executing action for intent '{intent}'...")
            exec_start = time.time()
            result = self.executor.execute(intent, parameters, context)
            exec_elapsed = time.time() - exec_start
            
            # Standard return validation
            if isinstance(result, dict):
                success = result.get("success", True)
                message = result.get("message", "")
                if success:
                    log_msg("EXECUTOR", f"Action succeeded in {exec_elapsed:.2f}s: {message}")
                else:
                    log_msg("EXECUTOR ERROR", f"Action failed in {exec_elapsed:.2f}s: {message}")
            else:
                log_msg("EXECUTOR", f"Action completed in {exec_elapsed:.2f}s.")
                
            if intent not in ["solve_query"]:
                speak("Done.")
        else:
            log_msg("EXECUTOR", "Action execution aborted by user.")
            speak("Action aborted.")

    def shutdown(self):
        """Cleans up and stops the vision background processes."""
        speak("Ending session. Bye boss")
        try:
            self.vision_session.stop()
        except Exception:
            pass
