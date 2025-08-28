# CodeBumble 🐝

**Advanced Background Coding Assistant**

CodeBumble is a sophisticated background service that assists with coding challenges by analyzing instruction panels and providing intelligent code suggestions through natural keystroke simulation.

## ⚠️ Important Disclaimer

**Educational Purpose Only**: This tool is designed for educational purposes to understand AI integration, computer vision, and automation concepts. Use responsibly and in accordance with platform terms of service.

## 🚀 Features

### Core Functionality
- **Intelligent Screen Analysis**: Automatically detects coding challenge interfaces
- **Advanced OCR**: Extracts problem descriptions from instruction panels
- **AI-Powered Solutions**: Uses Google Gemini Flash 2.5 Pro for code generation
- **Human-like Typing**: Simulates natural typing patterns with realistic delays
- **Background Operation**: Runs silently without visible interface

### Stealth Features
- **Process Masking**: Disguises as system service
- **Resource Monitoring**: Limits CPU/memory usage to avoid detection
- **Pattern Randomization**: Varies behavior to appear human-like
- **Rate Limiting**: Controls activity frequency for stealth

### Advanced Capabilities
- **Multi-Language Support**: Supports Python, JavaScript, Java, C++
- **Context Awareness**: Analyzes problem constraints and examples
- **Error Simulation**: Occasionally makes and corrects typos for realism
- **Session Management**: Tracks usage patterns and statistics

## 📋 Requirements

### System Requirements
- **Operating System**: macOS 10.14+ or Linux (Ubuntu 18.04+)
- **Python**: 3.8 or later
- **Memory**: 256MB RAM minimum
- **Permissions**: Accessibility permissions for keyboard/screen access

### Dependencies
- Google Generative AI SDK
- OpenCV for computer vision
- Tesseract OCR for text extraction
- PyAutoGUI for automation
- pynput for input monitoring

## 🔧 Installation

### Quick Install
```bash
# Clone repository
git clone https://github.com/yourusername/codebumble.git
cd codebumble

# Run installation script
./install.sh
```

### Manual Installation
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy configuration
cp config.example.py config.py

# Edit configuration with your API key
nano config.py
```

### System Dependencies

**macOS:**
```bash
# Install Tesseract OCR
brew install tesseract

# Grant accessibility permissions
# System Preferences > Security & Privacy > Privacy > Accessibility
# Add Terminal and Python to allowed apps
```

**Linux:**
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr tesseract-ocr-eng python3-tk

# Ensure X11 environment
export DISPLAY=:0
```

## ⚙️ Configuration

Edit `config.py` with your settings:

```python
# Required: Google Gemini API Key
GEMINI_API_KEY = "your_api_key_here"

# Typing behavior (adjust for realism)
TYPING_SPEED_MIN = 0.05
TYPING_SPEED_MAX = 0.15
WORD_PAUSE_MIN = 0.3
WORD_PAUSE_MAX = 0.8

# Detection avoidance
MAX_TYPING_SESSIONS_PER_HOUR = 5
IDLE_TIME_BEFORE_ACTIVATION = 3.0

# Debug mode
DEBUG_MODE = False
```

## 🖥️ Usage

### Basic Commands
```bash
# Start background service
./codebumble start

# Check service status
./codebumble status

# Stop service
./codebumble stop

# Run in foreground (for testing)
./codebumble foreground
```

### Service Management

**macOS (using launchd):**
```bash
# Start at login
launchctl load ~/Library/LaunchAgents/com.codebumble.agent.plist

# Stop auto-start
launchctl unload ~/Library/LaunchAgents/com.codebumble.agent.plist
```

**Linux (using systemd):**
```bash
# Enable service
systemctl --user enable codebumble.service

# Start service
systemctl --user start codebumble.service

# Check logs
journalctl --user -u codebumble.service -f
```

## 🎯 How It Works

### 1. Window Detection
- Continuously monitors active browser windows
- Identifies coding challenge interfaces using computer vision
- Detects split-panel layouts (instructions + code editor)

### 2. Text Extraction
- Uses OCR to extract problem descriptions
- Parses requirements, examples, and constraints
- Validates extracted content as coding problems

### 3. AI Processing
- Sends problem description to Gemini Flash 2.5 Pro
- Generates optimized code solutions
- Caches responses for immediate delivery

### 4. Activation System
- **🔥 Tab Key Trigger**: Press Tab in code editor for instant activation
- **Typing Detection**: Backup activation when you start typing
- **Fast Response**: 1-second delay for Tab, 3-second for typing
- **Visual Feedback**: Shows when activation is detected

### 5. Human Simulation
- Simulates natural keystroke patterns with realistic timing
- Includes realistic pauses, errors, and corrections
- Variable typing speeds and word breaks for authenticity

### 6. Stealth Operation
- Limits resource usage to avoid detection
- Randomizes behavior patterns
- Operates within rate limits

## 🚀 Quick Usage Guide

### **Step 1: Start CodeBumble**
```bash
./codebumble start      # Background service
./codebumble foreground # Foreground for testing  
./codebumble test       # Test mode with GUI window
```

### **Step 2: Open a Coding Challenge**
- Visit LeetCode, HackerRank, CodeSignal, etc.
- Open any coding problem with a split layout
- Click in the code editor area

### **Step 3: Activate AI Assistance**
- **🔥 Press Tab key** for instant activation (recommended)
- **OR** start typing normally (backup method)
- Watch for "Tab detected" message in logs

### **Step 4: Get Your Solution**
- **📋 Default: Clipboard Mode** - Solution copied to clipboard
- **Press Cmd+V (Mac) or Ctrl+V** to paste when ready
- **⌨️ Optional: Auto-typing Mode** - Types solution automatically
- **🎯 User Control** - You decide when to paste the solution

## 🛡️ Security & Stealth

### Detection Avoidance
- **Process Hiding**: Runs with generic system service names
- **Resource Limits**: Caps CPU usage at 5% and memory at 100MB
- **Pattern Variance**: Randomizes timing and behavior
- **Rate Limiting**: Maximum 5 sessions per hour

### Privacy Protection
- **Local Processing**: OCR and vision processing done locally
- **API Encryption**: All API calls use HTTPS encryption
- **No Data Storage**: Problem text not permanently stored
- **Memory Cleanup**: Regular garbage collection and cache clearing

## 📊 Monitoring & Debugging

### **🧪 Test Mode (Recommended)**
The easiest way to test and debug CodeBumble:

```bash
./codebumble test
```

**Features:**
- **📱 Scrollable overlay window** that stays on top
- **📊 Real-time status monitoring** of all components
- **📸 Live screenshot preview** - see exactly what's being captured
- **🤖 AI solution preview** - view generated code before pasting
- **🔥 Tab trigger simulation** for testing activation
- **🤖 AI connectivity testing** to check Gemini API
- **⌨️ Code typing simulation** for testing output
- **📝 Live log display** with color-coded messages
- **👻 Adjustable transparency** (50% - 90% opacity)
- **🔄 Auto-refresh** screenshots and solutions
- **📋 Copy controls** for solution management
- **📜 Full scrolling support** (mouse wheel + keyboard)

### Status Information
```bash
# Check detailed status
./codebumble status

# Test mode with GUI
./codebumble test

# Test mode without GUI
./codebumble test --no-window

# View logs (Linux)
journalctl --user -u codebumble.service

# View logs (macOS)
tail -f /tmp/codebumble.log
```

### Debug Mode
Enable debug mode in `config.py`:
```python
DEBUG_MODE = True
SAVE_SCREENSHOTS = True  # Save screenshots for analysis
LOG_LEVEL = "DEBUG"
```

## 🚨 Troubleshooting

### Common Issues

**Permission Denied:**
- Grant accessibility permissions on macOS
- Run with appropriate privileges on Linux
- Check X11 display access

**API Errors:**
- Verify Gemini API key is valid
- Check network connectivity
- Monitor rate limits

**Detection Issues:**
- Adjust window detection thresholds
- Verify OCR text extraction quality
- Check screen resolution compatibility

**Performance Issues:**
- Lower resource limits in stealth mode
- Increase screenshot intervals
- Clear cache more frequently

### Logs and Diagnostics
```bash
# Enable verbose logging
export CODEBUMBLE_DEBUG=1

# Check system resources
./codebumble status --detailed

# Test components individually
python3 -c "from src.window_detector import WindowDetector; w=WindowDetector(True); print(w.capture_screen() is not None)"
```

## 🔧 Advanced Configuration

### Output Method Configuration
```bash
# Clipboard mode (recommended - user controls when to paste)
USE_CLIPBOARD=true
AUTO_TYPE=false

# Auto-typing mode (automatic typing simulation)
USE_CLIPBOARD=false
AUTO_TYPE=true
```

### Custom Typing Patterns
```python
# Expert-level typing (fast, minimal errors)
TYPING_SPEED_MIN = 0.03
TYPING_SPEED_MAX = 0.08
ERROR_RATE = 0.01

# Beginner-level typing (slow, more errors)
TYPING_SPEED_MIN = 0.10
TYPING_SPEED_MAX = 0.20
ERROR_RATE = 0.05
```

### Stealth Profiles
```python
# Maximum stealth (very low resource usage)
STEALTH_PROFILE = "invisible"
CPU_LIMIT = 2.0
MEMORY_LIMIT = 50
NETWORK_DELAY = (10.0, 30.0)

# Balanced stealth
STEALTH_PROFILE = "low_profile"
CPU_LIMIT = 5.0
MEMORY_LIMIT = 100
NETWORK_DELAY = (2.0, 8.0)
```

## 🔌 API Integration

### Gemini API Setup
1. Visit [Google AI Studio](https://aistudio.google.com/)
2. Create new API key
3. Add to `config.py`

### Custom AI Providers
Extend `ai_client.py` to support other providers:
```python
class CustomAIClient(AIClient):
    def generate_code_solution(self, problem_text: str) -> CodeResponse:
        # Implement custom AI integration
        pass
```

## 📁 Project Structure

```
codebumble/
├── src/                      # Core modules
│   ├── window_detector.py    # Screen analysis and window detection
│   ├── text_extractor.py     # OCR and text processing
│   ├── ai_client.py          # Gemini AI integration
│   ├── keyboard_simulator.py # Keystroke simulation
│   ├── core_service.py       # Main service coordinator
│   └── stealth.py            # Stealth and detection avoidance
├── main.py                   # Entry point and daemon management
├── config.example.py         # Configuration template
├── requirements.txt          # Python dependencies
├── install.sh               # Installation script
└── README.md               # This file
```

## 🤝 Contributing

This project is for educational purposes. Contributions should focus on:
- Improving AI integration techniques
- Enhancing computer vision accuracy
- Better human behavior simulation
- Cross-platform compatibility

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚖️ Legal & Ethical Use

- **Educational Purpose**: Use only for learning and research
- **Platform Compliance**: Respect terms of service
- **Academic Integrity**: Do not use for academic dishonesty
- **Professional Ethics**: Follow workplace policies
- **Personal Responsibility**: Users are responsible for their usage

## 🔗 Resources

- [Google Generative AI Documentation](https://ai.google.dev/)
- [OpenCV Python Tutorials](https://docs.opencv.org/4.x/d6/d00/tutorial_py_root.html)
- [Tesseract OCR Documentation](https://tesseract-ocr.github.io/)
- [PyAutoGUI Documentation](https://pyautogui.readthedocs.io/)

---

**Remember**: This tool is a demonstration of advanced automation and AI integration concepts. Always use responsibly and ethically.
