#!/usr/bin/env python3
"""
CodeBumble - Background Coding Assistant
Entry point for the daemon service.
"""

import os
import sys
import argparse
import signal
import time
import threading
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core_service import CodeBumbleService

def load_config():
    """Load configuration from config.py"""
    config_dict = {}
    
    try:
        # Try to import config.py
        import config
        
        # Extract configuration variables
        for attr in dir(config):
            if not attr.startswith('_'):
                config_dict[attr] = getattr(config, attr)
                
    except ImportError:
        print("Error: config.py not found. Please copy config.example.py to config.py and configure it.")
        sys.exit(1)
    
    # Validate required configuration
    if not config_dict.get('GEMINI_API_KEY') or config_dict.get('GEMINI_API_KEY') == 'your_gemini_api_key_here':
        print("Error: Please set a valid GEMINI_API_KEY in config.py")
        sys.exit(1)
    
    return config_dict

def create_pid_file(pid_file_path: str):
    """Create PID file for daemon management"""
    try:
        with open(pid_file_path, 'w') as f:
            f.write(str(os.getpid()))
        return True
    except Exception as e:
        print(f"Failed to create PID file: {e}")
        return False

def remove_pid_file(pid_file_path: str):
    """Remove PID file"""
    try:
        if os.path.exists(pid_file_path):
            os.remove(pid_file_path)
    except Exception:
        pass

def is_daemon_running(pid_file_path: str) -> bool:
    """Check if daemon is already running"""
    if not os.path.exists(pid_file_path):
        return False
    
    try:
        with open(pid_file_path, 'r') as f:
            pid = int(f.read().strip())
        
        # Check if process is still running
        os.kill(pid, 0)  # This will raise OSError if process doesn't exist
        return True
        
    except (OSError, ValueError, FileNotFoundError):
        # Process not running, remove stale PID file
        remove_pid_file(pid_file_path)
        return False

def daemonize():
    """Daemonize the process (Unix-style double fork)"""
    try:
        # First fork
        pid = os.fork()
        if pid > 0:
            sys.exit(0)  # Exit parent
    except OSError as e:
        print(f"Fork #1 failed: {e}")
        sys.exit(1)
    
    # Decouple from parent environment
    os.chdir('/')
    os.setsid()
    os.umask(0)
    
    try:
        # Second fork
        pid = os.fork()
        if pid > 0:
            sys.exit(0)  # Exit parent
    except OSError as e:
        print(f"Fork #2 failed: {e}")
        sys.exit(1)
    
    # Redirect standard streams
    sys.stdout.flush()
    sys.stderr.flush()
    
    # Redirect to /dev/null (or keep for debugging)
    with open('/dev/null', 'r') as dev_null_r:
        os.dup2(dev_null_r.fileno(), sys.stdin.fileno())
    
    # For debugging, you might want to redirect to log files instead
    # with open('/tmp/codebumble.log', 'a') as log_file:
    #     os.dup2(log_file.fileno(), sys.stdout.fileno())
    #     os.dup2(log_file.fileno(), sys.stderr.fileno())

def start_daemon(config: dict, daemon_mode: bool = True, pid_file_path: str = None):
    """Start the daemon service"""
    
    if pid_file_path and is_daemon_running(pid_file_path):
        print("CodeBumble daemon is already running")
        return
    
    if daemon_mode:
        print("Starting CodeBumble daemon...")
        daemonize()
    else:
        print("Starting CodeBumble in foreground mode...")
    
    # Create PID file
    if pid_file_path:
        create_pid_file(pid_file_path)
    
    # Setup signal handlers for graceful shutdown
    def cleanup_and_exit(signum, frame):
        if pid_file_path:
            remove_pid_file(pid_file_path)
        sys.exit(0)
    
    signal.signal(signal.SIGTERM, cleanup_and_exit)
    signal.signal(signal.SIGINT, cleanup_and_exit)
    
    try:
        # Create and start the service
        service = CodeBumbleService(config)
        service.start()
        
        # Keep the main thread alive
        while service.is_running:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("Received interrupt signal")
    except Exception as e:
        print(f"Service error: {e}")
    finally:
        if pid_file_path:
            remove_pid_file(pid_file_path)

def stop_daemon(pid_file_path: str):
    """Stop the daemon service"""
    if not is_daemon_running(pid_file_path):
        print("CodeBumble daemon is not running")
        return
    
    try:
        with open(pid_file_path, 'r') as f:
            pid = int(f.read().strip())
        
        print(f"Stopping CodeBumble daemon (PID: {pid})...")
        os.kill(pid, signal.SIGTERM)
        
        # Wait for process to stop
        for _ in range(10):  # Wait up to 10 seconds
            try:
                os.kill(pid, 0)
                time.sleep(1)
            except OSError:
                break
        else:
            # Force kill if still running
            print("Process didn't stop gracefully, forcing termination...")
            os.kill(pid, signal.SIGKILL)
        
        remove_pid_file(pid_file_path)
        print("CodeBumble daemon stopped")
        
    except (OSError, ValueError, FileNotFoundError) as e:
        print(f"Error stopping daemon: {e}")
        remove_pid_file(pid_file_path)

def status_daemon(pid_file_path: str):
    """Check daemon status"""
    if is_daemon_running(pid_file_path):
        with open(pid_file_path, 'r') as f:
            pid = f.read().strip()
        print(f"CodeBumble daemon is running (PID: {pid})")
    else:
        print("CodeBumble daemon is not running")

def start_test_mode(config: dict, no_window: bool = False):
    """Start test mode with optional GUI window"""
    print("🧪 Starting CodeBumble Test Mode...")
    
    try:
        # Create service instance
        service = CodeBumbleService(config)
        
        if no_window:
            # Run without GUI
            print("🔧 Running in console test mode")
            service.start()
            
            # Keep running until interrupted
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n🛑 Test mode interrupted")
                service.stop()
        else:
            # Run with GUI window
            print("🖥️  Starting with test window...")
            
            # Import test window
            from src.test_window import create_test_window
            
            # Start service in background thread
            service_thread = threading.Thread(target=service.start, daemon=True)
            service_thread.start()
            
            # Give service time to initialize
            time.sleep(2)
            
            # Create and run test window
            test_window = create_test_window(service)
            test_window.run()
            
            # Cleanup when window closes
            service.stop()
            
    except Exception as e:
        print(f"❌ Test mode error: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='CodeBumble Background Coding Assistant')
    parser.add_argument('command', choices=['start', 'stop', 'restart', 'status', 'foreground', 'test'],
                       help='Daemon command')
    parser.add_argument('--pid-file', default='/tmp/codebumble.pid',
                       help='PID file path (default: /tmp/codebumble.pid)')
    parser.add_argument('--config-file', default='config.py',
                       help='Configuration file path (default: config.py)')
    parser.add_argument('--no-window', action='store_true',
                       help='Run test mode without GUI window')
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config()
    
    pid_file_path = args.pid_file
    
    if args.command == 'start':
        start_daemon(config, daemon_mode=True, pid_file_path=pid_file_path)
    
    elif args.command == 'stop':
        stop_daemon(pid_file_path)
    
    elif args.command == 'restart':
        stop_daemon(pid_file_path)
        time.sleep(2)
        start_daemon(config, daemon_mode=True, pid_file_path=pid_file_path)
    
    elif args.command == 'status':
        status_daemon(pid_file_path)
    
    elif args.command == 'foreground':
        start_daemon(config, daemon_mode=False, pid_file_path=None)
    
    elif args.command == 'test':
        start_test_mode(config, args.no_window)

if __name__ == '__main__':
    main()
