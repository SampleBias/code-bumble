#!/bin/bash

# CodeBumble Installation Script
# Installs CodeBumble as a background service on macOS/Linux

set -e  # Exit on any error

echo "🐝 CodeBumble Installation Script"
echo "================================="

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is required but not installed."
    echo "Please install Python 3.8 or later and try again."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "✓ Python $PYTHON_VERSION detected"

# Check minimum Python version (3.8+)
if ! python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)'; then
    echo "❌ Error: Python 3.8 or later is required."
    echo "Current version: $PYTHON_VERSION"
    exit 1
fi

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"

echo "📁 Installation directory: $PROJECT_DIR"

# Create virtual environment if it doesn't exist
if [ ! -d "$PROJECT_DIR/venv" ]; then
    echo "🔧 Creating virtual environment..."
    python3 -m venv "$PROJECT_DIR/venv"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source "$PROJECT_DIR/venv/bin/activate"

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r "$PROJECT_DIR/requirements.txt"

# Install additional system dependencies based on OS
OS_TYPE=$(uname -s)
echo "🖥️  Detected OS: $OS_TYPE"

if [[ "$OS_TYPE" == "Darwin" ]]; then
    # macOS specific setup
    echo "🍎 Setting up for macOS..."
    
    # Check if Tesseract is installed (required for OCR)
    if ! command -v tesseract &> /dev/null; then
        echo "📦 Installing Tesseract OCR..."
        if command -v brew &> /dev/null; then
            brew install tesseract
        else
            echo "❌ Homebrew not found. Please install Tesseract manually:"
            echo "   brew install tesseract"
            echo "   Or download from: https://github.com/tesseract-ocr/tesseract"
        fi
    else
        echo "✓ Tesseract OCR already installed"
    fi
    
    # Check accessibility permissions
    echo "⚠️  IMPORTANT: This application requires accessibility permissions."
    echo "   Please go to System Preferences > Security & Privacy > Privacy > Accessibility"
    echo "   and add Terminal (or your terminal app) to the list of allowed apps."
    echo "   You may need to add Python as well when prompted."
    
elif [[ "$OS_TYPE" == "Linux" ]]; then
    # Linux specific setup
    echo "🐧 Setting up for Linux..."
    
    # Install system dependencies (Ubuntu/Debian)
    if command -v apt-get &> /dev/null; then
        echo "📦 Installing system dependencies..."
        sudo apt-get update
        sudo apt-get install -y tesseract-ocr tesseract-ocr-eng python3-tk scrot
    elif command -v yum &> /dev/null; then
        # Red Hat/CentOS
        echo "📦 Installing system dependencies..."
        sudo yum install -y tesseract tesseract-langpack-eng tkinter
    elif command -v pacman &> /dev/null; then
        # Arch Linux
        echo "📦 Installing system dependencies..."
        sudo pacman -S tesseract tesseract-data-eng tk
    else
        echo "⚠️  Please install tesseract-ocr manually for your distribution"
    fi
    
    # Check X11 display
    if [ -z "$DISPLAY" ]; then
        echo "⚠️  Warning: No DISPLAY variable set. Make sure you're running in a graphical environment."
    fi
fi

# Setup configuration
if [ ! -f "$PROJECT_DIR/config.py" ]; then
    echo "⚙️  Setting up configuration..."
    cp "$PROJECT_DIR/config.example.py" "$PROJECT_DIR/config.py"
    echo "📝 Configuration file created: $PROJECT_DIR/config.py"
    echo "   Please edit this file to add your Gemini API key."
else
    echo "✓ Configuration file already exists"
fi

# Make main script executable
chmod +x "$PROJECT_DIR/main.py"

# Create launch script for easy access
cat > "$PROJECT_DIR/codebumble" << EOF
#!/bin/bash
# CodeBumble launcher script

SCRIPT_DIR="\$(cd "\$(dirname "\${BASH_SOURCE[0]}")" && pwd)"
source "\$SCRIPT_DIR/venv/bin/activate"
cd "\$SCRIPT_DIR"
python3 main.py "\$@"
EOF

chmod +x "$PROJECT_DIR/codebumble"

# Create service files for different systems
if [[ "$OS_TYPE" == "Darwin" ]]; then
    # Create launchd plist for macOS
    PLIST_DIR="$HOME/Library/LaunchAgents"
    PLIST_FILE="$PLIST_DIR/com.codebumble.agent.plist"
    
    mkdir -p "$PLIST_DIR"
    
    cat > "$PLIST_FILE" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.codebumble.agent</string>
    <key>ProgramArguments</key>
    <array>
        <string>$PROJECT_DIR/codebumble</string>
        <string>start</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/codebumble.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/codebumble.error.log</string>
    <key>WorkingDirectory</key>
    <string>$PROJECT_DIR</string>
</dict>
</plist>
EOF
    
    echo "🍎 Created macOS launch agent: $PLIST_FILE"
    echo "   To start at login: launchctl load $PLIST_FILE"
    echo "   To stop: launchctl unload $PLIST_FILE"
    
elif [[ "$OS_TYPE" == "Linux" ]]; then
    # Create systemd service file for Linux
    SERVICE_FILE="$HOME/.config/systemd/user/codebumble.service"
    mkdir -p "$(dirname "$SERVICE_FILE")"
    
    cat > "$SERVICE_FILE" << EOF
[Unit]
Description=CodeBumble Background Coding Assistant
After=graphical-session.target

[Service]
Type=simple
ExecStart=$PROJECT_DIR/codebumble start
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
WorkingDirectory=$PROJECT_DIR
Environment=DISPLAY=:0

[Install]
WantedBy=default.target
EOF
    
    echo "🐧 Created systemd service: $SERVICE_FILE"
    echo "   To enable: systemctl --user enable codebumble.service"
    echo "   To start: systemctl --user start codebumble.service"
    echo "   To check status: systemctl --user status codebumble.service"
fi

# Create uninstall script
cat > "$PROJECT_DIR/uninstall.sh" << EOF
#!/bin/bash
# CodeBumble Uninstaller

echo "🗑️  Uninstalling CodeBumble..."

# Stop service if running
if [[ "\$(uname -s)" == "Darwin" ]]; then
    launchctl unload "$PLIST_FILE" 2>/dev/null || true
    rm -f "$PLIST_FILE"
elif [[ "\$(uname -s)" == "Linux" ]]; then
    systemctl --user stop codebumble.service 2>/dev/null || true
    systemctl --user disable codebumble.service 2>/dev/null || true
    rm -f "$SERVICE_FILE"
fi

# Stop daemon if running
"$PROJECT_DIR/codebumble" stop 2>/dev/null || true

# Remove virtual environment
rm -rf "$PROJECT_DIR/venv"

# Remove generated files
rm -f "$PROJECT_DIR/codebumble"
rm -f "$PROJECT_DIR/config.py"
rm -f "/tmp/codebumble.pid"
rm -f "/tmp/codebumble.log"
rm -f "/tmp/codebumble.error.log"

echo "✅ CodeBumble uninstalled successfully"
echo "   Note: The source code directory was not removed: $PROJECT_DIR"
EOF

chmod +x "$PROJECT_DIR/uninstall.sh"

echo ""
echo "🎉 Installation completed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Edit the configuration file: $PROJECT_DIR/config.py"
echo "   - Add your Gemini API key"
echo "   - Adjust settings as needed"
echo ""
echo "2. Grant accessibility permissions (required):"
if [[ "$OS_TYPE" == "Darwin" ]]; then
    echo "   - Go to System Preferences > Security & Privacy > Privacy > Accessibility"
    echo "   - Add Terminal and Python to the allowed apps list"
elif [[ "$OS_TYPE" == "Linux" ]]; then
    echo "   - Ensure you're running in a graphical environment with X11"
    echo "   - The application needs to access keyboard and screen"
fi
echo ""
echo "3. Test the installation:"
echo "   $PROJECT_DIR/codebumble foreground"
echo ""
echo "4. Run as background service:"
echo "   $PROJECT_DIR/codebumble start"
echo ""
echo "🔧 Available commands:"
echo "   $PROJECT_DIR/codebumble start     - Start background service"
echo "   $PROJECT_DIR/codebumble stop      - Stop background service"
echo "   $PROJECT_DIR/codebumble status    - Check service status"
echo "   $PROJECT_DIR/codebumble foreground - Run in foreground (for testing)"
echo ""
echo "⚠️  Remember: This tool is for educational purposes only."
echo "   Use responsibly and in accordance with platform terms of service."

# Final permission check
echo ""
echo "🔐 Checking permissions..."
if [[ "$OS_TYPE" == "Darwin" ]]; then
    echo "   Please test screenshot capability manually after granting permissions."
elif [[ "$OS_TYPE" == "Linux" ]]; then
    if command -v xdpyinfo &> /dev/null; then
        if xdpyinfo >/dev/null 2>&1; then
            echo "✓ X11 display access confirmed"
        else
            echo "❌ X11 display access failed - check DISPLAY variable"
        fi
    fi
fi

echo ""
echo "Installation log saved to: /tmp/codebumble_install.log"
EOF
