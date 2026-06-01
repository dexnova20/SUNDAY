# c:\Users\mshas\OneDrive\Desktop\SUNDAY\brain\query_resolver.py
"""
Query Resolver for SUNDAY.
Handles memory-based questions, explicit corrections, and forget commands
locally. Bypasses Ollama completely for sub-1ms execution.
"""
import re
from memory.profile_manager import ProfileManager
from memory.preference_manager import PreferenceManager
from memory.goal_manager import GoalManager
from memory.knowledge_store import KnowledgeStore

class QueryResolver:
    @staticmethod
    def resolve_query(text: str, session_manager=None) -> str:
        """
        Evaluates memory-related queries, feedback loops, explainability requests,
        and slash commands locally. Bypasses Ollama completely for <1ms execution.
        """
        text_clean = text.strip()
        text_lower = text_clean.lower().translate(str.maketrans('', '', '?!!.,;:'))

        # =====================================================================
        # 1. Feedback Loop Reinforcement / Negation
        # =====================================================================
        feedback_affirmations = {"correct", "yes", "yep", "yup", "that is correct", "yeth", "indeed", "correct."}
        feedback_negations = {"no", "incorrect", "wrong", "that's wrong", "nope", "not correct", "incorrect."}
        
        is_aff = text_lower in feedback_affirmations or any(text_lower.startswith(aff) for aff in ("correct", "yes", "yep", "yup", "indeed"))
        is_neg = text_lower in feedback_negations or any(text_lower.startswith(neg) for neg in ("no", "incorrect", "wrong", "nope"))

        if (is_aff or is_neg) and session_manager:
            last_mem = getattr(session_manager, "last_memory_accessed", None)
            if last_mem and isinstance(last_mem, dict):
                store = last_mem.get("store")
                field = last_mem.get("field")
                val = last_mem.get("value")
                cat = last_mem.get("category")
                
                # Calculate adjustment amount
                amount = 0.15 if is_aff else -0.25
                feedback_str = "reinforced (+0.15)" if amount > 0 else "penalized (-0.25)"
                
                if store == "profile" and field:
                    ProfileManager.adjust_confidence(field, amount)
                    session_manager.set_last_memory_accessed(None)  # Reset
                    return f"[FEEDBACK] Understood, confidence {feedback_str} for your profile field '{field}'."
                    
                elif store == "preference" and cat and val:
                    PreferenceManager.adjust_confidence(cat, val, amount)
                    session_manager.set_last_memory_accessed(None)  # Reset
                    return f"[FEEDBACK] Understood, confidence {feedback_str} for your preference '{cat}: {val}'."
                    
                elif store == "goals" and val:
                    GoalManager.adjust_confidence(val, amount)
                    session_manager.set_last_memory_accessed(None)  # Reset
                    return f"[FEEDBACK] Understood, confidence {feedback_str} for your goal '{val}'."

        # =====================================================================
        # 2. Fast-Path Learn Statements (Success Criteria Compliance)
        # =====================================================================
        
        # Match name statement
        name_match = re.match(r"^my name is\s+([a-zA-Z\s]+)$", text_clean, re.IGNORECASE)
        if name_match:
            name = name_match.group(1).strip().title()
            ProfileManager.update_profile("name", name)
            return f"Got it. I'll remember your name is {name}."

        # Match response style statement
        pref_match = re.match(r"^i prefer\s+([a-zA-Z]+)\s+(responses|answers|replies)$", text_clean, re.IGNORECASE)
        if pref_match:
            style = pref_match.group(1).strip().lower()
            PreferenceManager.add_preference("response_style", style)
            return f"Understood. I'll keep responses {style}."

        # =====================================================================
        # 3. Memory Explainability (/why <topic>)
        # =====================================================================
        why_match = re.match(r"^(?:\/why|why\s+do\s+you\s+think\s+i\s+like|why\s+do\s+you\s+think\s+my\s+name\s+is|why\s+my\s+|why\s+)\s*(.+)$", text_clean, re.IGNORECASE)
        if why_match:
            query = why_match.group(1).strip().lower().translate(str.maketrans('', '', '?!!.,;:'))
            
            # Check Profile
            profile = ProfileManager.load_profile()
            for field in ("name", "college", "branch", "occupation", "location", "age"):
                if field in query or query == field:
                    item = profile.get(field, {})
                    if item:
                        return f"Memory Source (Profile field '{field}'):\n" \
                               f"  * Current Value: {item.get('value')}\n" \
                               f"  * Confidence Score: {item.get('confidence', 0.5):.2f}\n" \
                               f"  * Last Updated: {item.get('last_updated', 'unknown')[:19]}\n" \
                               f"  * Last Accessed: {item.get('last_accessed', 'unknown')[:19]}"
            
            # Check Preferences
            prefs = PreferenceManager.load_preferences()
            for cat in prefs:
                for val_key, item in prefs[cat].items():
                    if query in val_key or query in cat:
                        return f"Memory Source (Preference '{cat}'):\n" \
                               f"  * Learned Preference: {item.get('value')}\n" \
                               f"  * Mentioned Count: {item.get('count', 1)} times\n" \
                               f"  * Confidence Score: {item.get('confidence', 0.5):.2f}\n" \
                               f"  * Created At: {item.get('created_at', 'unknown')[:19]}\n" \
                               f"  * Last Updated: {item.get('last_updated', 'unknown')[:19]}\n" \
                               f"  * Last Accessed: {item.get('last_accessed', 'unknown')[:19]}"

            # Check Goals
            goals = GoalManager.load_goals()
            for g in goals.get("active_goals", []):
                if query in g["goal"].lower():
                    return f"Memory Source (Active Goal):\n" \
                           f"  * Goal Description: {g['goal']}\n" \
                           f"  * Confidence Score: {g.get('confidence', 0.8):.2f}\n" \
                           f"  * Created At: {g.get('created_at', 'unknown')[:19]}\n" \
                           f"  * Last Updated: {g.get('last_updated', 'unknown')[:19]}\n" \
                           f"  * Last Accessed: {g.get('last_accessed', 'unknown')[:19]}"

            # Check Knowledge Store
            knowledge = KnowledgeStore.load_knowledge()
            for entry in knowledge:
                if query in entry.get("topic", "").lower():
                    return f"Memory Source (Stored Knowledge):\n" \
                           f"  * Topic: {entry.get('topic')}\n" \
                           f"  * Content: {entry.get('content')}\n" \
                           f"  * Confidence Score: {entry.get('confidence', 0.95):.2f}\n" \
                           f"  * Created At: {entry.get('created_at', 'unknown')[:19]}\n" \
                           f"  * Last Accessed: {entry.get('last_accessed', 'unknown')[:19]}"

            return f"I couldn't find any active memory corresponding to '{query}'."

        # =====================================================================
        # 4. Identity Summary Layer (/whoami)
        # =====================================================================
        if text_lower in ("/whoami", "who am i", "whoami", "who am i?"):
            profile = ProfileManager.get_profile()
            goals = GoalManager.get_active_goals()
            response_style = PreferenceManager.get_active_preference("response_style")
            interests = PreferenceManager.get_active_preference("interests")
            
            lines = [
                "=========================================",
                "         SUNDAY USER IDENTITY VIEW       ",
                "========================================="
            ]
            lines.append(f"Name         : {profile.get('name', 'Not set')}")
            lines.append(f"College      : {profile.get('college', 'Not set')}")
            lines.append(f"Branch       : {profile.get('branch', 'Not set')}")
            lines.append(f"Occupation   : {profile.get('occupation', 'Not set')}")
            lines.append(f"Location     : {profile.get('location', 'Not set')}")
            lines.append(f"Age          : {profile.get('age', 'Not set')}")
            lines.append("-----------------------------------------")
            
            if goals:
                lines.append("Current Goals:")
                for g in goals:
                    lines.append(f"  * {g}")
            else:
                lines.append("Current Goals: None active")
                
            if interests:
                lines.append(f"Interests    : {', '.join(interests)}")
            else:
                lines.append("Interests    : None learned yet")
                
            if response_style:
                lines.append(f"Preferences  : Response style - {response_style[0]}")
            else:
                lines.append("Preferences  : None learned yet")
            lines.append("=========================================")
            return "\n".join(lines)

        # =====================================================================
        # 5. Forget & Correct Commands
        # =====================================================================
        correct_match = re.match(r"^(?:correct|change)\s+(?:my\s+)?(name|college|branch|occupation|location|age)\s+(?:to\s+)?(.+)$", text_clean, re.IGNORECASE)
        if correct_match:
            field = correct_match.group(1).strip().lower()
            val = correct_match.group(2).strip().rstrip(".!?,")
            if field == "name":
                val = val.title()
            ProfileManager.update_profile(field, val)
            return f"Understood. I've corrected your {field} to '{val}'."

        if text_lower.startswith("forget "):
            query = text_clean[7:].strip().rstrip(".!?,")
            query_lower = query.lower()
            
            profile = ProfileManager.load_profile()
            field_found = None
            for f in ("name", "college", "branch", "occupation", "location", "age"):
                if f in query_lower or query_lower == f:
                    field_found = f
                    break
                    
            if field_found and field_found in profile:
                del profile[field_found]
                ProfileManager.save_profile(profile)
                return f"I've forgotten your {field_found}."

            prefs = PreferenceManager.load_preferences()
            pref_deleted = False
            for cat in list(prefs.keys()):
                for val_key in list(prefs[cat].keys()):
                    if query_lower in val_key or query_lower in prefs[cat][val_key]["value"].lower():
                        del prefs[cat][val_key]
                        pref_deleted = True
                if pref_deleted:
                    PreferenceManager.save_preferences(prefs)
                    return f"I've forgotten that preference regarding '{query}'."

            knowledge = KnowledgeStore.load_knowledge()
            k_matches = [k for k in knowledge if query_lower in k.get("topic", "").lower()]
            if k_matches:
                remaining = [k for k in knowledge if k not in k_matches]
                KnowledgeStore.save_knowledge(remaining)
                topics = ", ".join(f"'{k['topic']}'" for k in k_matches)
                return f"I've forgotten knowledge about {topics}."

            return f"I couldn't find any memory matching '{query}' to forget."

        # =====================================================================
        # 6. Future-Ready Traversal Queries (Knowledge Graph preparation)
        # =====================================================================
        if text_lower in ("what projects am i working on", "what are my projects", "my projects"):
            from memory.relationship_manager import RelationshipManager
            relations = RelationshipManager.traverse_path("User", ["works_on"])
            if relations:
                return "Based on your relationships graph, you are working on:\n" + \
                       "\n".join(f"- {r}" for r in relations)
            # Fall back to active goals
            goals = GoalManager.get_active_goals()
            if goals:
                return "Here are the active goals you are working on:\n" + "\n".join(f"- {g}" for g in goals)
            return "No active projects or goals found in your relationships graph."

        if "technologies" in text_lower and any(kw in text_lower for kw in ("interested", "like", "use", "prefer")):
            from memory.relationship_manager import RelationshipManager
            tools = RelationshipManager.traverse_path("User", ["uses_tool"])
            if tools:
                return "According to your relationship graph, you use/prefer these technologies:\n" + \
                       "\n".join(f"- {t}" for t in tools)
            return "No technology relationships are mapped in your graph yet."

        # =====================================================================
        # 7. Memory Questions (setting last_memory_accessed for feedback loops)
        # =====================================================================
        if text_lower in ("what is my name", "who am i", "my name", "what's my name", "do you know my name"):
            profile = ProfileManager.get_profile()
            name = profile.get("name")
            if name:
                if session_manager:
                    session_manager.set_last_memory_accessed({"store": "profile", "field": "name", "value": name})
                return f"Your name is {name}."
            return "I don't know your name yet. You can tell me by saying 'My name is Shashwat'."

        if text_lower in ("what is my college", "where do i study", "my college", "what's my college", "which college do i study in"):
            profile = ProfileManager.get_profile()
            college = profile.get("college")
            if college:
                if session_manager:
                    session_manager.set_last_memory_accessed({"store": "profile", "field": "college", "value": college})
                return f"You study at {college}."
            return "I don't have college information in your profile yet."

        if text_lower in ("what is my branch", "my branch", "what branch am i in", "what is my stream"):
            profile = ProfileManager.get_profile()
            branch = profile.get("branch")
            if branch:
                if session_manager:
                    session_manager.set_last_memory_accessed({"store": "profile", "field": "branch", "value": branch})
                return f"Your branch is {branch}."
            return "I don't have branch information in your profile yet."

        if text_lower in ("what is my occupation", "what is my job", "what do i do for work", "what do i do", "my occupation", "my job"):
            profile = ProfileManager.get_profile()
            occ = profile.get("occupation")
            if occ:
                if session_manager:
                    session_manager.set_last_memory_accessed({"store": "profile", "field": "occupation", "value": occ})
                return f"Your occupation is {occ}."
            return "I don't have occupation information in your profile yet."

        if text_lower in ("where do i live", "what is my location", "my location", "where am i located"):
            profile = ProfileManager.get_profile()
            loc = profile.get("location")
            if loc:
                if session_manager:
                    session_manager.set_last_memory_accessed({"store": "profile", "field": "location", "value": loc})
                return f"You live in {loc}."
            return "I don't have location information in your profile yet."

        if text_lower in ("how old am i", "what is my age", "my age"):
            profile = ProfileManager.get_profile()
            age = profile.get("age")
            if age:
                if session_manager:
                    session_manager.set_last_memory_accessed({"store": "profile", "field": "age", "value": age})
                return f"You are {age} years old."
            return "I don't have age information in your profile yet."

        if text_lower in ("what are my goals", "my goals", "what am i trying to achieve", "what are my active goals"):
            goals = GoalManager.get_active_goals()
            if goals:
                if session_manager:
                    session_manager.set_last_memory_accessed({"store": "goals", "value": goals[0]})
                goals_list = "\n".join(f"- {g}" for g in goals)
                return f"Here are your active goals:\n{goals_list}"
            return "You don't have any active goals tracked right now."

        if text_lower in ("what project am i working on", "current project", "my active project", "what is my project"):
            proj = getattr(session_manager, "current_project", None) if session_manager else None
            if proj:
                return f"You are currently working on the project: {proj}."
            return "No active project is currently set. You can set one using '/project <name>'."

        if text_lower in ("what do i like", "my preferences", "what are my preferences", "my interests", "what is my preference"):
            response_style = PreferenceManager.get_active_preference("response_style")
            interests = PreferenceManager.get_active_preference("interests")
            tools = PreferenceManager.get_active_preference("preferred_tools")
            
            lines = []
            if response_style:
                lines.append(f"- Preferred response style: {response_style[0]}")
                if session_manager:
                    session_manager.set_last_memory_accessed({"store": "preference", "category": "response_style", "value": response_style[0]})
            if interests:
                lines.append(f"- Interests: {', '.join(interests)}")
                if session_manager and not response_style:
                    session_manager.set_last_memory_accessed({"store": "preference", "category": "interests", "value": interests[0]})
            if tools:
                lines.append(f"- Preferred tools: {', '.join(tools)}")
                
            if lines:
                return "Here are your learned preferences:\n" + "\n".join(lines)
            return "I haven't learned your preferences yet."

        if text_lower in ("what do you know about me", "tell me about myself", "who am i to you", "what is my profile"):
            profile = ProfileManager.get_profile()
            goals = GoalManager.get_active_goals()
            response_style = PreferenceManager.get_active_preference("response_style")
            interests = PreferenceManager.get_active_preference("interests")
            
            lines = ["Here is what I know about you:"]
            
            prof_fields = []
            for field in ("name", "occupation", "college", "branch", "location", "age"):
                val = profile.get(field)
                if val:
                    prof_fields.append(f"  * {field.capitalize()}: {val}")
            if prof_fields:
                lines.append("Profile:")
                lines.extend(prof_fields)
            else:
                lines.append("Profile: No details saved yet.")
                
            if goals:
                lines.append("Active Goals:")
                lines.extend(f"  * {g}" for g in goals)
            else:
                lines.append("Goals: No active goals tracked.")
                
            pref_fields = []
            if response_style:
                pref_fields.append(f"  * Response style: {response_style[0]}")
            if interests:
                pref_fields.append(f"  * Interests: {', '.join(interests)}")
            if pref_fields:
                lines.append("Preferences:")
                lines.extend(pref_fields)
                
            return "\n".join(lines)

        return None
