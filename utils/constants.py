# c:\Users\mshas\OneDrive\Desktop\SUNDAY\utils\constants.py
"""
Central System-Wide Constants for SUNDAY.
Defines app blacklists, reserved slash command keywords, hotkeys, default search engines, and aliases.
"""

# Security & Privacy Blacklisted Desktop Applications
BLACKLISTED_APPS = {"Bitwarden", "KeePass", "Windows Security"}

# Instant-response greetings that never touch Brain/Memory/Ollama
FAST_CHAT_RESPONSES = {
    "hi": "Hey! How can I help?",
    "hello": "Hello! What can I do for you?",
    "hey": "Hey! What's up?",
    "yo": "Yo! What's on your mind?",
    "sup": "Not much! What's up with you?",
    "thanks": "You're welcome!",
    "thank you": "Happy to help!",
    "ty": "No problem!",
    "bye": "See you later!",
    "goodbye": "Goodbye! Take care.",
    "ok": "Got it.",
    "okay": "Got it.",
    "sure": "Alright!",
    "how are you": "I'm running great, fully local and ready to help!",
    "how are you doing": "All systems operational! What do you need?",
    "whats up": "Ready and waiting. What do you need?",
    "what's up": "Ready and waiting. What do you need?",
    "good morning": "Good morning! Ready when you are.",
    "good afternoon": "Good afternoon! How can I help?",
    "good evening": "Good evening! What can I do for you?",
    "good night": "Good night!",
    "nice": "Glad to hear it!",
    "cool": "Glad that works!",
    "great": "Awesome!",
    "awesome": "Let's keep going!",
    "perfect": "Great!",
    "yes": "Got it.",
    "no": "Understood.",
    "nope": "Understood.",
    "yep": "Got it.",
    "yeah": "Got it.",
}

# Prebuilt smalltalk response cache for instant pleasantry resolution (<100ms)
SMALLTALK_CACHE = {
    "how are you": "I'm running great, fully local and ready to help!",
    "who are you": "I am SUNDAY, your private offline AI assistant.",
    "what can you do": "I can help you write code, manage tasks, control your system volume or brightness, take screenshots, search the web, and inspect your active screen.",
    "thank you": "You're very welcome! Let me know if there's anything else I can do.",
    "good morning": "Good morning! Hope you have a productive day ahead.",
    "good evening": "Good evening! How's your day been?",
    "good night": "Good night! Sleep well.",
    "what is up": "Not much, just active and fully operational. What's on your mind?",
    "whats up": "Not much, just active and fully operational. What's on your mind?",
    "sup": "Not much! What's up with you?",
    "yo": "Yo! What's on your mind?",
}

# Words that indicate a simple chat query — skip memory/context pipeline
SIMPLE_CHAT_WORDS = {
    "hi", "hello", "hey", "yo", "sup", "thanks", "thank", "bye", "goodbye",
    "how", "are", "you", "ok", "okay", "sure", "good", "morning",
    "afternoon", "evening", "night", "nice", "cool", "great",
    "awesome", "perfect", "yes", "no", "nope", "yep", "yeah", "ty",
}

# Reserved Assistant Slash Commands
RESERVED_SLASH_COMMANDS = {
    "/help",
    "/project",
    "/goal",
    "/task",
    "/tasks",
    "/status",
    "/learn",
    "/remember",
    "/recall",
    "/searchmemory",
    "/vision",
    "/exit",
    "/quit"
}

# Spatial Keyboard Global Hotkey Activations
DEFAULT_HOTKEYS = ["alt+s", "ctrl+shift+space"]

# Default Search Engines & Platforms Mapping
SEARCH_ENGINES = {
    "google": "https://www.google.com/search?q=",
    "youtube": "https://www.youtube.com/results?search_query=",
    "spotify": "https://open.spotify.com/search/"
}

# Command shortcuts keywords matching
SHORTCUT_KEYWORDS = [
    "open", "run", "start", "close", "take", "search", "launch", "type", "write", "enter",
    "brightness", "volume", "mute", "unmute", "play", "pause", "next", "previous", "skip",
    "shutdown", "restart", "sleep", "screenshot", "maximize", "minimize"
]
