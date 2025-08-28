"""
Keyboard Simulation and Input Monitoring
Handles keystroke simulation with human-like patterns and input monitoring.
"""

import time
import random
import pyautogui
from pynput import keyboard, mouse
from pynput.keyboard import Key, Listener as KeyboardListener
from pynput.mouse import Listener as MouseListener
import threading
import logging
from typing import Optional, Callable, List, Dict
from dataclasses import dataclass
import queue
import pyperclip

@dataclass
class TypingPattern:
    """Represents human-like typing patterns"""
    base_speed: float
    variation: float
    word_pause: float
    thinking_pause: float
    error_rate: float

class KeyboardSimulator:
    """Simulates human-like keyboard input"""
    
    def __init__(self, debug_mode: bool = False):
        self.debug_mode = debug_mode
        self.logger = logging.getLogger(__name__)
        
        # Typing patterns for different skill levels
        self.typing_patterns = {
            'beginner': TypingPattern(0.15, 0.08, 0.8, 2.0, 0.05),
            'intermediate': TypingPattern(0.08, 0.04, 0.5, 1.0, 0.02),
            'expert': TypingPattern(0.05, 0.02, 0.3, 0.5, 0.01)
        }
        
        self.current_pattern = self.typing_patterns['intermediate']
        
        # Control flags
        self.is_typing = False
        self.should_stop = False
        
        # Input monitoring
        self.input_queue = queue.Queue()
        self.is_monitoring = False
        self.typing_detection_callback = None
        
        # Key listeners
        self.keyboard_listener = None
        self.mouse_listener = None
        
        # Configure pyautogui
        pyautogui.FAILSAFE = False
        pyautogui.PAUSE = 0.01  # Minimal pause between actions
    
    def start_monitoring(self, typing_callback: Callable[[str], None]):
        """Start monitoring for user input to trigger typing"""
        self.typing_detection_callback = typing_callback
        self.is_monitoring = True
        
        # Start keyboard listener
        self.keyboard_listener = KeyboardListener(
            on_press=self._on_key_press,
            on_release=self._on_key_release
        )
        self.keyboard_listener.start()
        
        # Start mouse listener to detect click in code editor
        self.mouse_listener = MouseListener(
            on_click=self._on_mouse_click
        )
        self.mouse_listener.start()
        
        self.logger.info("Input monitoring started")
    
    def stop_monitoring(self):
        """Stop input monitoring"""
        self.is_monitoring = False
        self.should_stop = True
        
        if self.keyboard_listener:
            self.keyboard_listener.stop()
        
        if self.mouse_listener:
            self.mouse_listener.stop()
        
        self.logger.info("Input monitoring stopped")
    
    def _on_key_press(self, key):
        """Handle key press events"""
        if not self.is_monitoring or self.is_typing:
            return
        
        try:
            # Check for Tab key - this is the activation trigger
            if key == Key.tab:
                # Tab pressed - trigger AI assistance
                if self.typing_detection_callback:
                    self.typing_detection_callback("tab_triggered")
                    self.logger.info("🔥 Tab key detected - AI assistance activated!")
                    print("🎯 CodeBumble: Tab detected - AI assistance starting...")  # Visual feedback
                return
            
            # Also support typing detection as backup
            if hasattr(key, 'char') and key.char and key.char.isalnum():
                # User started typing - trigger AI assistance (secondary trigger)
                if self.typing_detection_callback:
                    self.typing_detection_callback("typing_started")
            
        except AttributeError:
            # Special keys (ctrl, alt, etc.)
            pass
    
    def _on_key_release(self, key):
        """Handle key release events"""
        pass
    
    def _on_mouse_click(self, x, y, button, pressed):
        """Handle mouse click events"""
        if pressed and self.is_monitoring:
            # Mouse click detected - potentially in code editor
            self.input_queue.put(('click', x, y))
    
    def type_text_naturally(self, text: str, target_x: Optional[int] = None, target_y: Optional[int] = None) -> bool:
        """Type text with natural human-like patterns"""
        if self.is_typing:
            self.logger.warning("Already typing, ignoring new request")
            return False
        
        self.is_typing = True
        self.should_stop = False
        
        try:
            # Click on target position if provided
            if target_x is not None and target_y is not None:
                pyautogui.click(target_x, target_y)
                time.sleep(0.1)  # Brief pause after click
            
            # Type text with natural patterns
            self._type_with_patterns(text)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to type text naturally: {e}")
            return False
        
        finally:
            self.is_typing = False
    
    def _type_with_patterns(self, text: str):
        """Type text using human-like patterns"""
        words = text.split(' ')
        
        for word_idx, word in enumerate(words):
            if self.should_stop:
                break
            
            # Type each character in the word
            for char_idx, char in enumerate(word):
                if self.should_stop:
                    break
                
                # Simulate occasional typos and corrections
                if random.random() < self.current_pattern.error_rate:
                    self._simulate_typo(char)
                
                # Type the correct character
                pyautogui.write(char)
                
                # Calculate typing delay
                delay = self._calculate_typing_delay(char, char_idx, len(word))
                time.sleep(delay)
            
            # Add space between words (except for last word)
            if word_idx < len(words) - 1:
                pyautogui.write(' ')
                
                # Pause between words
                word_pause = self.current_pattern.word_pause + random.uniform(-0.2, 0.2)
                time.sleep(max(0.1, word_pause))
            
            # Occasional thinking pauses
            if random.random() < 0.1:  # 10% chance of thinking pause
                thinking_pause = self.current_pattern.thinking_pause + random.uniform(-0.5, 1.0)
                time.sleep(max(0.5, thinking_pause))
    
    def _calculate_typing_delay(self, char: str, position: int, word_length: int) -> float:
        """Calculate realistic typing delay for a character"""
        base_delay = self.current_pattern.base_speed
        variation = self.current_pattern.variation
        
        # Add random variation
        delay = base_delay + random.uniform(-variation, variation)
        
        # Adjust for character complexity
        if char in '.,;:!?':
            delay *= 1.2  # Punctuation is slower
        elif char in '()[]{}':
            delay *= 1.3  # Brackets require more thought
        elif char.isupper():
            delay *= 1.1  # Capital letters are slightly slower
        elif char.isdigit():
            delay *= 0.9  # Numbers are often faster
        
        # Adjust for position in word
        if position == 0:
            delay *= 1.2  # First character of word is slower
        elif position == word_length - 1:
            delay *= 0.9  # Last character is faster
        
        return max(0.02, delay)  # Minimum delay to prevent too-fast typing
    
    def _simulate_typo(self, intended_char: str):
        """Simulate a typo and correction"""
        # Common typo mappings
        typo_map = {
            'a': 's', 's': 'a', 'd': 'f', 'f': 'd',
            'j': 'k', 'k': 'j', 'l': ';', ';': 'l',
            'q': 'w', 'w': 'q', 'e': 'r', 'r': 'e',
            'u': 'i', 'i': 'u', 'o': 'p', 'p': 'o'
        }
        
        typo_char = typo_map.get(intended_char.lower(), intended_char)
        
        # Type wrong character
        pyautogui.write(typo_char)
        time.sleep(0.1)
        
        # Pause (realizing mistake)
        time.sleep(random.uniform(0.2, 0.5))
        
        # Backspace to correct
        pyautogui.press('backspace')
        time.sleep(0.1)
    
    def set_typing_skill_level(self, level: str):
        """Set typing skill level (beginner, intermediate, expert)"""
        if level in self.typing_patterns:
            self.current_pattern = self.typing_patterns[level]
            self.logger.info(f"Typing skill level set to: {level}")
        else:
            self.logger.warning(f"Unknown skill level: {level}")
    
    def customize_typing_pattern(self, base_speed: float, variation: float, 
                                word_pause: float, thinking_pause: float, error_rate: float):
        """Customize typing pattern parameters"""
        self.current_pattern = TypingPattern(
            base_speed=base_speed,
            variation=variation,
            word_pause=word_pause,
            thinking_pause=thinking_pause,
            error_rate=error_rate
        )
        self.logger.info("Custom typing pattern applied")
    
    def copy_to_clipboard(self, text: str) -> bool:
        """Copy text to system clipboard"""
        try:
            pyperclip.copy(text)
            self.logger.info(f"📋 Copied {len(text)} characters to clipboard")
            return True
        except Exception as e:
            self.logger.error(f"❌ Failed to copy to clipboard: {e}")
            return False
    
    def get_clipboard_content(self) -> str:
        """Get current clipboard content"""
        try:
            content = pyperclip.paste()
            return content
        except Exception as e:
            self.logger.error(f"❌ Failed to read clipboard: {e}")
            return ""
    
    def copy_and_notify(self, text: str) -> bool:
        """Copy text to clipboard with user notification"""
        success = self.copy_to_clipboard(text)
        if success:
            self.logger.info("🎯 Solution copied! Press Cmd+V (Mac) or Ctrl+V (Windows/Linux) to paste")
            print("🎯 CodeBumble: Solution copied to clipboard! Press Cmd+V to paste.")
        return success
    
    def emergency_stop(self):
        """Emergency stop of all typing activities"""
        self.should_stop = True
        self.is_typing = False
        self.logger.info("Emergency stop activated")
    
    def is_currently_typing(self) -> bool:
        """Check if currently in typing mode"""
        return self.is_typing

class InputMonitor:
    """Monitors user input to trigger AI assistance"""
    
    def __init__(self, keyboard_sim: KeyboardSimulator):
        self.keyboard_sim = keyboard_sim
        self.logger = logging.getLogger(__name__)
        
        # State tracking
        self.user_typing_detected = False
        self.last_activity_time = time.time()
        self.typing_session_active = False
        
        # Callbacks
        self.on_typing_start = None
        self.on_typing_stop = None
    
    def set_callbacks(self, on_start: Callable, on_stop: Callable):
        """Set callbacks for typing events"""
        self.on_typing_start = on_start
        self.on_typing_stop = on_stop
    
    def detect_typing_opportunity(self) -> bool:
        """Detect when user is ready for AI assistance"""
        current_time = time.time()
        
        # Check if user has been inactive for a moment (indicating they might need help)
        time_since_activity = current_time - self.last_activity_time
        
        if time_since_activity > 3.0 and not self.typing_session_active:
            return True
        
        return False
    
    def mark_user_activity(self):
        """Mark that user activity was detected"""
        self.last_activity_time = time.time()
        self.user_typing_detected = True
    
    def start_typing_session(self):
        """Start a typing assistance session"""
        if not self.typing_session_active:
            self.typing_session_active = True
            if self.on_typing_start:
                self.on_typing_start()
    
    def end_typing_session(self):
        """End the typing assistance session"""
        if self.typing_session_active:
            self.typing_session_active = False
            if self.on_typing_stop:
                self.on_typing_stop()
