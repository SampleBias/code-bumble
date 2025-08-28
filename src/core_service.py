"""
Core Service - Main coordination system for CodeBumble
Orchestrates all components and manages the background operation.
"""

import time
import threading
import logging
import signal
import sys
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import json
import os

from .window_detector import WindowDetector
from .text_extractor import TextExtractor
from .ai_client import GeminiClient
from .keyboard_simulator import KeyboardSimulator, InputMonitor

class CodeBumbleService:
    """Main service that coordinates all components"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = self._setup_logging()
        
        # Component initialization
        # Initialize components with debug mode
        debug_mode = config.get('DEBUG_MODE', True)  # Enable debug by default
        self.window_detector = WindowDetector(debug_mode=debug_mode)
        self.text_extractor = TextExtractor(debug_mode=debug_mode)
        self.ai_client = GeminiClient(config['GEMINI_API_KEY'], debug_mode=debug_mode)
        self.keyboard_sim = KeyboardSimulator(debug_mode=config.get('DEBUG_MODE', False))
        self.input_monitor = InputMonitor(self.keyboard_sim)
        
        # Service state
        self.is_running = False
        self.is_paused = False
        self.current_session = None
        
        # Current state tracking
        self.last_screenshot_time = 0
        self.last_instruction_text = ""
        self.cached_ai_response = None
        self.active_coding_window = None
        
        # Statistics and monitoring
        self.session_stats = {
            'sessions_started': 0,
            'problems_solved': 0,
            'characters_typed': 0,
            'api_calls_made': 0,
            'uptime_start': datetime.now()
        }
        
        # Safety and stealth features
        self.typing_sessions_this_hour = 0
        self.last_hour_reset = datetime.now()
        self.max_sessions_per_hour = config.get('MAX_TYPING_SESSIONS_PER_HOUR', 5)
        
        # Threading
        self.main_thread = None
        self.monitor_thread = None
        self.shutdown_event = threading.Event()
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        log_level = self.config.get('LOG_LEVEL', 'INFO')
        
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        logger = logging.getLogger('CodeBumble')
        
        # In production, might want to log to file
        if not self.config.get('DEBUG_MODE', False):
            # Minimize console output in production
            logger.setLevel(logging.WARNING)
        
        return logger
    
    def start(self):
        """Start the background service"""
        if self.is_running:
            self.logger.warning("Service is already running")
            return
        
        self.logger.info("Starting CodeBumble background service...")
        
        # Validate configuration
        if not self._validate_config():
            self.logger.error("Configuration validation failed")
            return
        
        # Test AI client
        if not self.ai_client.validate_api_key():
            self.logger.error("Invalid Gemini API key")
            return
        
        self.is_running = True
        
        # Setup input monitoring callbacks
        self.input_monitor.set_callbacks(
            on_start=self._on_typing_session_start,
            on_stop=self._on_typing_session_end
        )
        
        # Start monitoring threads
        self.main_thread = threading.Thread(target=self._main_loop, daemon=True)
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        
        self.main_thread.start()
        self.monitor_thread.start()
        
        # Start input monitoring
        self.keyboard_sim.start_monitoring(self._on_user_input_detected)
        
        self.logger.info("CodeBumble service started successfully")
        self.session_stats['uptime_start'] = datetime.now()
    
    def stop(self):
        """Stop the background service"""
        if not self.is_running:
            return
        
        self.logger.info("Stopping CodeBumble service...")
        
        self.is_running = False
        self.shutdown_event.set()
        
        # Stop input monitoring
        self.keyboard_sim.stop_monitoring()
        
        # Wait for threads to finish
        if self.main_thread and self.main_thread.is_alive():
            self.main_thread.join(timeout=5.0)
        
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5.0)
        
        self.logger.info("CodeBumble service stopped")
    
    def _main_loop(self):
        """Main service loop"""
        screenshot_interval = self.config.get('SCREENSHOT_INTERVAL', 2.0)
        
        while self.is_running and not self.shutdown_event.is_set():
            try:
                if not self.is_paused:
                    current_time = time.time()
                    
                    # Check if it's time for a new screenshot
                    if current_time - self.last_screenshot_time >= screenshot_interval:
                        self._process_screen_analysis()
                        self.last_screenshot_time = current_time
                
                # Brief sleep to prevent excessive CPU usage
                time.sleep(0.1)
                
            except Exception as e:
                self.logger.error(f"Error in main loop: {e}")
                time.sleep(1.0)  # Longer sleep on error
    
    def _monitor_loop(self):
        """Monitoring and maintenance loop"""
        while self.is_running and not self.shutdown_event.is_set():
            try:
                # Reset hourly typing session counter
                self._reset_hourly_counters()
                
                # Check for memory cleanup needs
                self._perform_maintenance()
                
                # Log statistics periodically
                self._log_statistics()
                
                # Sleep for maintenance interval
                time.sleep(60.0)  # Run maintenance every minute
                
            except Exception as e:
                self.logger.error(f"Error in monitor loop: {e}")
                time.sleep(60.0)
    
    def _process_screen_analysis(self):
        """Analyze current screen for coding interfaces"""
        # Capture screenshot
        screenshot = self.window_detector.capture_screen()
        if screenshot is None:
            self.logger.warning("Failed to capture screenshot")
            return
        
        if self.config.get('DEBUG_MODE', False):
            self.logger.debug(f"Screenshot captured: {screenshot.shape}")
        
        # Get instruction region (prefer user-selected over auto-detected)
        instruction_region = self.window_detector.get_instruction_region(screenshot)
        if not instruction_region:
            # No instruction region found
            self.active_coding_window = None
            if self.config.get('DEBUG_MODE', False):
                self.logger.debug("No instruction region found")
            return
        
        # Create a simple layout with the instruction region
        self.active_coding_window = {
            'instruction_panel': instruction_region,
            'code_editor': {
                'x': instruction_region['x'] + instruction_region['width'],
                'y': instruction_region['y'],
                'width': screenshot.shape[1] - (instruction_region['x'] + instruction_region['width']),
                'height': instruction_region['height']
            }
        }
        
        if self.config.get('DEBUG_MODE', False):
            self.logger.debug(f"Using instruction region: {instruction_region}")
        
        # Extract instruction text from the region
        if instruction_region:
            if self.config.get('DEBUG_MODE', False):
                self.logger.debug(f"Extracting from instruction region: {instruction_region}")
            
            instruction_text = self.text_extractor.extract_instruction_text(
                screenshot, instruction_region
            )
            
            if self.config.get('DEBUG_MODE', False):
                self.logger.debug(f"Extracted text length: {len(instruction_text)}")
                self.logger.debug(f"Text preview: {instruction_text[:200]}")
            
            # Check if this is a new problem
            if instruction_text != self.last_instruction_text and len(instruction_text) > 50:
                if self.text_extractor.is_valid_coding_problem(instruction_text):
                    self.logger.info(f"New coding problem detected: {len(instruction_text)} chars")
                    self._prepare_ai_response(instruction_text)
                    self.last_instruction_text = instruction_text
                else:
                    self.logger.debug("Extracted text doesn't appear to be a coding problem")
            elif len(instruction_text) <= 50:
                self.logger.debug(f"Extracted text too short: {len(instruction_text)} chars")
        else:
            self.logger.warning("No instruction panel found in layout")
    
    def _prepare_ai_response(self, instruction_text: str):
        """Prepare AI response for the detected problem"""
        try:
            self.logger.info("Preparing AI response for new coding problem")
            
            # Extract problem details
            problem_details = self.text_extractor.extract_problem_details(instruction_text)
            
            # Generate code solution
            response = self.ai_client.generate_code_solution(
                instruction_text, 
                language="python"  # Could be made configurable
            )
            
            # Add raw instruction text to response for display
            if response:
                response.raw_instruction_text = instruction_text
            
            if response and response.confidence > 0.5:
                self.cached_ai_response = response
                self.session_stats['api_calls_made'] += 1
                self.logger.debug("AI response cached and ready")
            else:
                self.logger.warning("AI response quality too low, not caching")
                
        except Exception as e:
            self.logger.error(f"Failed to prepare AI response: {e}")
    
    def _on_user_input_detected(self, input_type: str):
        """Handle user input detection"""
        if input_type in ["tab_triggered", "typing_started"] and self._can_start_typing_session():
            if input_type == "tab_triggered":
                self.logger.info("🎯 Tab trigger detected - starting AI assistance session")
            # Store trigger type for timing adjustments
            self._last_trigger_type = input_type
            self.input_monitor.start_typing_session()
    
    def _on_typing_session_start(self):
        """Handle start of typing assistance session"""
        if not self.cached_ai_response or not self.active_coding_window:
            return
        
        # Check rate limiting
        if not self._can_start_typing_session():
            self.logger.info("Rate limiting: skipping typing session")
            return
        
        self.logger.info("Starting typing assistance session")
        
        # Find code input field location
        editor_region = self.active_coding_window.get('code_editor')
        if editor_region:
            input_location = self.window_detector.find_code_input_field(
                self.window_detector.capture_screen(), editor_region
            )
            
            if input_location:
                # Start typing the AI response
                threading.Thread(
                    target=self._execute_typing_session,
                    args=(input_location,),
                    daemon=True
                ).start()
    
    def _execute_typing_session(self, input_location: tuple):
        """Execute the typing session"""
        try:
            # Small delay to ensure user has stopped typing
            # Shorter delay for tab-triggered sessions
            if hasattr(self, '_last_trigger_type') and self._last_trigger_type == "tab_triggered":
                delay = self.config.get('TAB_TRIGGER_DELAY', 1.0)
                self.logger.info(f"⚡ Tab trigger - using fast activation ({delay}s delay)")
            else:
                delay = self.config.get('IDLE_TIME_BEFORE_ACTIVATION', 3.0)
                self.logger.info(f"⏳ Standard activation delay ({delay}s)")
            
            time.sleep(delay)
            
            if self.cached_ai_response:
                # Check if clipboard mode is enabled
                if self.config.get('USE_CLIPBOARD', True):
                    # Copy to clipboard mode
                    success = self.keyboard_sim.copy_and_notify(self.cached_ai_response.code)
                    if success:
                        self.session_stats['sessions_started'] += 1
                        self.session_stats['characters_typed'] += len(self.cached_ai_response.code)
                        self.typing_sessions_this_hour += 1
                        self.logger.info("📋 Solution copied to clipboard successfully")
                    else:
                        self.logger.error("❌ Failed to copy solution to clipboard")
                        
                elif self.config.get('AUTO_TYPE', False):
                    # Auto-typing mode (original behavior)
                    success = self.keyboard_sim.type_text_naturally(
                        self.cached_ai_response.code,
                        target_x=input_location[0],
                        target_y=input_location[1]
                    )
                    
                    if success:
                        self.session_stats['sessions_started'] += 1
                        self.session_stats['characters_typed'] += len(self.cached_ai_response.code)
                        self.typing_sessions_this_hour += 1
                        self.logger.info("⌨️ Auto-typing session completed successfully")
                    else:
                        self.logger.error("❌ Auto-typing session failed")
                else:
                    # Default to clipboard if neither is explicitly enabled
                    success = self.keyboard_sim.copy_and_notify(self.cached_ai_response.code)
                    if success:
                        self.session_stats['sessions_started'] += 1
                        self.session_stats['characters_typed'] += len(self.cached_ai_response.code)
                        self.typing_sessions_this_hour += 1
                        self.logger.info("📋 Solution copied to clipboard (default mode)")
                    else:
                        self.logger.error("❌ Failed to copy solution to clipboard")
        
        except Exception as e:
            self.logger.error(f"Error during typing session: {e}")
        
        finally:
            self.input_monitor.end_typing_session()
    
    def _on_typing_session_end(self):
        """Handle end of typing assistance session"""
        self.logger.debug("Typing assistance session ended")
        # Clear cached response to prevent reuse
        self.cached_ai_response = None
    
    def _can_start_typing_session(self) -> bool:
        """Check if a new typing session can be started"""
        # Check hourly rate limit
        if self.typing_sessions_this_hour >= self.max_sessions_per_hour:
            return False
        
        # Check if currently typing
        if self.keyboard_sim.is_currently_typing():
            return False
        
        # Check if service is paused
        if self.is_paused:
            return False
        
        return True
    
    def _reset_hourly_counters(self):
        """Reset hourly counters for rate limiting"""
        current_time = datetime.now()
        if current_time - self.last_hour_reset >= timedelta(hours=1):
            self.typing_sessions_this_hour = 0
            self.last_hour_reset = current_time
    
    def _perform_maintenance(self):
        """Perform routine maintenance tasks"""
        # Clear AI client cache periodically
        if len(self.ai_client.response_cache) > 100:
            self.ai_client.clear_cache()
        
        # Memory cleanup would go here
        pass
    
    def _log_statistics(self):
        """Log service statistics"""
        if self.config.get('DEBUG_MODE', False):
            uptime = datetime.now() - self.session_stats['uptime_start']
            self.logger.debug(f"Service stats - Uptime: {uptime}, "
                            f"Sessions: {self.session_stats['sessions_started']}, "
                            f"API calls: {self.session_stats['api_calls_made']}")
    
    def _validate_config(self) -> bool:
        """Validate configuration"""
        required_keys = ['GEMINI_API_KEY']
        
        for key in required_keys:
            if key not in self.config or not self.config[key]:
                self.logger.error(f"Missing required configuration: {key}")
                return False
        
        return True
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.stop()
        sys.exit(0)
    
    def pause(self):
        """Pause the service temporarily"""
        self.is_paused = True
        self.logger.info("Service paused")
    
    def resume(self):
        """Resume the service"""
        self.is_paused = False
        self.logger.info("Service resumed")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current service status"""
        uptime = datetime.now() - self.session_stats['uptime_start']
        
        return {
            'running': self.is_running,
            'paused': self.is_paused,
            'uptime_seconds': uptime.total_seconds(),
            'active_window_detected': self.active_coding_window is not None,
            'ai_response_cached': self.cached_ai_response is not None,
            'typing_sessions_this_hour': self.typing_sessions_this_hour,
            'statistics': self.session_stats.copy()
        }
