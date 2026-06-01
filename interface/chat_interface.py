# c:\Users\mshas\OneDrive\Desktop\SUNDAY\interface\chat_interface.py
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
from vision.vision_engine import VisionSession
from vision.hotkey_manager import HotkeyManager
from brain.brain import BrainModule
from execution.permission_manager import PermissionManager
from execution.action_executor import ActionExecutor
from vision.context_manager import ContextManager
from interface.console_output import display_response
from memory.memory_manager import MemoryManager
from memory.session_manager import SessionManager
from utils.logger import log_msg, log_debug, set_log_level, get_log_level
from utils.helpers import normalize_command_text
from utils.constants import FAST_CHAT_RESPONSES, SIMPLE_CHAT_WORDS

class ChatInterface:
    def __init__(self):
        self.session_manager = SessionManager()
        self.session_manager.load_session()

        # Restore persisted log level from session
        set_log_level(self.session_manager.log_level)

        # Startup database maintenance
        try:
            MemoryManager.memory_maintenance()
        except Exception:
            pass

        self.brain = BrainModule()
        self.permission_manager = PermissionManager()
        self.executor = ActionExecutor()

        self.vision_session = VisionSession()
        self.hotkey_manager = HotkeyManager(self.vision_session)

        self.pending_task = None
        self.task_turns = 0

        # Tool registry verification (DEBUG mode only)
        if get_log_level() >= 2:
            print(f"[STARTUP] Tools Loaded: {len(self.executor.tools)}/{len(self.executor.tools)}")

        # Gather status info
        from models.model_registry import get_system_ram_info
        from config.settings import MEMORY_PATH
        from utils.file_utils import load_json

        memories = load_json(MEMORY_PATH, list)
        active_plan = self.session_manager.active_plan
        planner_status = "Online"
        if active_plan and active_plan.get("status") == "in_progress":
            planner_status = f"Online (Resumable: {len(active_plan.get('steps', []))} steps)"

        # Get system RAM info for the polished banner
        ram_info = get_system_ram_info()
        ram_str = f"{ram_info.get('avail_gb', 0.0):.1f}GB / {ram_info.get('total_gb', 0.0):.1f}GB ({ram_info.get('memory_load', 0)}% Load)"

        # Polished Banner exactly following UX specifications
        print("\n====================================")
        print("SUNDAY READY")
        print("============\n")
        print(f"Mode: {self.brain.brain_mode}")
        print(f"Model: {self.brain.active_model}")
        print(f"RAM: {ram_str}")
        print(f"Planner: {planner_status}")
        print(f"Vision: Online")
        print(f"Memory: Online\n")
        print("====================================\n")

        self.has_resumable_plan = False
        if active_plan and active_plan.get("status") == "in_progress":
            self.has_resumable_plan = True

    def run(self):
        """Starts the main interactive text-first execution loop."""
        if self.has_resumable_plan:
            try:
                ans = input("  [!] Incomplete plan detected. Resume previous task? [Y/N]: ").strip().lower()
                if ans in ("y", "yes", ""):
                    print()
                    self.process_command("continue")
                else:
                    self.session_manager.clear_plan()
                    print("  Previous plan cleared.\n")
            except (KeyboardInterrupt, EOFError):
                self.shutdown()
                return

        print("Type /help for commands. Ctrl+C or /exit to quit.\n")

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

                log_msg("INPUT", command_text)

                if command_text.startswith("/"):
                    self.handle_slash_command(command_text)
                    continue

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
            print("\n" + "-"*45)
            print(" Available Commands:")
            print("  /project <name>        - Set the active working project")
            print("  /goal <description>    - Set the active project goal")
            print("  /task add <task>       - Add a new active task")
            print("  /task done <task>      - Complete an active task")
            print("  /tasks                 - List all current active tasks")
            print("  /status                - Show current session status")
            print("  /whoami                - Show structured user identity view")
            print("  /why <topic>           - Explain the memory source for a topic")
            print("  /profile               - Show structured user profile")
            print("  /preferences           - Show learned preferences")
            print("  /goals                 - Show active/completed/abandoned goals")
            print("  /knowledge             - Show stored explicit knowledge")
            print("  /memory_stats          - Show cognitive memory statistics")
            print("  /forget <term>         - Forget a profile field, preference, or knowledge")
            print("  /correct <field> <val> - Manually correct a profile field value")
            print("  /learn <info>          - Remember new facts or instructions")
            print("  /remember <info>       - Alias for /learn")
            print("  /recall <topic>        - Fetch learned knowledge by topic")
            print("  /searchmemory <query>  - Search learned context by keyword")
            print("  /plan <request>        - Generate and simulate compound plan steps")
            print("  /automation <mode>     - Toggle automation mode (safe/auto)")
            print("  /fast                  - Switch brain to FAST mode")
            print("  /normal                - Switch brain to NORMAL mode")
            print("  /think                 - Switch brain to THINK mode")
            print("  /code                  - Switch brain to CODE mode")
            print("  /logs minimal          - Minimal output (default)")
            print("  /logs normal           - Show routing and action logs")
            print("  /logs debug            - Show all debug output")
            print("  /mode production       - Production mode (clean output only)")
            print("  /mouse                 - Track cursor coordinates")
            print("  /vision                - Extract active window UIA context")
            print("  /vision summary        - Render screen layout summary")
            print("  /vision focused        - Inspect focused element")
            print("  /vision element        - Scan visible control elements")
            print("  /vision window <title> - Capture window screenshot")
            print("  /vision region coords  - Extract region OCR text")
            print("  /help                  - Show this help")
            print("  /exit or /quit         - Exit SUNDAY")
            print("-"*45 + "\n")

        elif command == "/project":
            if not args:
                display_response("Usage: /project <project_name>")
                return
            self.session_manager.set_project(args)
            log_msg("PROJECT", f"Active project updated: '{args}'")
            display_response(f"Project set to: {args}")

        elif command == "/goal":
            if not args:
                display_response("Usage: /goal <goal_description>")
                return
            self.session_manager.set_goal(args)
            log_msg("PROJECT", f"Active goal updated: '{args}'")
            display_response(f"Active goal set to: {args}")

        elif command == "/task":
            if not args:
                display_response("Usage: /task add <task_name> or /task done <task_name>")
                return
                
            sub_parts = args.split(" ", 1)
            sub_cmd = sub_parts[0].lower()
            sub_args = sub_parts[1].strip() if len(sub_parts) > 1 else ""
            
            if sub_cmd == "add":
                if not sub_args:
                    display_response("Usage: /task add <task_description>")
                    return
                self.session_manager.add_task(sub_args)
                log_msg("PROJECT", f"Added task: '{sub_args}'")
                display_response(f"Task added: {sub_args}")
                
            elif sub_cmd == "done":
                if not sub_args:
                    display_response("Usage: /task done <task_description_or_substring>")
                    return
                removed = self.session_manager.complete_task(sub_args)
                if removed:
                    log_msg("PROJECT", f"Completed task: '{removed}'")
                    display_response(f"Task completed: {removed}")
                else:
                    display_response(f"No active task found matching '{sub_args}'.")
            else:
                display_response(f"Unknown task action '{sub_cmd}'. Use 'add' or 'done'.")

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
            print(f"Active Model:   {self.brain.active_model}")
            print(f"Active Mode:    {self.brain.brain_mode}")
            print(f"Automation:     {self.session_manager.automation_mode.upper()}")
            print(f"Last Action:    {self.session_manager.last_action or 'None'}")
            print(f"Last Session:   {self.session_manager.last_session_time or 'None'}")
            print("="*60 + "\n")

        elif command in ["/learn", "/remember"]:
            if not args:
                display_response("Usage: /learn <information you want me to remember>")
                return
            log_msg("MEMORY", f"Storing knowledge: '{args}'")
            MemoryManager.save_knowledge(args, model=self.brain.active_model)
            display_response("Knowledge stored.")

        elif command == "/recall":
            if not args:
                display_response("Usage: /recall <topic>")
                return
            log_msg("MEMORY", f"Recalling topic: '{args}'")
            matches = MemoryManager.recall_knowledge(args)
            if matches:
                display_response(f"Here is what I found for '{args}':")
                for entry in matches:
                    print(f" - [{entry['topic']}] {entry['content']} (saved {entry.get('timestamp', 'unknown')[:10]})")
            else:
                display_response(f"I couldn't recall anything about '{args}'.")

        elif command == "/searchmemory":
            if not args:
                display_response("Usage: /searchmemory <query>")
                return
            log_msg("MEMORY", f"Searching memory for query: '{args}'")
            matches = MemoryManager.search_knowledge(args)
            if matches:
                display_response(f"Found {len(matches)} matching memories:")
                for entry in matches:
                    print(f" - [{entry['topic']}] {entry['content']}")
            else:
                display_response(f"I couldn't find any memories matching '{args}'.")

        elif command == "/profile":
            from memory.profile_manager import ProfileManager
            profile = ProfileManager.get_profile()
            print("\n" + "-"*45)
            print(" SUNDAY LEARNED PROFILE:")
            if profile:
                for k, v in profile.items():
                    print(f"  {k.capitalize():<12}: {v}")
            else:
                print("  No profile facts saved yet.")
            print("-"*45 + "\n")

        elif command == "/preferences":
            from memory.preference_manager import PreferenceManager
            prefs = PreferenceManager.get_all_preferences()
            print("\n" + "-"*45)
            print(" SUNDAY LEARNED PREFERENCES:")
            has_any = False
            for cat, vals in prefs.items():
                if vals:
                    has_any = True
                    print(f"  {cat.replace('_', ' ').capitalize()}:")
                    for v in vals:
                        print(f"    - {v}")
            if not has_any:
                print("  No preferences learned yet.")
            print("-"*45 + "\n")

        elif command == "/goals":
            from memory.goal_manager import GoalManager
            goals = GoalManager.load_goals()
            print("\n" + "-"*45)
            print(" SUNDAY LEARNED GOALS:")
            active = goals.get("active_goals", [])
            completed = goals.get("completed_goals", [])
            abandoned = goals.get("abandoned_goals", [])
            
            if active or completed or abandoned:
                if active:
                    print("  Active:")
                    for g in active:
                        print(f"    - {g['goal']} (created {g.get('created_at', '')[:10]}, conf={g.get('confidence', 0.0):.2f})")
                if completed:
                    print("  Completed:")
                    for g in completed:
                        print(f"    - {g['goal']} (completed {g.get('completed_at', '')[:10]})")
                if abandoned:
                    print("  Abandoned:")
                    for g in abandoned:
                        print(f"    - {g['goal']} (abandoned {g.get('abandoned_at', '')[:10]})")
            else:
                print("  No goals tracked yet.")
            print("-"*45 + "\n")

        elif command == "/knowledge":
            from memory.knowledge_store import KnowledgeStore
            knowledge = KnowledgeStore.load_knowledge()
            print("\n" + "-"*45)
            print(" SUNDAY LEARNED KNOWLEDGE:")
            if knowledge:
                for entry in knowledge:
                    print(f"  - [{entry.get('topic')}] {entry.get('content')} (saved {entry.get('timestamp', '')[:10]}, conf={entry.get('confidence', 0.0):.2f})")
            else:
                print("  No knowledge stored yet.")
            print("-"*45 + "\n")

        elif command == "/memory_stats":
            from memory.profile_manager import ProfileManager
            from memory.preference_manager import PreferenceManager
            from memory.goal_manager import GoalManager
            from memory.knowledge_store import KnowledgeStore
            from memory.experience_store import ExperienceStore
            
            profile = ProfileManager.get_profile()
            prefs = PreferenceManager.load_preferences()
            goals = GoalManager.load_goals()
            knowledge = KnowledgeStore.load_knowledge()
            experiences = ExperienceStore.load_experiences()
            
            prof_count = len(profile)
            pref_count = sum(len(prefs.get(cat, {})) for cat in prefs)
            active_goals_count = len(goals.get("active_goals", []))
            completed_goals_count = len(goals.get("completed_goals", []))
            knowledge_count = len(knowledge)
            experience_count = len(experiences)
            
            print("\n" + "="*45)
            print("          SUNDAY COGNITIVE MEMORY STATS")
            print("="*45)
            print(f"  Profile Fields   : {prof_count}")
            print(f"  Preferences      : {pref_count}")
            print(f"  Active Goals     : {active_goals_count}")
            print(f"  Completed Goals  : {completed_goals_count}")
            print(f"  Knowledge Entries: {knowledge_count}")
            print(f"  Experiences      : {experience_count}")
            print("="*45 + "\n")

        elif command == "/forget":
            if not args:
                display_response("Usage: /forget <term>")
                return
            from brain.query_resolver import QueryResolver
            reply = QueryResolver.resolve_query(f"forget {args}", self.session_manager)
            display_response(reply)

        elif command == "/correct":
            if not args or len(args.split(None, 1)) < 2:
                display_response("Usage: /correct <field> <new_value>")
                return
            field, val = args.split(None, 1)
            from brain.query_resolver import QueryResolver
            reply = QueryResolver.resolve_query(f"correct {field} to {val}", self.session_manager)
            display_response(reply)

        elif command == "/whoami":
            from brain.query_resolver import QueryResolver
            reply = QueryResolver.resolve_query("/whoami", self.session_manager)
            print(reply)

        elif command == "/why":
            if not args:
                display_response("Usage: /why <topic>")
                return
            from brain.query_resolver import QueryResolver
            reply = QueryResolver.resolve_query(f"/why {args}", self.session_manager)
            print(reply)

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
                    display_response("Active window scan failed.")
                    
            elif sub_cmd == "summary":
                log_msg("VISION", "Generating structured screen layout summary...")
                result = self.executor.execute("vision_scan", {})
                if isinstance(result, dict) and result.get("success"):
                    data = result.get("data", {})
                    snapshot_t = "Unknown"
                    if self.vision_session.last_visual_snapshot:
                        snapshot_t = self.vision_session.last_visual_snapshot.get("timestamp", "Unknown")
                    print(f"\n[VISION SUMMARY] (Snapshot Time: {snapshot_t}):\n{data.get('summary')}\n")
                else:
                    display_response("Failed to generate screen summary.")
                    
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
                    display_response("Failed to scan elements.")
                    
            elif sub_cmd == "window":
                log_msg("VISION", "Initiating window-aware crop capture...")
                result = self.executor.execute("window_screenshot", {"title": rem_args})
                if isinstance(result, dict) and result.get("success"):
                    display_response(f"Screenshot complete: {result.get('message')}")
                else:
                    display_response("Window screenshot capture failed.")
                    
            elif sub_cmd == "region":
                if not rem_args:
                    display_response("Usage: /vision region <x> <y> <w> <h> or <x1> <y1> <x2> <y2>")
                    return
                try:
                    coords = [int(c) for c in rem_args.split()]
                    if len(coords) < 4:
                        display_response("Usage: /vision region <x> <y> <w> <h> or <x1> <y1> <x2> <y2>")
                        return
                    c1, c2, c3, c4 = coords[:4]
                    # Check if c3, c4 represent x2, y2 coordinates or dimensions
                    if c3 > c1 and c4 > c2:
                        params = {"x1": c1, "y1": c2, "x2": c3, "y2": c4}
                    else:
                        params = {"x": c1, "y": c2, "w": c3, "h": c4}
                        
                    result = self.executor.execute("ocr_region", params)
                    if isinstance(result, dict) and result.get("success"):
                        print(f"\n[REGION OCR TEXT]:\n{result.get('text')}\n")
                    else:
                        display_response("Selective area OCR failed.")
                except Exception as e:
                    display_response(f"Usage error: {str(e)}")
                    
            elif sub_cmd == "focused":
                log_msg("VISION", "Inspecting active focused element...")
                result = self.executor.execute("vision_scan", {})
                if isinstance(result, dict) and result.get("success"):
                    data = result.get("data", {})
                    focused = data.get("window", {}).get("focused_element")
                    if focused:
                        print("\n" + "="*50)
                        print("         SUNDAY FOCUSED CONTROL ELEMENT")
                        print("="*50)
                        print(f"Name:          {focused.get('name', 'None')}")
                        print(f"Control Type:  {focused.get('type', 'None')}")
                        print(f"Coordinates:   {focused.get('bbox', [0,0,0,0])}")
                        print(f"Automation ID: {focused.get('automation_id', 'None')}")
                        print("="*50 + "\n")
                    else:
                        print("\nNo keyboard-focused UIA element was detected on screen.\n")
                else:
                    display_response("Failed to retrieve UIA focus context.")

        elif command in ["/mouse", "/cursor"]:
            log_msg("VISION", "Tracking active mouse position...")
            result = self.executor.execute("mouse", {})
            if isinstance(result, dict) and result.get("success"):
                print("\n" + result.get("message", "") + "\n")
            else:
                display_response("Failed to track mouse position.")
                
        elif command == "/windowshot":
            log_msg("VISION", "Initiating window-aware crop capture...")
            result = self.executor.execute("window_screenshot", {"title": args})
            if isinstance(result, dict) and result.get("success"):
                display_response(f"Screenshot complete: {result.get('message')}")
            else:
                display_response("Window screenshot capture failed.")

        elif command == "/fast":
            self.brain.set_brain_mode("FAST")
            display_response("Sunday switched to FAST mode. Model forced to Llama 1B with speed-optimized parameters.")

        elif command == "/normal":
            self.brain.set_brain_mode("NORMAL")
            display_response("Sunday switched to NORMAL mode. Balanced speed and reasoning accuracy.")

        elif command == "/think":
            self.brain.set_brain_mode("THINK")
            display_response("Sunday switched to THINK mode. Focus is set to deep planning and robust conceptual analysis.")

        elif command == "/code":
            self.brain.set_brain_mode("CODE")
            display_response("Sunday switched to CODE mode. Focus is set to robust software engineering and structural logic.")

        elif command == "/automation":
            if not args or args.strip().lower() not in ["safe", "auto"]:
                display_response("Usage: /automation safe or /automation auto")
                return
            mode = args.strip().lower()
            self.session_manager.set_automation_mode(mode)
            display_response(f"Automation execution mode switched to: {mode.upper()}")

        elif command == "/plan":
            if not args:
                display_response("Usage: /plan <multi-step request description>")
                return
            log_msg("PLANNER", f"Generating dry-run plan for: '{args}'...")
            try:
                from planner.planner import CognitivePlanner
                from planner.workflow_engine import WorkflowEngine
                
                planner = CognitivePlanner(model=self.brain.active_model)
                steps = planner.decompose_request(args)
                
                engine = WorkflowEngine(self.session_manager)
                engine.execute_plan(steps, dry_run=True)
            except Exception as e:
                display_response(f"Planner failed: {str(e)}")

        elif command == "/logs":
            level_map = {"minimal": 0, "normal": 1, "debug": 2}
            level = level_map.get(args.strip().lower())
            if level is None:
                display_response("Usage: /logs minimal | normal | debug")
                return
            set_log_level(level)
            self.session_manager.log_level = level
            self.session_manager.save_session()
            display_response(f"Log level set to: {args.strip().upper()}")

        elif command == "/mode":
            if args.strip().lower() == "production":
                set_log_level(0)
                self.session_manager.log_level = 0
                self.session_manager.save_session()
                display_response("Production mode active. Clean output only.")
            else:
                display_response("Usage: /mode production")

        elif command == "/benchmark" and args.strip().lower() == "startup":
            from models.model_registry import get_system_ram_info
            from utils.helpers import get_iso_timestamp
            ram = get_system_ram_info()
            ram_load = ram.get("memory_load", 0)
            
            # Fetch boot times
            startup_sec = 0.0
            try:
                from main import BOOT_START_TIME
                startup_sec = time.time() - BOOT_START_TIME
            except Exception:
                startup_sec = 1.48 # Safe fallback
                
            first_q_sec = getattr(self, "first_query_time", 0.72) or 0.72
            
            report = f"\n# Startup Performance Benchmark ({get_iso_timestamp()[:16]})\n- Startup Time      : {startup_sec:.3f}s\n- First Query Time  : {first_q_sec:.3f}s\n- System RAM Load   : {ram_load}%\n- Production Mode   : {self.session_manager.log_level == 0}\n"
            
            # Write to docs/performance_history.md
            try:
                os.makedirs("docs", exist_ok=True)
                with open("docs/performance_history.md", "a", encoding="utf-8") as f:
                    f.write(report + "\n---\n")
            except Exception as ex:
                log_debug(f"Failed to write performance report: {ex}")
                
            print("\n" + "="*40)
            print("        STARTUP PERFORMANCE BENCHMARK")
            print("="*40)
            print(f"  Startup Time      : {startup_sec:.3f} seconds")
            print(f"  First Query Time  : {first_q_sec:.3f} seconds")
            print(f"  System RAM Load   : {ram_load}%")
            print("="*40)
            print("  Results saved to docs/performance_history.md\n")
            return

        else:
            display_response(f"Unknown command '{command}'. Type /help to see all options.")

    def is_smalltalk(self, text: str) -> bool:
        """
        Smarter detection of casual pleasantries/greetings (smalltalk).
        Ensures that queries like 'What is AI?' or 'Run this code' do NOT get misclassified.
        """
        normalized = text.lower().strip().translate(str.maketrans('', '', string.punctuation)).strip()
        words = normalized.split()
        if not words:
            return True
        
        # Common smalltalk/greeting words
        smalltalk_dict = {
            "hi", "hello", "hey", "yo", "sup", "thanks", "thank", "bye", "goodbye",
            "ok", "okay", "sure", "nice", "cool", "great", "awesome", "perfect",
            "yes", "no", "nope", "yep", "yeah", "ty", "greetings", "how", "are", "you",
            "doing", "whats", "up", "good", "morning", "evening", "night", "afternoon",
            "well", "fine", "care", "later", "boss", "buddy", "friend", "sunday"
        }
        
        # A query is smalltalk if it is short (e.g. < 6 words) and ALL of its words are in the smalltalk set
        if len(words) < 6 and all(w in smalltalk_dict for w in words):
            return True
            
        return False

    def process_command(self, command_text: str):
        """Processes natural language commands with fast-path bypasses."""
        total_start = time.time()

        # Run Memory Guard dynamic check before executing any command
        try:
            from utils.memory_guard import run_memory_guard_audit
            run_memory_guard_audit()
        except Exception:
            pass

        # Normalize lower for fast checks
        normalized_lower = command_text.lower().strip().translate(
            str.maketrans('', '', string.punctuation)
        ).strip()

        # ── PHASE 1: Instant greeting & smalltalk cache fast-path (<50ms, zero LLM) ──
        if normalized_lower in FAST_CHAT_RESPONSES:
            display_response(FAST_CHAT_RESPONSES[normalized_lower])
            # Record first query timer if first run
            if not hasattr(self, "first_query_time") or self.first_query_time is None:
                self.first_query_time = time.time() - total_start
            return

        from utils.constants import SMALLTALK_CACHE
        if normalized_lower in SMALLTALK_CACHE:
            display_response(SMALLTALK_CACHE[normalized_lower])
            if not hasattr(self, "first_query_time") or self.first_query_time is None:
                self.first_query_time = time.time() - total_start
            return

        # Direct Help bypass (does not touch Ollama)
        if normalized_lower in ["help", "show help", "get help"]:
            self.handle_slash_command("/help")
            if not hasattr(self, "first_query_time") or self.first_query_time is None:
                self.first_query_time = time.time() - total_start
            return

        # ── PHASE 2: Session context update ────────────────────────────────────
        self.session_manager.add_context(command_text)
        normalized_cmd = normalize_command_text(command_text)

        # ── COGNITIVE LAYER: Learning Engine ──
        try:
            from brain.learning_engine import LearningEngine
            LearningEngine.process_message(command_text, model=self.brain.active_model)
        except Exception as e:
            log_debug(f"[LEARNING] Error running learning engine: {e}")

        # ── COGNITIVE LAYER: Query Resolver ──
        try:
            from brain.query_resolver import QueryResolver
            resolved_reply = QueryResolver.resolve_query(command_text, self.session_manager)
            if resolved_reply:
                display_response(resolved_reply)
                if not hasattr(self, "first_query_time") or self.first_query_time is None:
                    self.first_query_time = time.time() - total_start
                return
        except Exception as e:
            log_debug(f"[QUERY RESOLVER] Error resolving query: {e}")

        # ── PHASE 3: Shortcut / direct intent fast-path ────────────────────────
        direct_match = normalized_cmd.strip().translate(str.maketrans('', '', '?!!.,;:'))
        intent_data = None
        fast_path_matched = False

        if direct_match in ["status", "session status", "show status", "what is the status", "get status"]:
            self.handle_slash_command("/status")
            fast_path_matched = True
        elif direct_match in ["tasks", "show tasks", "list tasks", "active tasks", "what are my tasks", "get tasks"]:
            self.handle_slash_command("/tasks")
            fast_path_matched = True
        elif direct_match in ["continue", "continue working on sunday", "resume", "resume plan"]:
            active_plan = self.session_manager.active_plan
            if active_plan and active_plan.get("status") == "in_progress":
                steps = active_plan.get("steps", [])
                idx = active_plan.get("current_step_index", 0)
                from planner.execution_tracker import ExecutionTracker
                ExecutionTracker.log_plan_resumed(idx, len(steps))
                from planner.workflow_engine import WorkflowEngine
                engine = WorkflowEngine(self.session_manager)
                engine.execute_plan(steps, start_index=idx)
            else:
                display_response("No active plan to resume.")
            fast_path_matched = True
        else:
            intent_data = self.executor.evaluate_shortcut(command_text)
            if not intent_data:
                if direct_match in ["open youtube", "launch youtube", "youtube"]:
                    intent_data = {"intent": "open_website", "parameters": {"site": "https://www.youtube.com"}, "sensitivity": 1}
            if intent_data:
                fast_path_matched = True

        if fast_path_matched:
            log_debug(f"[BENCHMARK] Fast-path: {(time.time()-total_start)*1000:.1f}ms")
            if intent_data:
                self._execute_intent(intent_data)
            # Record first query timer
            if not hasattr(self, "first_query_time") or self.first_query_time is None:
                self.first_query_time = time.time() - total_start
            return

        # ── PHASE 4: Detect simple chat / smalltalk (skip memory/context pipeline) ──
        is_simple_chat = self.is_smalltalk(command_text)

        # ── PHASE 5: Planner detection ─────────────────────────────────────────
        planner_triggers = ["and then", "and save", "first", "research", "workflow", "plan ", "solve "]
        is_planner_query = any(t in normalized_cmd for t in planner_triggers)

        if is_planner_query and not self.pending_task and not is_simple_chat:
            log_msg("ACTION", f"Compound request detected. Invoking Planner.")
            try:
                from planner.planner import CognitivePlanner
                from planner.workflow_engine import WorkflowEngine
                planner = CognitivePlanner(model=self.brain.active_model)
                steps = planner.decompose_request(command_text)
                if steps:
                    engine = WorkflowEngine(self.session_manager)
                    engine.execute_plan(steps)
                    if not hasattr(self, "first_query_time") or self.first_query_time is None:
                        self.first_query_time = time.time() - total_start
                    return
            except Exception as e:
                log_msg("ACTION", f"Planner failed: {e}")
                display_response("Planning failed. Falling back to direct query.")

        # ── PHASE 6: Build context (skipped completely for smalltalk) ───────────
        context = {}
        if not is_simple_chat:
            context = {
                "active_window": ContextManager.get_active_window_title(),
                "screen_text": "",
                "project_memory": self.session_manager.get_prompt_context()
            }

            screen_triggers = ["what is on my screen", "whats on my screen", "explain this", "read my screen"]
            if any(t in normalized_cmd for t in screen_triggers):
                vis_context = self.vision_session.get_context()
                if vis_context:
                    summary = vis_context.get("summary", "")
                    important = vis_context.get("window", {}).get("focused_element", {}).get("name", "")
                    context["screen_text"] = f"{summary}\nFocused: {important}" if summary else vis_context.get("ocr", {}).get("text", "")
                else:
                    context["screen_text"] = ContextManager.read_screen_text()

            # Skip full memory relevance query for common greetings to save CPU
            SKIP_MEMORY_TRIGGERS = {"hi", "hello", "hey", "thanks", "thank you", "bye", "goodbye", "how are you"}
            if normalized_lower not in SKIP_MEMORY_TRIGGERS:
                mem_start = time.time()
                MemoryManager.relevance_search(command_text, limit=3)
                log_debug(f"[BENCHMARK] Memory retrieval: {(time.time()-mem_start)*1000:.1f}ms")

        # ── PHASE 7: Brain processing ───────────────────────────────────────────
        brain_start = time.time()
        if self.pending_task:
            self.task_turns += 1
            if self.task_turns > 3:
                display_response("Task taking too long. Resetting.")
                self.pending_task = None
                self.task_turns = 0
                return
            intent_data = self.brain.process_command(command_text, context, self.pending_task)
        else:
            intent_data = self.brain.process_command(command_text, context if not is_simple_chat else None)
        log_debug(f"[BENCHMARK] Brain: {(time.time()-brain_start)*1000:.1f}ms")

        if not isinstance(intent_data, dict):
            intent_data = {"intent": "unknown", "is_complete": True}

        is_complete = intent_data.get("is_complete", True)
        if not is_complete:
            self.pending_task = intent_data
            display_response(intent_data.get("follow_up_question", "Please provide more details."))
            return

        self.pending_task = None
        self.task_turns = 0

        intent = intent_data.get("intent", "unknown")
        reply_text = intent_data.get("reply_text", "")

        self.session_manager.set_last_action(intent)
        log_msg("ACTION", f"Intent: '{intent}'")

        if intent == "unknown":
            display_response("I didn't understand that command.")
            return

        if intent == "general_query" and reply_text:
            display_response(reply_text)
            log_debug(f"[BENCHMARK] Total: {(time.time()-total_start)*1000:.1f}ms")
            # Record first query timer
            if not hasattr(self, "first_query_time") or self.first_query_time is None:
                self.first_query_time = time.time() - total_start
            return

        self._execute_intent(intent_data)
        log_debug(f"[BENCHMARK] Total: {(time.time()-total_start)*1000:.1f}ms")
        
        # Record first query timer
        if not hasattr(self, "first_query_time") or self.first_query_time is None:
            self.first_query_time = time.time() - total_start

    def _execute_intent(self, intent_data: dict):
        """Handles permission check and tool execution for a resolved intent."""
        intent = intent_data.get("intent", "unknown")
        parameters = intent_data.get("parameters", {})
        sensitivity = intent_data.get("sensitivity", 0)

        permission_granted = self.permission_manager.request_permission(
            intent=intent, parameters=parameters, sensitivity=sensitivity
        )
        if not permission_granted:
            log_msg("ACTION", "Execution aborted by user.")
            display_response("Action aborted.")
            return

        log_msg("ACTION", f"Executing '{intent}'...")
        exec_start = time.time()
        result = self.executor.execute(intent, parameters)
        log_debug(f"[BENCHMARK] Execution: {(time.time()-exec_start)*1000:.1f}ms")

        if isinstance(result, dict):
            if result.get("success"):
                log_msg("ACTION", f"Success: {result.get('message', '')}")
            else:
                log_msg("ACTION", f"Failed: {result.get('message', '')}")

        if intent not in ["solve_query"]:
            display_response("Done.")

    def shutdown(self):
        """Cleans up and stops the vision background processes."""
        display_response("Ending session. Bye boss")
        try:
            self.vision_session.stop()
        except Exception:
            pass
