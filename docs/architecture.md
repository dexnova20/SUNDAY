# SUNDAY System Architecture Documentation

This document provides a detailed overview of the modular system architecture of SUNDAY. By decoupling cognitive routing, persistent storage, visual automation, execution registries, and front-end displays, we establish a robust, maintainable, and highly extensible framework.

---

## 1. System Modular Tree & Dependencies

The system structure maps clear vertical responsibility tiers:

```mermaid
graph TD
    Launcher[main.py] --> Interface[interface/chat_interface.py]
    Interface --> Output[interface/console_output.py]
    Interface --> Settings[config/settings.py]
    Interface --> Brain[brain/brain.py]
    Interface --> Memory[memory/memory_manager.py]
    Interface --> Session[memory/session_manager.py]
    Interface --> Vision[vision/vision_engine.py]
    Interface --> Executor[execution/action_executor.py]
    Interface --> Permissions[execution/permission_manager.py]
    
    Executor --> Tools[tools/ base_tool + concrete tools]
    Tools --> Settings
    Tools --> Output
    
    Vision --> UIContext[vision/ui_context.py]
    Vision --> Context[vision/context_manager.py]
    Vision --> Hotkeys[vision/hotkey_manager.py]
```

---

## 2. Startup Operational Flow

Upon invoking `python main.py`, SUNDAY executes the following sequential verification sequence:

```mermaid
sequenceDiagram
    participant OS as OS Console
    participant Launcher as main.py (Startup)
    participant Ollama as Ollama API
    participant UI as interface/chat_interface.py
    
    OS->>Launcher: Invoke python main.py
    Launcher->>Ollama: Ping http://localhost:11434 (Check Status)
    alt Ollama not running
        Launcher->>OS: Spawn subprocess "ollama serve"
    end
    Launcher->>Ollama: GET /api/tags (List Available Models)
    alt sundaybrain missing but GGUF/Modelfile present
        Launcher->>OS: Start background create "sundaybrain"
    end
    Launcher->>UI: Instantiate ChatInterface
    UI-->>Launcher: Complete component loading
    Launcher->>UI: Trigger app.run() loop
```

---

## 3. Cognitive Routing & Execution Flow

When a user submits text inputs in the CLI loop, it routes dynamically through the LLM Brain classifier and the centralized Tool Registry:

```mermaid
graph TD
    UserInput[User Input] --> SlashCheck{Is Command a Slash command /?}
    
    %% Slash Commands branch
    SlashCheck -- Yes --> SlashExec[Execute Slash command: /tasks, /recall, /status, etc.]
    
    %% Standard Query branch
    SlashCheck -- No --> MatchShortcut{Shortcut Matches Regex?}
    MatchShortcut -- Yes --> RuleIntent[Extract rule intent + bypass LLM]
    MatchShortcut -- No --> BrainClassify[Brain Classify: ACTION vs CHAT]
    
    BrainClassify --> ModeCheck{Classified Mode}
    ModeCheck -- CHAT --> Converse[Process LLM response directly]
    ModeCheck -- ACTION --> ExtractJSON[Generate structured Intent JSON]
    
    RuleIntent --> MergeIntents[Resolve intent + parameters]
    ExtractJSON --> MergeIntents
    
    MergeIntents --> CheckSens{Sensitivity Level 1 or 2?}
    CheckSens -- Level 0 / Safe --> RunTool[Central Tool Registry execute]
    CheckSens -- Sensitive --> PromptUser{CLI YES/NO Prompt}
    
    PromptUser -- YES --> RunTool
    PromptUser -- NO --> Abort[Display: Action Aborted]
    
    RunTool --> PrintDone[Display: Done / print success status]
```

---

## 4. Session State & Memory Manager Relationships

The persistent operational memory layers maintain distinct roles:

1. ** Factual Knowledge (`MemoryManager` -> `data/memory.json`)**:
   - Saves factual lessons on-demand via the `/learn` or `/remember` command.
   - Leverages Ollama in a background utility method to dynamically classify the topic headline.
   - Evaluates keyword matching and semantic queries via `/recall` and `/searchmemory`.

2. ** Active Session Tracking (`SessionManager` -> `data/session.json`)**:
   - Persists state dynamically (current working project, active goal description, open tasks lists, and rolling recent commands context history).
   - Generates condensed context header strings on every command turn:
     `[PROJECT: name] [GOAL: desc] [ACTIVE TASKS: task1, task2] [RECENT HISTORY: cmd1 -> cmd2]`
   - Injects this rolling context header directly into the LLM Brain system prompt to provide immediate context awareness.
