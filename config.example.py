# Copy this file to config.py and add your API keys
GEMINI_API_KEY = "your_gemini_api_key_here"

# Typing simulation settings
TYPING_SPEED_MIN = 0.05  # Minimum delay between keystrokes (seconds)
TYPING_SPEED_MAX = 0.15  # Maximum delay between keystrokes (seconds)
WORD_PAUSE_MIN = 0.3     # Minimum pause between words
WORD_PAUSE_MAX = 0.8     # Maximum pause between words

# Screenshot and monitoring settings
SCREENSHOT_INTERVAL = 2.0  # How often to check for coding interfaces (seconds)
WINDOW_DETECTION_THRESHOLD = 0.8  # Confidence threshold for window detection

# Stealth settings
MAX_TYPING_SESSIONS_PER_HOUR = 5  # Limit to avoid detection
IDLE_TIME_BEFORE_ACTIVATION = 3.0  # Wait time before starting to type

# Debug settings
DEBUG_MODE = False
SAVE_SCREENSHOTS = False  # Save screenshots for debugging
LOG_LEVEL = "INFO"
