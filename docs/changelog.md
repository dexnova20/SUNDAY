# SUNDAY Architecture Changelog

All notable changes to the SUNDAY Assistant architecture will be documented in this file.

---

## [2.0.0] - 2026-06-01
### Added
- **Modular Directory Tree**: Refactored the flat folder hierarchy into dedicated package namespaces: `config/`, `brain/`, `memory/`, `vision/`, `execution/`, and `interface/`.
- **Decoupled Tool Registry**: Extracted all 14 automation execution routines from the base executor script into standalone modules under `tools/` inheriting from the base `BaseTool` class.
- **Unified Settings Config** (`config/settings.py`): Consolidated all environment paths and Ollama model options into centralized variables, resolving absolute paths dynamically using Python path methods.
- **Dedicated Data Namespace** (`data/`): Migrated database files `memory.json` and `.sunday_session.json` (as `session.json`) into a secure `data/` folder, ensuring runtime state files do not clutter the source codebase.
- **Automated Verification Harness** (`tests/test_migration.py`): Designed and executed an integrated unit testing suite to automatically validate configurations, session serializers, and rule-based executor tool mappings.
- **Namespace Expansion Paths**: Established package initials `planner/`, `models/`, and `utils/` to provide structured paths for upcoming planning components and Heretic model implementations.

### Changed
- **Speech Subsystem Removal**: Completely purged legacy speech and transcription subsystems, including speech recognition Kaldi models, transcription inference calls, sounddevice integrations, and voice configurations.
- **Main Launcher Integration**: Updated root `main.py` to boot diagnostics and load modular front-end packages.
- **Standardized Output Display**: Ported root output helper to a clean text display function `display_response()` in `interface/console_output.py`, completely removing the `speak()` metaphor.

### Removed
- Removed 12 duplicate root-level scripts to eliminate codebase clutter.
- Removed legacy local `audio/` subfolder from the workspace.
- Completely removed `voice/` directory, offline speech models, pyttsx3, pygame, sounddevice, and pyaudio dependencies.

---

## [1.1.0] - 2026-05-20
### Added
- **Text-First Infrastructure**: Decoupled pyttsx3, sounddevice, and speech requirements from the core runtime pathway to enable lightning-fast text processing speeds.
- **Safety Barriers**: Placed protected exceptions in `audio_manager.py` to prevent silent imports from executing mic recording loops.
- **Session State Serialization**: Created persistent `.sunday_session.json` to serialize projects, active goals, rolling recent command contexts, and open task checklist boards.
- **Memory Query slash commands**: Introduced `/recall` and `/searchmemory` to query learned facts dynamically using substring match loops.
- **Active Startup Checks**: Built automatic Ollama pings and sundaybrain Modelfile builder checkers on boots.

---

## [1.0.0] - 2026-05-04
### Added
- Flat script codebase containing: `main.py`, `brain.py`, `action_executor.py`, `memory_manager.py`, and `voice_output.py`.
- Integrated offline wake-word listener and speech-to-text recording loops.
- Direct Google / YouTube automation triggers.
