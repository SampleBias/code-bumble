#!/bin/bash
# CodeBumble Uninstaller

echo "🗑️  Uninstalling CodeBumble..."

# Stop service if running
if [[ "$(uname -s)" == "Darwin" ]]; then
    launchctl unload "/Users/jamesutley/Library/LaunchAgents/com.codebumble.agent.plist" 2>/dev/null || true
    rm -f "/Users/jamesutley/Library/LaunchAgents/com.codebumble.agent.plist"
elif [[ "$(uname -s)" == "Linux" ]]; then
    systemctl --user stop codebumble.service 2>/dev/null || true
    systemctl --user disable codebumble.service 2>/dev/null || true
    rm -f ""
fi

# Stop daemon if running
"/Users/jamesutley/code-bumble/code-bumble/codebumble" stop 2>/dev/null || true

# Remove virtual environment
rm -rf "/Users/jamesutley/code-bumble/code-bumble/venv"

# Remove generated files
rm -f "/Users/jamesutley/code-bumble/code-bumble/codebumble"
rm -f "/Users/jamesutley/code-bumble/code-bumble/config.py"
rm -f "/tmp/codebumble.pid"
rm -f "/tmp/codebumble.log"
rm -f "/tmp/codebumble.error.log"

echo "✅ CodeBumble uninstalled successfully"
echo "   Note: The source code directory was not removed: /Users/jamesutley/code-bumble/code-bumble"
