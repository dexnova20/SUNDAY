# 🎙️ SUNDAY: The Intelligent Offline Desktop Assistant

SUNDAY is a premium, privacy-first AI assistant designed for Windows. Unlike generic assistants, SUNDAY runs **100% locally**, ensuring your voice, screen data, and personal files never leave your machine.

---

## ✨ Key Features

### 🧠 Dual-Mode Intelligence
SUNDAY intelligently toggles between a high-speed **Shortcut Engine** for instant system tasks and a deep-thinking **LLM Brain** for complex reasoning.

### 👁️ Contextual Screen Awareness
Ask SUNDAY about anything you're looking at. He can "read" your active window (emails, code, documents) to provide instant explanations or summaries without you needing to copy-paste.

### 🛠️ Universal Task Execution
- **System Control**: Adjust volume, brightness, and power states (Shutdown/Restart/Sleep) with voice confirmation.
- **App Management**: Launch your favorite tools like Chrome, VS Code, or Spotify via natural language.
- **Web Navigation**: Instant web searches and URL routing.
- **Safe Operations**: A built-in Permission Manager ensures no sensitive files are read or modified without your explicit "Yes".

### 💾 Persistent Memory
SUNDAY can store knowledge from your conversations into a local long-term memory, allowing him to remember context across sessions.

---

## 🚀 Technology Stack

| Component | Technology | Role |
| :--- | :--- | :--- |
| **Wake Word** | Vosk (Offline Kaldi) | High-efficiency "Sunday" detection |
| **STT** | OpenAI Whisper (Local) | High-accuracy command transcription |
| **LLM** | Ollama (Llama 3.2 1B/3B) | Natural language intent parsing |
| **TTS** | gTTS / pyttsx3 | Natural-sounding neural voice feedback |
| **Automation** | PyAutoGUI | System-level desktop interaction |

---

## 🛠️ Installation & Setup

### 1. Prerequisites
- **Python 3.10+**
- **Ollama**: [Download here](https://ollama.com/) and pull the model:
  ```bash
  ollama pull llama3.2:1b
  ```

### 2. Setup
Clone the repository and install dependencies:
```bash
pip install -r requirements.txt
```

### 3. Usage
- **Run Manually**: `python main.py`
- **Boot Mode**: `python main.py --boot` (Recommended for startup)
- **Auto-Start**: To have SUNDAY launch automatically with Windows:
  ```bash
  python setup_autostart.py
  ```

---

## 🛡️ Privacy & Security
SUNDAY is built on the principle of **Zero-Data Exfiltration**. 
- No voice data is sent to the cloud.
- No screen content is transmitted to servers.
- All intelligence is local.

---

## ⌨️ Developer Commands
- `python setup_autostart.py --remove`: Removes SUNDAY from Windows startup.
- `python main.py --boot`: Adds a 30s delay to allow audio drivers to stabilize on system boot.

---

> *"SUNDAY isn't just an assistant; he's your local co-pilot."*
