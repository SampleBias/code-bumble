"""
Transparent Testing Window
Provides a visual interface for testing CodeBumble functionality.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import time
from datetime import datetime
from typing import Dict, Any, Optional
import logging
import cv2
import numpy as np
from PIL import Image, ImageTk

class TestWindow:
    """Transparent overlay window for testing CodeBumble"""
    
    def __init__(self, core_service=None):
        self.core_service = core_service
        self.logger = logging.getLogger(__name__)
        
        # Window setup
        self.root = tk.Tk()
        self.root.title("CodeBumble Testing Interface")
        self.root.geometry("600x700+50+50")  # width x height + x_offset + y_offset (smaller with scrolling)
        
        # Make window semi-transparent and always on top
        self.root.attributes('-alpha', 0.9)  # 90% opacity
        self.root.attributes('-topmost', True)
        
        # Configure window style
        self.root.configure(bg='#2b2b2b')
        
        # Status tracking
        self.status_vars = {}
        self.log_lines = []
        self.max_log_lines = 100
        
        # Progress tracking
        self.progress_vars = {}
        self.loading_states = {}
        self.animation_states = {}
        self.progress_bars = {}
        
        # Screenshot display
        self.screenshot_label = None
        self.last_screenshot = None
        self.screenshot_scale = 0.3  # Scale factor for display
        
        # Solution preview
        self.solution_preview = None
        self.last_solution = ""
        
        self.setup_ui()
        self.start_status_updates()
    
    def setup_ui(self):
        """Setup the user interface"""
        # Create main canvas and scrollbar
        canvas = tk.Canvas(self.root, bg='#2b2b2b')
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        
        # Configure scrolling
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
        scrollbar.pack(side="right", fill="y", padx=(0, 10), pady=10)
        
        # Bind mousewheel to canvas (cross-platform)
        def _on_mousewheel(event):
            # Windows and macOS
            if event.delta:
                canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            # Linux
            elif event.num == 4:
                canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                canvas.yview_scroll(1, "units")
        
        def _bind_to_mousewheel(event):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
            # Linux
            canvas.bind_all("<Button-4>", _on_mousewheel)
            canvas.bind_all("<Button-5>", _on_mousewheel)
        
        def _unbind_from_mousewheel(event):
            canvas.unbind_all("<MouseWheel>")
            canvas.unbind_all("<Button-4>")
            canvas.unbind_all("<Button-5>")
        
        canvas.bind('<Enter>', _bind_to_mousewheel)
        canvas.bind('<Leave>', _unbind_from_mousewheel)
        
        # Add keyboard scrolling
        def _on_key_press(event):
            if event.keysym == 'Up':
                canvas.yview_scroll(-1, "units")
            elif event.keysym == 'Down':
                canvas.yview_scroll(1, "units")
            elif event.keysym == 'Prior':  # Page Up
                canvas.yview_scroll(-5, "units")
            elif event.keysym == 'Next':   # Page Down
                canvas.yview_scroll(5, "units")
            elif event.keysym == 'Home':
                canvas.yview_moveto(0)
            elif event.keysym == 'End':
                canvas.yview_moveto(1)
        
        # Make canvas focusable for keyboard events
        canvas.focus_set()
        canvas.bind('<Key>', _on_key_press)
        
        # Store canvas reference for later use
        self.canvas = canvas
        
        # Main container (now inside scrollable frame)
        main_frame = ttk.Frame(self.scrollable_frame)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Title with scroll hint
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill='x', pady=(0, 10))
        
        title_label = ttk.Label(title_frame, text="🐝 CodeBumble Test Console", 
                               font=('Arial', 14, 'bold'))
        title_label.pack(side='left')
        
        scroll_hint = ttk.Label(title_frame, text="📜 Scroll: Mouse wheel, ↑↓ keys, PgUp/PgDn", 
                               font=('Arial', 8), foreground='gray')
        scroll_hint.pack(side='right')
        
        # Status section
        self.setup_status_section(main_frame)
        
        # Progress section
        self.setup_progress_section(main_frame)
        
        # Controls section
        self.setup_controls_section(main_frame)
        
        # Screenshot section
        self.setup_screenshot_section(main_frame)
        
        # Solution preview section
        self.setup_solution_section(main_frame)
        
        # Log section
        self.setup_log_section(main_frame)
        
        # Testing section
        self.setup_testing_section(main_frame)
    
    def setup_status_section(self, parent):
        """Setup status indicators with enhanced visual feedback"""
        status_frame = ttk.LabelFrame(parent, text="📊 System Status", padding=10)
        status_frame.pack(fill='x', pady=(0, 10))
        
        # Service status
        self.status_vars['service'] = tk.StringVar(value="❌ Stopped")
        ttk.Label(status_frame, text="🔧 Service:").grid(row=0, column=0, sticky='w')
        ttk.Label(status_frame, textvariable=self.status_vars['service']).grid(row=0, column=1, sticky='w', padx=(10, 0))
        
        # AI status
        self.status_vars['ai'] = tk.StringVar(value="❓ Unknown")
        ttk.Label(status_frame, text="🤖 AI Ready:").grid(row=1, column=0, sticky='w')
        ttk.Label(status_frame, textvariable=self.status_vars['ai']).grid(row=1, column=1, sticky='w', padx=(10, 0))
        
        # Window detection
        self.status_vars['window'] = tk.StringVar(value="🔍 Scanning...")
        ttk.Label(status_frame, text="🖼️ Coding Window:").grid(row=2, column=0, sticky='w')
        ttk.Label(status_frame, textvariable=self.status_vars['window']).grid(row=2, column=1, sticky='w', padx=(10, 0))
        
        # Initialize animation states
        for key in ['service', 'ai', 'window']:
            self.animation_states[key] = {"frame": 0, "active": False}
    
    def setup_progress_section(self, parent):
        """Setup progress bars and loading indicators"""
        progress_frame = ttk.LabelFrame(parent, text="⏳ Process Progress", padding=10)
        progress_frame.pack(fill='x', pady=(0, 10))
        
        # Progress items with bars
        progress_items = [
            ("screenshot", "📸 Screenshot"),
            ("ai_processing", "🤖 AI Processing"),
            ("typing", "⌨️ Code Output"),
            ("clipboard", "📋 Clipboard")
        ]
        
        for i, (key, label) in enumerate(progress_items):
            # Label with loading indicator
            ttk.Label(progress_frame, text=label).grid(row=i, column=0, sticky='w', pady=2)
            
            self.loading_states[key] = tk.StringVar(value="⚪ Idle")
            ttk.Label(progress_frame, textvariable=self.loading_states[key]).grid(row=i, column=1, sticky='w', padx=(10, 0))
            
            # Progress bar
            self.progress_vars[key] = tk.DoubleVar(value=0)
            progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_vars[key], 
                                         maximum=100, length=120, mode='determinate')
            progress_bar.grid(row=i, column=2, sticky='ew', padx=(10, 0), pady=2)
            self.progress_bars[key] = progress_bar
            
            # Initialize animation state
            self.animation_states[key] = {"frame": 0, "active": False}
        
        # Configure grid weights
        progress_frame.grid_columnconfigure(2, weight=1)
    
    def setup_controls_section(self, parent):
        """Setup control buttons"""
        controls_frame = ttk.LabelFrame(parent, text="🎮 Controls", padding=10)
        controls_frame.pack(fill='x', pady=(0, 10))
        
        # Button frame
        button_frame = ttk.Frame(controls_frame)
        button_frame.pack(fill='x')
        
        # Test screenshot button with progress
        ttk.Button(button_frame, text="📸 Capture Screen", 
                  command=self.test_screenshot_with_progress).pack(side='left', padx=(0, 5))
        
        # Test AI button with progress
        ttk.Button(button_frame, text="🤖 Test AI", 
                  command=self.test_ai_with_progress).pack(side='left', padx=(0, 5))
        
        # Simulate tab button
        ttk.Button(button_frame, text="🔥 Simulate Tab", 
                  command=self.simulate_tab_trigger).pack(side='left')
        
        # Progress test buttons
        ttk.Label(controls_frame, text="⏳ Progress Tests:", font=('Arial', 9, 'bold')).pack(anchor='w', pady=(10, 5))
        
        progress_frame = ttk.Frame(controls_frame)
        progress_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Button(progress_frame, text="📸 Screenshot", 
                  command=self.simulate_screenshot_progress).pack(side='left', padx=(0, 3))
        ttk.Button(progress_frame, text="🤖 AI Process", 
                  command=self.simulate_ai_progress).pack(side='left', padx=(0, 3))
        ttk.Button(progress_frame, text="⌨️ Typing", 
                  command=self.simulate_typing_progress).pack(side='left', padx=(0, 3))
        ttk.Button(progress_frame, text="📋 Clipboard", 
                  command=self.simulate_clipboard_progress).pack(side='left', padx=(0, 3))
        
        # Control buttons
        button_frame2 = ttk.Frame(controls_frame)
        button_frame2.pack(fill='x')
        
        # Clear logs
        ttk.Button(button_frame2, text="🧹 Clear Logs", 
                  command=self.clear_logs).pack(side='left', padx=(0, 5))
        
        # Toggle transparency
        ttk.Button(button_frame2, text="👻 Toggle Opacity", 
                  command=self.toggle_opacity).pack(side='left', padx=(0, 5))
        
        # Close button
        ttk.Button(button_frame2, text="❌ Close", 
                  command=self.close_window).pack(side='right')
    
    def setup_screenshot_section(self, parent):
        """Setup screenshot display section"""
        screenshot_frame = ttk.LabelFrame(parent, text="📸 Live Screenshot Preview", padding=10)
        screenshot_frame.pack(fill='x', pady=(0, 10))
        
        # Info label
        info_label = ttk.Label(screenshot_frame, text="Latest captured screen (scaled 30%):")
        info_label.pack(anchor='w')
        
        # Screenshot container
        screenshot_container = ttk.Frame(screenshot_frame)
        screenshot_container.pack(fill='x', pady=(5, 0))
        
        # Screenshot label (will hold the image)
        self.screenshot_label = ttk.Label(screenshot_container, text="📷 No screenshot captured yet")
        self.screenshot_label.pack()
        
        # Screenshot info
        self.screenshot_info = ttk.Label(screenshot_container, text="Resolution: N/A | Captured: Never")
        self.screenshot_info.pack(pady=(5, 0))
    
    def setup_solution_section(self, parent):
        """Setup AI solution preview section"""
        solution_frame = ttk.LabelFrame(parent, text="🤖 AI Solution Preview", padding=10)
        solution_frame.pack(fill='x', pady=(0, 10))
        
        # Info label
        info_label = ttk.Label(solution_frame, text="Latest AI-generated solution (ready to paste):")
        info_label.pack(anchor='w')
        
        # Solution text area (read-only)
        solution_container = ttk.Frame(solution_frame)
        solution_container.pack(fill='x', pady=(5, 0))
        
        self.solution_preview = scrolledtext.ScrolledText(solution_container, height=5, font=('Consolas', 9))
        self.solution_preview.pack(fill='x')
        self.solution_preview.insert('1.0', "🤖 No solution generated yet...\nPress Tab in a coding challenge to generate a solution!")
        self.solution_preview.configure(state='disabled')  # Read-only
        
        # Solution info and actions
        solution_actions = ttk.Frame(solution_container)
        solution_actions.pack(fill='x', pady=(5, 0))
        
        # Solution info
        self.solution_info = ttk.Label(solution_actions, text="Language: N/A | Length: 0 chars | Generated: Never")
        self.solution_info.pack(side='left')
        
        # Copy button
        ttk.Button(solution_actions, text="📋 Copy Again", 
                  command=self.copy_current_solution).pack(side='right')
        
        # Clear button  
        ttk.Button(solution_actions, text="🧹 Clear", 
                  command=self.clear_solution_preview).pack(side='right', padx=(0, 5))
    
    def setup_log_section(self, parent):
        """Setup log display"""
        log_frame = ttk.LabelFrame(parent, text="📝 Live Logs", padding=10)
        log_frame.pack(fill='both', expand=True, pady=(0, 10))
        
        # Log text area (optimized for scrollable window)
        self.log_text = scrolledtext.ScrolledText(log_frame, height=5, font=('Consolas', 9))
        self.log_text.pack(fill='both', expand=True)
        
        # Configure text tags for colors
        self.log_text.tag_configure("INFO", foreground="blue")
        self.log_text.tag_configure("WARNING", foreground="orange")
        self.log_text.tag_configure("ERROR", foreground="red")
        self.log_text.tag_configure("SUCCESS", foreground="green")
    
    def setup_testing_section(self, parent):
        """Setup testing utilities"""
        test_frame = ttk.LabelFrame(parent, text="🧪 Quick Tests", padding=10)
        test_frame.pack(fill='x')
        
        # Test input field
        ttk.Label(test_frame, text="Test Code Input:").pack(anchor='w')
        self.test_input = tk.Text(test_frame, height=3, font=('Consolas', 10))
        self.test_input.pack(fill='x', pady=(5, 10))
        self.test_input.insert('1.0', 'def solution(nums):\n    # Your code here\n    return []')
        
        # Button frame for test actions
        test_button_frame = ttk.Frame(test_frame)
        test_button_frame.pack(fill='x', pady=(5, 0))
        
        # Type test code button
        ttk.Button(test_button_frame, text="⌨️ Type Code", 
                  command=self.type_test_code).pack(side='left', padx=(0, 5))
        
        # Copy to clipboard button
        ttk.Button(test_button_frame, text="📋 Copy to Clipboard", 
                  command=self.copy_test_code).pack(side='left')
    
    def start_status_updates(self):
        """Start periodic status updates"""
        self.update_status()
        self.auto_update_screenshot()
        self.check_for_new_solution()
        self._update_animations()
        self.root.after(2000, self.start_status_updates)  # Update every 2 seconds
    
    def update_status(self):
        """Update status indicators"""
        try:
            if self.core_service:
                status = self.core_service.get_status()
                
                # Service status
                if status['running']:
                    self.status_vars['service'].set("✅ Running")
                else:
                    self.status_vars['service'].set("❌ Stopped")
                
                # AI status
                if status.get('ai_response_cached'):
                    self.status_vars['ai'].set("✅ Ready")
                else:
                    self.status_vars['ai'].set("⏳ Preparing...")
                
                # Window detection
                if status.get('active_window_detected'):
                    self.status_vars['window'].set("✅ Detected")
                else:
                    self.status_vars['window'].set("🔍 Scanning...")
                
            else:
                # No core service - standalone mode
                self.status_vars['service'].set("🧪 Test Mode")
                self.status_vars['ai'].set("🧪 Simulated")
                self.status_vars['window'].set("🧪 Mock")
                
        except Exception as e:
            self.log_message(f"Status update error: {e}", "ERROR")
    
    def auto_update_screenshot(self):
        """Automatically update screenshot if service is running"""
        try:
            if self.core_service and hasattr(self.core_service, 'window_detector'):
                # Only auto-update every 4th cycle (every 8 seconds) to avoid spam
                if not hasattr(self, '_screenshot_counter'):
                    self._screenshot_counter = 0
                
                self._screenshot_counter += 1
                
                if self._screenshot_counter >= 4:
                    self._screenshot_counter = 0
                    screenshot = self.core_service.window_detector.capture_screen()
                    if screenshot is not None:
                        self.update_screenshot_display(screenshot)
                        self.last_screenshot = screenshot
                
                # Check for new AI solution
                self.check_for_new_solution()
                        
        except Exception as e:
            # Don't log auto-update errors to avoid spam
            pass
    
    def check_for_new_solution(self):
        """Check if there's a new AI solution to display"""
        try:
            if self.core_service and hasattr(self.core_service, 'cached_ai_response'):
                cached_response = self.core_service.cached_ai_response
                if cached_response and cached_response.code != self.last_solution:
                    # New solution available
                    self.update_solution_display(cached_response)
                    self.last_solution = cached_response.code
                    
        except Exception as e:
            # Don't log errors to avoid spam
            pass
    
    def update_solution_display(self, ai_response):
        """Update the solution preview with new AI response"""
        try:
            # Enable editing temporarily
            self.solution_preview.configure(state='normal')
            
            # Clear and insert new solution
            self.solution_preview.delete('1.0', tk.END)
            self.solution_preview.insert('1.0', ai_response.code)
            
            # Disable editing again
            self.solution_preview.configure(state='disabled')
            
            # Update info
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.solution_info.configure(
                text=f"Language: {ai_response.language} | Length: {len(ai_response.code)} chars | Generated: {timestamp}"
            )
            
            self.log_message(f"🤖 New solution displayed: {len(ai_response.code)} characters", "SUCCESS")
            
        except Exception as e:
            self.log_message(f"❌ Solution display error: {e}", "ERROR")
    
    def copy_current_solution(self):
        """Copy the current solution to clipboard again"""
        if self.last_solution:
            try:
                if self.core_service:
                    success = self.core_service.keyboard_sim.copy_to_clipboard(self.last_solution)
                else:
                    import pyperclip
                    pyperclip.copy(self.last_solution)
                    success = True
                
                if success:
                    self.log_message("📋 Solution copied to clipboard again", "SUCCESS")
                else:
                    self.log_message("❌ Failed to copy solution", "ERROR")
                    
            except Exception as e:
                self.log_message(f"❌ Copy error: {e}", "ERROR")
        else:
            self.log_message("❌ No solution to copy", "WARNING")
    
    def clear_solution_preview(self):
        """Clear the solution preview"""
        try:
            self.solution_preview.configure(state='normal')
            self.solution_preview.delete('1.0', tk.END)
            self.solution_preview.insert('1.0', "🤖 No solution generated yet...\nPress Tab in a coding challenge to generate a solution!")
            self.solution_preview.configure(state='disabled')
            
            self.solution_info.configure(text="Language: N/A | Length: 0 chars | Generated: Never")
            self.last_solution = ""
            
            self.log_message("🧹 Solution preview cleared", "INFO")
            
        except Exception as e:
            self.log_message(f"❌ Clear error: {e}", "ERROR")
    
    def create_mock_solution(self):
        """Create a mock solution for testing when no service is available"""
        try:
            # Create a simple mock solution
            mock_solution = '''def add_numbers(a, b):
    """
    Returns the sum of two numbers.
    
    Args:
        a (int/float): First number
        b (int/float): Second number
    
    Returns:
        int/float: Sum of a and b
    """
    return a + b

# Example usage:
# result = add_numbers(5, 3)
# print(result)  # Output: 8'''
            
            # Update solution preview
            self.solution_preview.configure(state='normal')
            self.solution_preview.delete('1.0', tk.END)
            self.solution_preview.insert('1.0', mock_solution)
            self.solution_preview.configure(state='disabled')
            
            # Update info
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.solution_info.configure(
                text=f"Language: python | Length: {len(mock_solution)} chars | Generated: {timestamp} (MOCK)"
            )
            
            self.last_solution = mock_solution
            
        except Exception as e:
            self.log_message(f"❌ Mock solution error: {e}", "ERROR")
    
    def test_screenshot(self):
        """Test screenshot functionality"""
        self.log_message("📸 Testing screenshot capture...", "INFO")
        
        try:
            if self.core_service:
                screenshot = self.core_service.window_detector.capture_screen()
                if screenshot is not None:
                    height, width = screenshot.shape[:2]
                    self.log_message(f"✅ Screenshot successful: {width}x{height}", "SUCCESS")
                    
                    # Update display
                    self.update_screenshot_display(screenshot)
                    
                    # Store for later use
                    self.last_screenshot = screenshot
                else:
                    self.log_message("❌ Screenshot failed", "ERROR")
            else:
                # Simulate for testing
                self.log_message("✅ Screenshot test (simulated): 1920x1080", "SUCCESS")
                self.create_mock_screenshot()
                
        except Exception as e:
            self.log_message(f"❌ Screenshot error: {e}", "ERROR")
    
    def update_screenshot_display(self, screenshot):
        """Update the screenshot display in the GUI"""
        try:
            # Convert from BGR to RGB (OpenCV uses BGR)
            screenshot_rgb = cv2.cvtColor(screenshot, cv2.COLOR_BGR2RGB)
            
            # Get original dimensions
            height, width = screenshot_rgb.shape[:2]
            
            # Calculate new dimensions (scaled down)
            new_width = int(width * self.screenshot_scale)
            new_height = int(height * self.screenshot_scale)
            
            # Resize for display
            screenshot_resized = cv2.resize(screenshot_rgb, (new_width, new_height))
            
            # Convert to PIL Image
            pil_image = Image.fromarray(screenshot_resized)
            
            # Convert to PhotoImage for tkinter
            photo = ImageTk.PhotoImage(pil_image)
            
            # Update the label
            self.screenshot_label.configure(image=photo, text="")
            self.screenshot_label.image = photo  # Keep a reference
            
            # Update info
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.screenshot_info.configure(
                text=f"Resolution: {width}x{height} | Displayed: {new_width}x{new_height} | Captured: {timestamp}"
            )
            
        except Exception as e:
            self.log_message(f"❌ Display update error: {e}", "ERROR")
    
    def create_mock_screenshot(self):
        """Create a mock screenshot for testing when no service is available"""
        try:
            # Create a simple mock image
            mock_image = np.zeros((400, 600, 3), dtype=np.uint8)
            
            # Add some visual elements
            cv2.rectangle(mock_image, (50, 50), (550, 150), (100, 100, 255), -1)  # Red rectangle
            cv2.rectangle(mock_image, (50, 200), (300, 350), (100, 255, 100), -1)  # Green rectangle
            cv2.rectangle(mock_image, (350, 200), (550, 350), (255, 100, 100), -1)  # Blue rectangle
            
            # Add text
            cv2.putText(mock_image, "MOCK SCREENSHOT", (150, 100), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            cv2.putText(mock_image, "Instructions", (80, 280), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
            cv2.putText(mock_image, "Code Editor", (380, 280), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
            
            # Update display
            self.update_screenshot_display(mock_image)
            
        except Exception as e:
            self.log_message(f"❌ Mock screenshot error: {e}", "ERROR")
    
    def test_ai(self):
        """Test AI connectivity"""
        self.log_message("🤖 Testing AI connection...", "INFO")
        
        try:
            if self.core_service:
                # Test with sample problem
                test_problem = "Write a function that returns the sum of two numbers."
                response = self.core_service.ai_client.generate_code_solution(test_problem)
                
                if response and response.confidence > 0.5:
                    self.log_message("✅ AI test successful", "SUCCESS")
                    self.log_message(f"Generated {len(response.code)} chars of code", "INFO")
                    
                    # Update solution preview with test result
                    self.update_solution_display(response)
                    self.last_solution = response.code
                else:
                    self.log_message("❌ AI test failed - low confidence", "ERROR")
            else:
                # Simulate for testing
                self.log_message("✅ AI test (simulated): Generated sample code", "SUCCESS")
                
                # Create mock solution for testing
                self.create_mock_solution()
                
        except Exception as e:
            self.log_message(f"❌ AI error: {e}", "ERROR")
    
    def simulate_tab_trigger(self):
        """Simulate a tab key trigger"""
        self.log_message("🔥 Simulating Tab key trigger...", "INFO")
        
        try:
            if self.core_service:
                # Simulate tab trigger
                self.core_service._on_user_input_detected("tab_triggered")
                self.status_vars['trigger'].set("🔥 Tab (simulated)")
                self.log_message("✅ Tab trigger simulated", "SUCCESS")
            else:
                # Standalone simulation
                self.status_vars['trigger'].set("🔥 Tab (test mode)")
                self.log_message("✅ Tab trigger (test mode)", "SUCCESS")
                
        except Exception as e:
            self.log_message(f"❌ Tab simulation error: {e}", "ERROR")
    
    def type_test_code(self):
        """Type the test code from input field"""
        code = self.test_input.get('1.0', 'end-1c')
        self.log_message("⌨️ Starting test typing...", "INFO")
        
        try:
            if self.core_service:
                # Use keyboard simulator
                success = self.core_service.keyboard_sim.type_text_naturally(code)
                if success:
                    self.log_message("✅ Test typing completed", "SUCCESS")
                else:
                    self.log_message("❌ Test typing failed", "ERROR")
            else:
                # Simulate typing
                self.log_message(f"✅ Would type: {len(code)} characters", "SUCCESS")
                
        except Exception as e:
            self.log_message(f"❌ Typing error: {e}", "ERROR")
    
    def copy_test_code(self):
        """Copy the test code to clipboard"""
        code = self.test_input.get('1.0', 'end-1c')
        self.log_message("📋 Copying test code to clipboard...", "INFO")
        
        try:
            if self.core_service:
                # Use keyboard simulator's clipboard function
                success = self.core_service.keyboard_sim.copy_to_clipboard(code)
                if success:
                    self.log_message("✅ Test code copied to clipboard", "SUCCESS")
                    self.log_message("🎯 Press Cmd+V (Mac) or Ctrl+V to paste", "INFO")
                else:
                    self.log_message("❌ Failed to copy test code", "ERROR")
            else:
                # Use pyperclip directly
                import pyperclip
                pyperclip.copy(code)
                self.log_message("✅ Test code copied to clipboard", "SUCCESS")
                self.log_message("🎯 Press Cmd+V (Mac) or Ctrl+V to paste", "INFO")
                
        except Exception as e:
            self.log_message(f"❌ Clipboard error: {e}", "ERROR")
    
    def clear_logs(self):
        """Clear the log display"""
        self.log_text.delete('1.0', tk.END)
        self.log_lines.clear()
        self.log_message("🧹 Logs cleared", "INFO")
    
    def toggle_opacity(self):
        """Toggle window opacity"""
        current_alpha = self.root.attributes('-alpha')
        new_alpha = 0.5 if current_alpha > 0.7 else 0.9
        self.root.attributes('-alpha', new_alpha)
        self.log_message(f"👻 Opacity: {int(new_alpha * 100)}%", "INFO")
    
    def close_window(self):
        """Close the test window"""
        self.log_message("❌ Closing test window...", "INFO")
        self.root.destroy()
    
    def log_message(self, message: str, level: str = "INFO"):
        """Add a message to the log display"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"
        
        # Add to log text
        self.log_text.insert(tk.END, formatted_message, level)
        self.log_text.see(tk.END)  # Auto-scroll to bottom
        
        # Keep log history
        self.log_lines.append(formatted_message)
        if len(self.log_lines) > self.max_log_lines:
            self.log_lines.pop(0)
            # Remove old lines from display
            self.log_text.delete('1.0', '2.0')
    
    # ===== PROGRESS AND ANIMATION METHODS =====
    
    def set_progress(self, process: str, value: int, status: str = None):
        """Update progress bar and status for a process"""
        if process in self.progress_vars:
            self.progress_vars[process].set(value)
            
        if process in self.loading_states and status:
            self.loading_states[process].set(status)
            
        # Start animation if value > 0 and < 100
        if process in self.animation_states:
            self.animation_states[process]["active"] = 0 < value < 100
    
    def start_loading(self, process: str, message: str = "🔄 Processing..."):
        """Start loading animation for a process"""
        if process in self.loading_states:
            self.loading_states[process].set(message)
            
        if process in self.animation_states:
            self.animation_states[process]["active"] = True
            
        if process in self.progress_bars:
            self.progress_bars[process].configure(mode='indeterminate')
            self.progress_bars[process].start(10)  # Fast animation
    
    def stop_loading(self, process: str, message: str = "✅ Complete", final_value: int = 100):
        """Stop loading animation for a process"""
        if process in self.loading_states:
            self.loading_states[process].set(message)
            
        if process in self.animation_states:
            self.animation_states[process]["active"] = False
            
        if process in self.progress_bars:
            self.progress_bars[process].stop()
            self.progress_bars[process].configure(mode='determinate')
            
        if process in self.progress_vars:
            self.progress_vars[process].set(final_value)
    
    def _update_animations(self):
        """Update animated loading indicators"""
        loading_frames = ["⚪", "🔵", "🟡", "🟠", "🔴", "🟣", "🟢"]
        
        for process, state in self.animation_states.items():
            if state["active"]:
                state["frame"] = (state["frame"] + 1) % len(loading_frames)
                current_frame = loading_frames[state["frame"]]
                
                if process in self.loading_states:
                    current_text = self.loading_states[process].get()
                    if "🔄" in current_text:
                        # Update just the emoji part
                        base_text = current_text.replace("🔄", "").strip()
                        self.loading_states[process].set(f"{current_frame} {base_text}")
    
    def simulate_screenshot_progress(self):
        """Simulate screenshot capture progress"""
        def progress():
            self.start_loading("screenshot", "🔄 Capturing...")
            self.set_progress("screenshot", 25, "🔄 Window Detection...")
            self.root.after(300, lambda: self.set_progress("screenshot", 50, "🔄 Image Processing..."))
            self.root.after(600, lambda: self.set_progress("screenshot", 75, "🔄 OCR Analysis..."))
            self.root.after(900, lambda: self.stop_loading("screenshot", "✅ Complete"))
        
        threading.Thread(target=progress, daemon=True).start()
    
    def simulate_ai_progress(self):
        """Simulate AI processing progress"""
        def progress():
            self.start_loading("ai_processing", "🔄 Connecting...")
            self.set_progress("ai_processing", 20, "🔄 Sending Request...")
            self.root.after(500, lambda: self.set_progress("ai_processing", 40, "🔄 AI Thinking..."))
            self.root.after(1000, lambda: self.set_progress("ai_processing", 70, "🔄 Generating Code..."))
            self.root.after(1500, lambda: self.set_progress("ai_processing", 90, "🔄 Formatting..."))
            self.root.after(2000, lambda: self.stop_loading("ai_processing", "✅ Solution Ready"))
        
        threading.Thread(target=progress, daemon=True).start()
    
    def simulate_typing_progress(self):
        """Simulate typing progress"""
        def progress():
            self.start_loading("typing", "🔄 Preparing...")
            self.set_progress("typing", 30, "🔄 Typing Code...")
            self.root.after(400, lambda: self.set_progress("typing", 60, "🔄 Adding Syntax..."))
            self.root.after(800, lambda: self.set_progress("typing", 85, "🔄 Finalizing..."))
            self.root.after(1200, lambda: self.stop_loading("typing", "✅ Code Typed"))
        
        threading.Thread(target=progress, daemon=True).start()
    
    def simulate_clipboard_progress(self):
        """Simulate clipboard operation progress"""
        def progress():
            self.start_loading("clipboard", "🔄 Accessing...")
            self.set_progress("clipboard", 50, "🔄 Copying...")
            self.root.after(200, lambda: self.stop_loading("clipboard", "✅ Copied"))
        
        threading.Thread(target=progress, daemon=True).start()
    
    def test_screenshot_with_progress(self):
        """Test screenshot with progress indicators"""
        self.log_message("📸 Testing screenshot with progress...", "INFO")
        self.simulate_screenshot_progress()
        # Also call the regular screenshot function
        threading.Timer(1.0, self.test_screenshot).start()
    
    def test_ai_with_progress(self):
        """Test AI with progress indicators"""
        self.log_message("🤖 Testing AI with progress...", "INFO")
        self.simulate_ai_progress()
        # Also call the regular AI function
        threading.Timer(2.5, self.test_ai).start()
    
    def run(self):
        """Run the test window"""
        self.log_message("🐝 CodeBumble Test Window Started", "SUCCESS")
        self.log_message("Press 🔥 Simulate Tab to test activation", "INFO")
        self.root.mainloop()

def create_test_window(core_service=None):
    """Create and return a test window instance"""
    return TestWindow(core_service)

if __name__ == "__main__":
    # Standalone testing
    window = TestWindow()
    window.run()
