import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Required: Google Gemini API Key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "your_gemini_api_key_here")

# Typing simulation settings
TYPING_SPEED_MIN = float(os.getenv("TYPING_SPEED_MIN", "0.05"))
TYPING_SPEED_MAX = float(os.getenv("TYPING_SPEED_MAX", "0.15"))
WORD_PAUSE_MIN = float(os.getenv("WORD_PAUSE_MIN", "0.3"))
WORD_PAUSE_MAX = float(os.getenv("WORD_PAUSE_MAX", "0.8"))

# Screenshot and monitoring settings
SCREENSHOT_INTERVAL = float(os.getenv("SCREENSHOT_INTERVAL", "2.0"))
WINDOW_DETECTION_THRESHOLD = float(os.getenv("WINDOW_DETECTION_THRESHOLD", "0.8"))

# Stealth settings
MAX_TYPING_SESSIONS_PER_HOUR = int(os.getenv("MAX_TYPING_SESSIONS_PER_HOUR", "5"))
IDLE_TIME_BEFORE_ACTIVATION = float(os.getenv("IDLE_TIME_BEFORE_ACTIVATION", "3.0"))
TAB_TRIGGER_DELAY = float(os.getenv("TAB_TRIGGER_DELAY", "1.0"))

# Output method settings
USE_CLIPBOARD = os.getenv("USE_CLIPBOARD", "true").lower() == "true"
AUTO_TYPE = os.getenv("AUTO_TYPE", "false").lower() == "true"

# Debug settings
DEBUG_MODE = os.getenv("DEBUG_MODE", "true").lower() == "true"  # Enable debug by default
SAVE_SCREENSHOTS = os.getenv("SAVE_SCREENSHOTS", "true").lower() == "true"  # Save screenshots by default
LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG").upper()  # Debug logging by default

# Optional paths
TESSERACT_PATH = os.getenv("TESSERACT_PATH", "")
SCREENSHOT_SAVE_DIR = os.getenv("SCREENSHOT_SAVE_DIR", "/tmp/codebumble_screenshots")
