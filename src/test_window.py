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
        
        # Title
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill='x', pady=(0, 10))
        
        title_label = ttk.Label(title_frame, text="CodeBumble Test Console", 
                               font=('Arial', 14, 'bold'))
        title_label.pack(side='left')
        
        scroll_hint = ttk.Label(title_frame, text="Scroll: Mouse wheel, ↑↓ keys, PgUp/PgDn", 
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
        
        # AI Reasoning section
        self.setup_ai_reasoning_section(main_frame)
        
        # Solution preview section
        self.setup_solution_section(main_frame)
        
        # Log section
        self.setup_log_section(main_frame)
        
        # Extracted Text Display section (lower area)
        self.setup_extracted_text_section(main_frame)
        
        # Testing section
        self.setup_testing_section(main_frame)
    
    def setup_status_section(self, parent):
        """Setup status indicators"""
        status_frame = ttk.LabelFrame(parent, text="System Status", padding=10)
        status_frame.pack(fill='x', pady=(0, 10))
        
        # Service status
        self.status_vars['service'] = tk.StringVar(value="Stopped")
        ttk.Label(status_frame, text="Service:").grid(row=0, column=0, sticky='w')
        ttk.Label(status_frame, textvariable=self.status_vars['service']).grid(row=0, column=1, sticky='w', padx=(10, 0))
        
        # AI status
        self.status_vars['ai'] = tk.StringVar(value="Unknown")
        ttk.Label(status_frame, text="AI Ready:").grid(row=1, column=0, sticky='w')
        ttk.Label(status_frame, textvariable=self.status_vars['ai']).grid(row=1, column=1, sticky='w', padx=(10, 0))
        
        # Window detection
        self.status_vars['window'] = tk.StringVar(value="Scanning...")
        ttk.Label(status_frame, text="Coding Window:").grid(row=2, column=0, sticky='w')
        ttk.Label(status_frame, textvariable=self.status_vars['window']).grid(row=2, column=1, sticky='w', padx=(10, 0))
        
        # Initialize animation states
        for key in ['service', 'ai', 'window']:
            self.animation_states[key] = {"frame": 0, "active": False}
    
    def setup_progress_section(self, parent):
        """Setup progress bars and loading indicators"""
        progress_frame = ttk.LabelFrame(parent, text="Process Progress", padding=10)
        progress_frame.pack(fill='x', pady=(0, 10))
        
        # Progress items with bars
        progress_items = [
            ("screenshot", "Screenshot"),
            ("ai_processing", "AI Processing"),
            ("typing", "Code Output"),
            ("clipboard", "Clipboard")
        ]
        
        for i, (key, label) in enumerate(progress_items):
            # Label with loading indicator
            ttk.Label(progress_frame, text=label).grid(row=i, column=0, sticky='w', pady=2)
            
            self.loading_states[key] = tk.StringVar(value="Idle")
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
        controls_frame = ttk.LabelFrame(parent, text="Controls", padding=10)
        controls_frame.pack(fill='x', pady=(0, 10))
        
        # Button frame
        button_frame = ttk.Frame(controls_frame)
        button_frame.pack(fill='x')
        
        # Test screenshot button with progress
        ttk.Button(button_frame, text="Capture Screen", 
                  command=self.test_screenshot_with_progress).pack(side='left', padx=(0, 5))
        
        # Test AI button with progress
        ttk.Button(button_frame, text="Test AI", 
                  command=self.test_ai_with_progress).pack(side='left', padx=(0, 5))
        
        # Simulate tab button
        ttk.Button(button_frame, text="Simulate Tab", 
                  command=self.simulate_tab_trigger).pack(side='left')
        
        # Progress test buttons
        ttk.Label(controls_frame, text="Progress Tests:", font=('Arial', 9, 'bold')).pack(anchor='w', pady=(10, 5))
        
        progress_frame = ttk.Frame(controls_frame)
        progress_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Button(progress_frame, text="Screenshot", 
                  command=self.simulate_screenshot_progress).pack(side='left', padx=(0, 3))
        ttk.Button(progress_frame, text="AI Process", 
                  command=self.simulate_ai_progress).pack(side='left', padx=(0, 3))
        ttk.Button(progress_frame, text="Typing", 
                  command=self.simulate_typing_progress).pack(side='left', padx=(0, 3))
        ttk.Button(progress_frame, text="Clipboard", 
                  command=self.simulate_clipboard_progress).pack(side='left', padx=(0, 3))
        
        # Control buttons
        button_frame2 = ttk.Frame(controls_frame)
        button_frame2.pack(fill='x')
        
        # Region selector button
        ttk.Button(button_frame2, text="Select Region", 
                  command=self.launch_region_selector).pack(side='left', padx=(0, 5))
        
        # Test screenshot button
        ttk.Button(button_frame2, text="Test Screenshot", 
                  command=self.test_screenshot).pack(side='left', padx=(0, 5))
        
        # Clear logs
        ttk.Button(button_frame2, text="Clear Logs", 
                  command=self.clear_logs).pack(side='left', padx=(0, 5))
        
        # Toggle transparency
        ttk.Button(button_frame2, text="Toggle Opacity", 
                  command=self.toggle_opacity).pack(side='left', padx=(0, 5))
        
        # Close button
        ttk.Button(button_frame2, text="Close", 
                  command=self.close_window).pack(side='right')
    
    def setup_screenshot_section(self, parent):
        """Setup screenshot display section"""
        screenshot_frame = ttk.LabelFrame(parent, text="Live Screenshot Preview", padding=10)
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
        solution_frame = ttk.LabelFrame(parent, text="AI Solution Preview", padding=10)
        solution_frame.pack(fill='x', pady=(0, 10))
        
        # Info label
        info_label = ttk.Label(solution_frame, text="Latest AI-generated solution (ready to paste):")
        info_label.pack(anchor='w')
        
        # Solution text area (read-only)
        solution_container = ttk.Frame(solution_frame)
        solution_container.pack(fill='x', pady=(5, 0))
        
        self.solution_preview = scrolledtext.ScrolledText(solution_container, height=5, font=('Consolas', 9))
        self.solution_preview.pack(fill='x')
        self.solution_preview.insert('1.0', "No solution generated yet...\nPress Tab in a coding challenge to generate a solution!")
        self.solution_preview.configure(state='disabled')  # Read-only
        
        # Solution info and actions
        solution_actions = ttk.Frame(solution_container)
        solution_actions.pack(fill='x', pady=(5, 0))
        
        # Solution info
        self.solution_info = ttk.Label(solution_actions, text="Language: N/A | Length: 0 chars | Generated: Never")
        self.solution_info.pack(side='left')
        
        # Copy button
        ttk.Button(solution_actions, text="Copy Again", 
                  command=self.copy_current_solution).pack(side='right')
        
        # Clear button  
        ttk.Button(solution_actions, text="Clear", 
                  command=self.clear_solution_preview).pack(side='right', padx=(0, 5))
    
    def setup_ai_reasoning_section(self, parent):
        """Setup AI reasoning and analysis display section"""
        # AI Reasoning Frame
        reasoning_frame = ttk.LabelFrame(parent, text="AI Reasoning & Analysis", padding=10)
        reasoning_frame.pack(fill='x', pady=(0, 10))
        
        # Create notebook for tabs
        self.reasoning_notebook = ttk.Notebook(reasoning_frame)
        self.reasoning_notebook.pack(fill='both', expand=True)
        
        # Raw Instruction Text Tab
        raw_frame = ttk.Frame(self.reasoning_notebook)
        self.reasoning_notebook.add(raw_frame, text="Raw Text")
        
        raw_label = ttk.Label(raw_frame, text="Extracted Instruction Text:")
        raw_label.pack(anchor='w', pady=(0, 5))
        
        self.raw_text_display = scrolledtext.ScrolledText(raw_frame, height=6, font=('Consolas', 9))
        self.raw_text_display.pack(fill='both', expand=True)
        
        # Problem Analysis Tab
        analysis_frame = ttk.Frame(self.reasoning_notebook)
        self.reasoning_notebook.add(analysis_frame, text="Problem Analysis")
        
        analysis_label = ttk.Label(analysis_frame, text="AI Problem Analysis:")
        analysis_label.pack(anchor='w', pady=(0, 5))
        
        self.analysis_display = scrolledtext.ScrolledText(analysis_frame, height=6, font=('Consolas', 9))
        self.analysis_display.pack(fill='both', expand=True)
        
        # AI Approach Tab
        approach_frame = ttk.Frame(self.reasoning_notebook)
        self.reasoning_notebook.add(approach_frame, text="AI Approach")
        
        approach_label = ttk.Label(approach_frame, text="AI Solution Approach:")
        approach_label.pack(anchor='w', pady=(0, 5))
        
        self.approach_display = scrolledtext.ScrolledText(approach_frame, height=6, font=('Consolas', 9))
        self.approach_display.pack(fill='both', expand=True)
        
        # AI Reasoning Tab
        reasoning_tab_frame = ttk.Frame(self.reasoning_notebook)
        self.reasoning_notebook.add(reasoning_tab_frame, text="AI Reasoning")
        
        reasoning_tab_label = ttk.Label(reasoning_tab_frame, text="AI Step-by-Step Reasoning:")
        reasoning_tab_label.pack(anchor='w', pady=(0, 5))
        
        self.reasoning_display = scrolledtext.ScrolledText(reasoning_tab_frame, height=6, font=('Consolas', 9))
        self.reasoning_display.pack(fill='both', expand=True)
        
        # Raw AI Response Tab
        raw_ai_frame = ttk.Frame(self.reasoning_notebook)
        self.reasoning_notebook.add(raw_ai_frame, text="Raw AI Response")
        
        raw_ai_label = ttk.Label(raw_ai_frame, text="Complete AI Response:")
        raw_ai_label.pack(anchor='w', pady=(0, 5))
        
        self.raw_ai_display = scrolledtext.ScrolledText(raw_ai_frame, height=6, font=('Consolas', 9))
        self.raw_ai_display.pack(fill='both', expand=True)
        
        # AI Response Stats
        stats_frame = ttk.Frame(reasoning_frame)
        stats_frame.pack(fill='x', pady=(10, 0))
        
        self.confidence_var = tk.StringVar(value="Confidence: N/A")
        self.execution_time_var = tk.StringVar(value="Execution Time: N/A")
        self.response_length_var = tk.StringVar(value="Response Length: N/A")
        
        ttk.Label(stats_frame, textvariable=self.confidence_var).pack(side='left', padx=(0, 20))
        ttk.Label(stats_frame, textvariable=self.execution_time_var).pack(side='left', padx=(0, 20))
        ttk.Label(stats_frame, textvariable=self.response_length_var).pack(side='left')
    
    def setup_extracted_text_section(self, parent):
        """Setup extracted text display section in lower area"""
        # Extracted Text Frame
        text_frame = ttk.LabelFrame(parent, text="Extracted Text from Left Side", padding=10)
        text_frame.pack(fill='both', expand=True, pady=(0, 10))
        
        # Info label
        info_label = ttk.Label(text_frame, text="Live text extraction from left side of screen:")
        info_label.pack(anchor='w')
        
        # Text display area (larger for better visibility)
        text_container = ttk.Frame(text_frame)
        text_container.pack(fill='both', expand=True, pady=(5, 0))
        
        self.extracted_text_display = scrolledtext.ScrolledText(
            text_container, 
            height=8,  # Larger height for better visibility
            font=('Consolas', 10),  # Larger font
            wrap=tk.WORD
        )
        self.extracted_text_display.pack(fill='both', expand=True)
        
        # Set initial text
        self.extracted_text_display.insert('1.0', "No text extracted yet...\n\nClick 'Test Screenshot' to capture and analyze the current screen.")
        
        # Text info and actions
        text_actions = ttk.Frame(text_container)
        text_actions.pack(fill='x', pady=(5, 0))
        
        # Text info
        self.extracted_text_info = ttk.Label(text_actions, text="Status: Waiting for screenshot...")
        self.extracted_text_info.pack(side='left')
        
        # Action buttons
        ttk.Button(text_actions, text="Clear Text", 
                  command=self.clear_extracted_text).pack(side='right', padx=(0, 5))
        
        ttk.Button(text_actions, text="Copy Text", 
                  command=self.copy_extracted_text).pack(side='right')
    
    def setup_log_section(self, parent):
        """Setup log display"""
        log_frame = ttk.LabelFrame(parent, text="Live Logs", padding=10)
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
        test_frame = ttk.LabelFrame(parent, text="Quick Tests", padding=10)
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
        ttk.Button(test_button_frame, text="Type Code", 
                  command=self.type_test_code).pack(side='left', padx=(0, 5))
        
        # Copy to clipboard button
        ttk.Button(test_button_frame, text="Copy to Clipboard", 
                  command=self.copy_test_code).pack(side='left')
    
    def start_status_updates(self):
        """Start periodic status updates"""
        self.update_status()
        self.auto_update_screenshot()
        self.check_for_new_solution()
        self._update_animations()
        
        # Trigger initial screenshot analysis after a short delay
        if not hasattr(self, '_initial_analysis_done'):
            self.root.after(3000, self.perform_initial_analysis)
            self._initial_analysis_done = True
        
        self.root.after(2000, self.start_status_updates)  # Update every 2 seconds
    
    def perform_initial_analysis(self):
        """Perform initial screenshot analysis when window starts"""
        try:
            if self.core_service and hasattr(self.core_service, 'window_detector'):
                self.log_message("Performing initial screenshot analysis...", "INFO")
                screenshot = self.core_service.window_detector.capture_screen()
                if screenshot is not None:
                    self.update_screenshot_display(screenshot)
                    self.last_screenshot = screenshot
                    self.analyze_screenshot(screenshot)
                else:
                    self.log_message("Failed to capture initial screenshot", "WARNING")
        except Exception as e:
            self.log_message(f"Initial analysis error: {e}", "ERROR")
    
    def update_status(self):
        """Update status indicators"""
        try:
            if self.core_service:
                status = self.core_service.get_status()
                
                # Service status
                if status['running']:
                    self.status_vars['service'].set("Running")
                else:
                    self.status_vars['service'].set("Stopped")
                
                # AI status
                if status.get('ai_response_cached'):
                    self.status_vars['ai'].set("Ready")
                else:
                    self.status_vars['ai'].set("Preparing...")
                
                # Window detection
                if status.get('active_window_detected'):
                    self.status_vars['window'].set("Detected")
                else:
                    self.status_vars['window'].set("Scanning...")
                
            else:
                # No core service - standalone mode
                self.status_vars['service'].set("Test Mode")
                self.status_vars['ai'].set("Simulated")
                self.status_vars['window'].set("Mock")
                
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
                        # Also analyze the screenshot for text extraction
                        self.analyze_screenshot(screenshot)
                
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
            
            # Also update AI reasoning displays
            self.update_ai_reasoning_display(ai_response)
            
        except Exception as e:
            self.log_message(f"❌ Solution display error: {e}", "ERROR")
    
    def update_ai_reasoning_display(self, ai_response):
        """Update AI reasoning and analysis displays"""
        try:
            if not ai_response:
                self.clear_ai_reasoning_displays()
                return
            
            # Update raw instruction text
            if hasattr(ai_response, 'raw_instruction_text'):
                self.raw_text_display.delete(1.0, tk.END)
                self.raw_text_display.insert(1.0, ai_response.raw_instruction_text or "No instruction text available")
            
            # Update problem analysis
            if hasattr(ai_response, 'problem_analysis'):
                self.analysis_display.delete(1.0, tk.END)
                self.analysis_display.insert(1.0, ai_response.problem_analysis or "No analysis available")
            
            # Update AI approach
            if hasattr(ai_response, 'approach'):
                self.approach_display.delete(1.0, tk.END)
                self.approach_display.insert(1.0, ai_response.approach or "No approach available")
            
            # Update AI reasoning
            if hasattr(ai_response, 'reasoning'):
                self.reasoning_display.delete(1.0, tk.END)
                self.reasoning_display.insert(1.0, ai_response.reasoning or "No reasoning available")
            
            # Update raw AI response
            if hasattr(ai_response, 'raw_response'):
                self.raw_ai_display.delete(1.0, tk.END)
                self.raw_ai_display.insert(1.0, ai_response.raw_response or "No raw response available")
            
            # Update stats
            if hasattr(ai_response, 'confidence'):
                self.confidence_var.set(f"Confidence: {ai_response.confidence:.2f}")
            
            if hasattr(ai_response, 'execution_time'):
                self.execution_time_var.set(f"Execution Time: {ai_response.execution_time:.2f}s")
            
            if hasattr(ai_response, 'raw_response'):
                self.response_length_var.set(f"Response Length: {len(ai_response.raw_response)} chars")
            
            self.log_message("AI reasoning display updated")
            
        except Exception as e:
            self.log_message(f"AI reasoning display error: {e}", "ERROR")
    
    def clear_ai_reasoning_displays(self):
        """Clear all AI reasoning displays"""
        try:
            self.raw_text_display.delete(1.0, tk.END)
            self.raw_text_display.insert(1.0, "No instruction text available")
            
            self.analysis_display.delete(1.0, tk.END)
            self.analysis_display.insert(1.0, "No analysis available")
            
            self.approach_display.delete(1.0, tk.END)
            self.approach_display.insert(1.0, "No approach available")
            
            self.reasoning_display.delete(1.0, tk.END)
            self.reasoning_display.insert(1.0, "No reasoning available")
            
            self.raw_ai_display.delete(1.0, tk.END)
            self.raw_ai_display.insert(1.0, "No raw response available")
            
            self.confidence_var.set("Confidence: N/A")
            self.execution_time_var.set("Execution Time: N/A")
            self.response_length_var.set("Response Length: N/A")
            
        except Exception as e:
            self.log_message(f"Clear AI reasoning error: {e}", "ERROR")
    
    def clear_extracted_text(self):
        """Clear the extracted text display"""
        try:
            self.extracted_text_display.delete(1.0, tk.END)
            self.extracted_text_display.insert('1.0', "Text cleared...\n\nClick 'Test Screenshot' to capture and analyze the current screen.")
            self.extracted_text_info.configure(text="Status: Text cleared")
            self.log_message("Extracted text cleared", "INFO")
        except Exception as e:
            self.log_message(f"Clear text error: {e}", "ERROR")
    
    def copy_extracted_text(self):
        """Copy extracted text to clipboard"""
        try:
            text = self.extracted_text_display.get(1.0, tk.END).strip()
            if text and text != "No text extracted yet...\n\nClick 'Test Screenshot' to capture and analyze the current screen.":
                import pyperclip
                pyperclip.copy(text)
                self.log_message("Extracted text copied to clipboard", "SUCCESS")
            else:
                self.log_message("No text to copy", "WARNING")
        except Exception as e:
            self.log_message(f"Copy text error: {e}", "ERROR")
    
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
    
    def launch_region_selector(self):
        """Launch the interactive region selector"""
        try:
            self.log_message("Launching region selector...", "INFO")
            
            # Show confirmation popup first
            if not self.show_region_selector_popup():
                self.log_message("Region selection cancelled", "INFO")
                return
            
            # Import and launch region selector
            from src.region_selector import RegionSelector
            
            selector = RegionSelector()
            selected_region = selector.show_selector()
            
            if selected_region:
                self.log_message(f"Region selected: {selected_region}", "SUCCESS")
                # Reload the region in the window detector
                self.core_service.window_detector.load_user_region()
                self.log_message("Region configuration updated", "SUCCESS")
            else:
                self.log_message("No region selected", "INFO")
                
        except Exception as e:
            self.log_message(f"Region selector error: {e}", "ERROR")
    
    def show_region_selector_popup(self):
        """Show confirmation popup before launching region selector"""
        popup = tk.Toplevel(self.root)
        popup.title("Region Selection")
        popup.geometry("400x300")
        popup.attributes('-topmost', True)
        popup.resizable(False, False)
        
        # Center the popup
        popup.update_idletasks()
        x = (popup.winfo_screenwidth() // 2) - (400 // 2)
        y = (popup.winfo_screenheight() // 2) - (300 // 2)
        popup.geometry(f"400x300+{x}+{y}")
        
        # Main frame
        main_frame = ttk.Frame(popup, padding=20)
        main_frame.pack(fill='both', expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="🎯 Select Instruction Area", 
                               font=('Arial', 14, 'bold'))
        title_label.pack(pady=(0, 15))
        
        # Message
        message_text = """
This will open a region selector where you can:
• Draw a rectangle around your instruction area
• Select exactly where coding problems appear
• Configure the AI to read from the right location

Ready to proceed?
        """
        
        message_label = ttk.Label(main_frame, text=message_text, 
                                font=('Arial', 10), justify='left')
        message_label.pack(pady=(0, 20))
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x')
        
        # Variable to track user choice
        user_choice = {'proceed': False}
        
        def on_ok():
            user_choice['proceed'] = True
            popup.destroy()
        
        def on_cancel():
            user_choice['proceed'] = False
            popup.destroy()
        
        # OK button
        ok_button = ttk.Button(button_frame, text="OK", command=on_ok)
        ok_button.pack(side='right', padx=(10, 0))
        
        # Cancel button
        cancel_button = ttk.Button(button_frame, text="Cancel", command=on_cancel)
        cancel_button.pack(side='right')
        
        # Focus on OK button
        ok_button.focus_set()
        
        # Bind Enter key to OK button
        popup.bind('<Return>', lambda e: on_ok())
        popup.bind('<Escape>', lambda e: on_cancel())
        
        # Make popup modal
        popup.transient(self.root)
        popup.grab_set()
        
        # Wait for user response
        popup.wait_window()
        
        return user_choice['proceed']
    
    def test_screenshot(self):
        """Test screenshot functionality with detailed analysis"""
        self.log_message("Testing screenshot capture and analysis...", "INFO")
        
        try:
            if self.core_service:
                # Capture screenshot
                screenshot = self.core_service.window_detector.capture_screen()
                if screenshot is not None:
                    height, width = screenshot.shape[:2]
                    self.log_message(f"Screenshot successful: {width}x{height}", "SUCCESS")
                    
                    # Update display
                    self.update_screenshot_display(screenshot)
                    
                    # Store for later use
                    self.last_screenshot = screenshot
                    
                    # Analyze the screenshot
                    self.analyze_screenshot(screenshot)
                else:
                    self.log_message("Screenshot failed", "ERROR")
            else:
                # Simulate for testing
                self.log_message("Screenshot test (simulated): 1920x1080", "SUCCESS")
                self.create_mock_screenshot()
                
        except Exception as e:
            self.log_message(f"Screenshot error: {e}", "ERROR")
    
    def analyze_screenshot(self, screenshot):
        """Analyze screenshot and extract text for debugging"""
        try:
            self.log_message("Analyzing screenshot...", "INFO")
            
            # Get instruction region (prefer user-selected over auto-detected)
            instruction_region = self.core_service.window_detector.get_instruction_region(screenshot)
            if instruction_region:
                self.log_message(f"Instruction region: {instruction_region}", "SUCCESS")
                
                # Use direct OCR approach (which we know works)
                try:
                    import pytesseract
                    from PIL import Image
                    import cv2
                    
                    x, y, w, h = instruction_region['x'], instruction_region['y'], instruction_region['width'], instruction_region['height']
                    roi = screenshot[y:y+h, x:x+w]
                    
                    # Convert to PIL and extract text (BGR to RGB)
                    pil_image = Image.fromarray(cv2.cvtColor(roi, cv2.COLOR_BGR2RGB))
                    instruction_text = pytesseract.image_to_string(pil_image)
                    
                    if instruction_text:
                        self.log_message("Direct OCR text extraction successful", "SUCCESS")
                    else:
                        instruction_text = "No text could be extracted from this region"
                        
                except Exception as e:
                    self.log_message(f"Direct OCR extraction failed: {e}", "ERROR")
                    instruction_text = "Text extraction failed"
                
                if instruction_text:
                    self.log_message(f"Text extracted: {len(instruction_text)} chars", "SUCCESS")
                    
                    # Display full text in log area (lower section)
                    self.log_message("=" * 60, "INFO")
                    self.log_message("EXTRACTED TEXT FROM LEFT SIDE:", "SUCCESS")
                    self.log_message("=" * 60, "INFO")
                    
                    # Split text into lines and log each line
                    lines = instruction_text.split('\n')
                    for i, line in enumerate(lines[:20]):  # Show first 20 lines
                        if line.strip():
                            self.log_message(f"Line {i+1}: {line.strip()}", "INFO")
                    
                    if len(lines) > 20:
                        self.log_message(f"... and {len(lines) - 20} more lines", "INFO")
                    
                    self.log_message("=" * 60, "INFO")
                    
                    # Update the raw text display in AI reasoning section
                    self.raw_text_display.delete(1.0, tk.END)
                    self.raw_text_display.insert(1.0, instruction_text)
                    
                    # Update the extracted text display in lower area
                    self.extracted_text_display.delete(1.0, tk.END)
                    self.extracted_text_display.insert(1.0, instruction_text)
                    
                    # Update text info
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    self.extracted_text_info.configure(
                        text=f"Status: Text extracted at {timestamp} | Length: {len(instruction_text)} chars"
                    )
                    
                    # Check if it's a valid coding problem
                    if self.core_service.text_extractor.is_valid_coding_problem(instruction_text):
                        self.log_message("✅ Valid coding problem detected!", "SUCCESS")
                    else:
                        self.log_message("⚠️ Text doesn't appear to be a coding problem", "WARNING")
                else:
                    self.log_message("No text extracted from instruction region", "WARNING")
            else:
                self.log_message("No instruction region found", "WARNING")
                
        except Exception as e:
            self.log_message(f"Screenshot analysis error: {e}", "ERROR")
            import traceback
            traceback.print_exc()
    
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
            self.log_message(f"Display update error: {e}", "ERROR")
    
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
            self.log_message(f"Mock screenshot error: {e}", "ERROR")
    
    def test_ai(self):
        """Test AI connectivity"""
        self.log_message("Testing AI connection...", "INFO")
        
        try:
            if self.core_service:
                # Test with sample problem
                test_problem = "Write a function that returns the sum of two numbers."
                response = self.core_service.ai_client.generate_code_solution(test_problem)
                
                if response and response.confidence > 0.5:
                    self.log_message("AI test successful", "SUCCESS")
                    self.log_message(f"Generated {len(response.code)} chars of code", "INFO")
                    
                    # Update solution preview with test result
                    self.update_solution_display(response)
                    self.last_solution = response.code
                else:
                    self.log_message("AI test failed - low confidence", "ERROR")
            else:
                # Simulate for testing
                self.log_message("AI test (simulated): Generated sample code", "SUCCESS")
                
                # Create mock solution for testing
                self.create_mock_solution()
                
        except Exception as e:
            self.log_message(f"AI error: {e}", "ERROR")
    
    def simulate_tab_trigger(self):
        """Simulate a tab key trigger"""
        self.log_message("Simulating Tab key trigger...", "INFO")
        
        try:
            if self.core_service:
                # Simulate tab trigger
                self.core_service._on_user_input_detected("tab_triggered")
                self.status_vars['trigger'].set("Tab (simulated)")
                self.log_message("Tab trigger simulated", "SUCCESS")
            else:
                # Standalone simulation
                self.status_vars['trigger'].set("Tab (test mode)")
                self.log_message("Tab trigger (test mode)", "SUCCESS")
                
        except Exception as e:
            self.log_message(f"Tab simulation error: {e}", "ERROR")
    
    def type_test_code(self):
        """Type the test code from input field"""
        code = self.test_input.get('1.0', 'end-1c')
        self.log_message("Starting test typing...", "INFO")
        
        try:
            if self.core_service:
                # Use keyboard simulator
                success = self.core_service.keyboard_sim.type_text_naturally(code)
                if success:
                    self.log_message("Test typing completed", "SUCCESS")
                else:
                    self.log_message("Test typing failed", "ERROR")
            else:
                # Simulate typing
                self.log_message(f"Would type: {len(code)} characters", "SUCCESS")
                
        except Exception as e:
            self.log_message(f"Typing error: {e}", "ERROR")
    
    def copy_test_code(self):
        """Copy the test code to clipboard"""
        code = self.test_input.get('1.0', 'end-1c')
        self.log_message("Copying test code to clipboard...", "INFO")
        
        try:
            if self.core_service:
                # Use keyboard simulator's clipboard function
                success = self.core_service.keyboard_sim.copy_to_clipboard(code)
                if success:
                    self.log_message("Test code copied to clipboard", "SUCCESS")
                    self.log_message("Press Cmd+V (Mac) or Ctrl+V to paste", "INFO")
                else:
                    self.log_message("Failed to copy test code", "ERROR")
            else:
                # Use pyperclip directly
                import pyperclip
                pyperclip.copy(code)
                self.log_message("Test code copied to clipboard", "SUCCESS")
                self.log_message("Press Cmd+V (Mac) or Ctrl+V to paste", "INFO")
                
        except Exception as e:
            self.log_message(f"Clipboard error: {e}", "ERROR")
    
    def clear_logs(self):
        """Clear the log display"""
        self.log_text.delete('1.0', tk.END)
        self.log_lines.clear()
        self.log_message("Logs cleared", "INFO")
    
    def toggle_opacity(self):
        """Toggle window opacity"""
        current_alpha = self.root.attributes('-alpha')
        new_alpha = 0.5 if current_alpha > 0.7 else 0.9
        self.root.attributes('-alpha', new_alpha)
        self.log_message(f"Opacity: {int(new_alpha * 100)}%", "INFO")
    
    def close_window(self):
        """Close the test window"""
        self.log_message("Closing test window...", "INFO")
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
    
    def start_loading(self, process: str, message: str = "Processing..."):
        """Start loading animation for a process"""
        if process in self.loading_states:
            self.loading_states[process].set(message)
            
        if process in self.animation_states:
            self.animation_states[process]["active"] = True
            
        if process in self.progress_bars:
            self.progress_bars[process].configure(mode='indeterminate')
            self.progress_bars[process].start(10)  # Fast animation
    
    def stop_loading(self, process: str, message: str = "Complete", final_value: int = 100):
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
        loading_frames = ["●", "○", "●", "○", "●", "○", "●"]
        
        for process, state in self.animation_states.items():
            if state["active"]:
                state["frame"] = (state["frame"] + 1) % len(loading_frames)
                current_frame = loading_frames[state["frame"]]
                
                if process in self.loading_states:
                    current_text = self.loading_states[process].get()
                    if "Processing" in current_text:
                        # Update just the indicator part
                        base_text = current_text.replace("●", "").replace("○", "").strip()
                        self.loading_states[process].set(f"{current_frame} {base_text}")
    
    def simulate_screenshot_progress(self):
        """Simulate screenshot capture progress"""
        def progress():
            self.start_loading("screenshot", "Capturing...")
            self.set_progress("screenshot", 20, "Window Detection...")
            self.root.after(300, lambda: self.set_progress("screenshot", 40, "Left Panel Analysis..."))
            self.root.after(600, lambda: self.set_progress("screenshot", 60, "Instruction Extraction..."))
            self.root.after(900, lambda: self.set_progress("screenshot", 80, "Text Processing..."))
            self.root.after(1200, lambda: self.stop_loading("screenshot", "Complete"))
        
        threading.Thread(target=progress, daemon=True).start()
    
    def simulate_ai_progress(self):
        """Simulate AI processing progress"""
        def progress():
            self.start_loading("ai_processing", "Connecting...")
            self.set_progress("ai_processing", 20, "Sending Request...")
            self.root.after(500, lambda: self.set_progress("ai_processing", 40, "AI Thinking..."))
            self.root.after(1000, lambda: self.set_progress("ai_processing", 70, "Generating Code..."))
            self.root.after(1500, lambda: self.set_progress("ai_processing", 90, "Formatting..."))
            self.root.after(2000, lambda: self.stop_loading("ai_processing", "Solution Ready"))
        
        threading.Thread(target=progress, daemon=True).start()
    
    def simulate_typing_progress(self):
        """Simulate typing progress"""
        def progress():
            self.start_loading("typing", "Preparing...")
            self.set_progress("typing", 30, "Typing Code...")
            self.root.after(400, lambda: self.set_progress("typing", 60, "Adding Syntax..."))
            self.root.after(800, lambda: self.set_progress("typing", 85, "Finalizing..."))
            self.root.after(1200, lambda: self.stop_loading("typing", "Code Typed"))
        
        threading.Thread(target=progress, daemon=True).start()
    
    def simulate_clipboard_progress(self):
        """Simulate clipboard operation progress"""
        def progress():
            self.start_loading("clipboard", "Accessing...")
            self.set_progress("clipboard", 50, "Copying...")
            self.root.after(200, lambda: self.stop_loading("clipboard", "Copied"))
        
        threading.Thread(target=progress, daemon=True).start()
    
    def test_screenshot_with_progress(self):
        """Test screenshot with progress indicators"""
        self.log_message("Testing screenshot with progress...", "INFO")
        self.simulate_screenshot_progress()
        # Also call the regular screenshot function
        threading.Timer(1.0, self.test_screenshot).start()
    
    def test_ai_with_progress(self):
        """Test AI with progress indicators"""
        self.log_message("Testing AI with progress...", "INFO")
        self.simulate_ai_progress()
        # Create mock AI response with reasoning after progress completes
        threading.Timer(2.5, self.create_mock_ai_response_with_reasoning).start()
    
    def create_mock_ai_response_with_reasoning(self):
        """Create a mock AI response with detailed reasoning for testing"""
        try:
            from src.ai_client import CodeResponse
            
            # Mock instruction text
            mock_instruction = """Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.

You may assume that each input would have exactly one solution, and you may not use the same element twice.

You can return the answer in any order.

Example 1:
Input: nums = [2,7,11,15], target = 9
Output: [0,1]
Explanation: Because nums[0] + nums[1] == 9, we return [0, 1].

Example 2:
Input: nums = [3,2,4], target = 6
Output: [1,2]

Example 3:
Input: nums = [3,3], target = 6
Output: [0,1]"""
            
            # Mock AI response with reasoning
            mock_response = CodeResponse(
                code="""def twoSum(nums, target):
    # Create a hash map to store complements
    seen = {}
    
    # Iterate through the array
    for i, num in enumerate(nums):
        complement = target - num
        
        # If complement exists in hash map, we found our pair
        if complement in seen:
            return [seen[complement], i]
        
        # Store current number and its index
        seen[num] = i
    
    # No solution found (though problem guarantees one exists)
    return []""",
                language="python",
                explanation="Uses hash map for O(n) time complexity",
                confidence=0.95,
                execution_time=2.3,
                reasoning="""Step 1: Analyze the problem
- We need to find two numbers that sum to target
- Each input has exactly one solution
- We need to return indices, not values
- Cannot use same element twice

Step 2: Choose approach
- Brute force would be O(n²) - too slow
- Hash map approach gives O(n) time and space
- Store each number and its index as we iterate
- For each number, check if (target - num) exists

Step 3: Implementation details
- Use dictionary to store {number: index} pairs
- Iterate through array once
- For each number, calculate complement = target - num
- If complement exists in hash map, return [complement_index, current_index]
- Otherwise, store current number and continue

Step 4: Edge cases
- Problem guarantees exactly one solution exists
- Handle case where no solution found (though shouldn't happen)""",
                problem_analysis="""This is a classic Two Sum problem that tests understanding of:
1. Hash maps/dictionaries for efficient lookups
2. Time complexity optimization
3. Array manipulation and indexing
4. Problem constraints and edge cases

The key insight is using a hash map to achieve O(n) time complexity instead of O(n²) brute force approach.""",
                approach="Hash Map Approach: Use a dictionary to store numbers and their indices as we iterate through the array. For each number, check if its complement (target - num) exists in the hash map.",
                raw_response="""ANALYSIS:
This is a classic Two Sum problem that tests understanding of hash maps, time complexity optimization, and array manipulation. The key insight is using a hash map to achieve O(n) time complexity.

APPROACH:
Hash Map Approach: Use a dictionary to store numbers and their indices as we iterate through the array. For each number, check if its complement (target - num) exists in the hash map.

REASONING:
Step 1: Analyze the problem
- We need to find two numbers that sum to target
- Each input has exactly one solution
- We need to return indices, not values
- Cannot use same element twice

Step 2: Choose approach
- Brute force would be O(n²) - too slow
- Hash map approach gives O(n) time and space
- Store each number and its index as we iterate
- For each number, check if (target - num) exists

SOLUTION:
def twoSum(nums, target):
    # Create a hash map to store complements
    seen = {}
    
    # Iterate through the array
    for i, num in enumerate(nums):
        complement = target - num
        
        # If complement exists in hash map, we found our pair
        if complement in seen:
            return [seen[complement], i]
        
        # Store current number and its index
        seen[num] = i
    
    # No solution found (though problem guarantees one exists)
    return []"""
            )
            
            # Add raw instruction text
            mock_response.raw_instruction_text = mock_instruction
            
            # Update displays
            self.update_solution_display(mock_response)
            self.update_ai_reasoning_display(mock_response)
            
            self.log_message("Mock AI response with reasoning created for testing", "SUCCESS")
            
        except Exception as e:
            self.log_message(f"Mock AI response error: {e}", "ERROR")
    
    def run(self):
        """Run the test window"""
        self.log_message("CodeBumble Test Window Started", "SUCCESS")
        self.log_message("Press Simulate Tab to test activation", "INFO")
        self.root.mainloop()

def create_test_window(core_service=None):
    """Create and return a test window instance"""
    return TestWindow(core_service)

if __name__ == "__main__":
    # Standalone testing
    window = TestWindow()
    window.run()
