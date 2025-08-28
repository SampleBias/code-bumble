import tkinter as tk
from tkinter import ttk
import cv2
import numpy as np
from PIL import Image, ImageTk
import pyautogui
import json
import os
from datetime import datetime


class RegionSelector:
    """Interactive region selector for defining instruction areas"""
    
    def __init__(self, config_file='region_config.json'):
        self.config_file = config_file
        self.root = None
        self.canvas = None
        self.screenshot = None
        self.photo = None
        self.selection_start = None
        self.selection_end = None
        self.selection_rect = None
        self.selected_region = None
        
    def capture_full_screen(self):
        """Capture the full screen for region selection"""
        try:
            screenshot = pyautogui.screenshot()
            return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        except Exception as e:
            print(f"Error capturing screen: {e}")
            return None
    
    def resize_for_display(self, image, max_width=1200, max_height=800):
        """Resize image to fit on screen while maintaining aspect ratio"""
        height, width = image.shape[:2]
        
        # Calculate scale factor
        scale_x = max_width / width
        scale_y = max_height / height
        scale = min(scale_x, scale_y)
        
        if scale < 1:
            new_width = int(width * scale)
            new_height = int(height * scale)
            resized = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
            return resized, scale
        else:
            return image, 1.0
    
    def on_mouse_down(self, event):
        """Handle mouse button press"""
        self.selection_start = (event.x, event.y)
        self.selection_end = None
        if self.selection_rect:
            self.canvas.delete(self.selection_rect)
            self.selection_rect = None
    
    def on_mouse_move(self, event):
        """Handle mouse movement for live rectangle drawing"""
        if self.selection_start:
            if self.selection_rect:
                self.canvas.delete(self.selection_rect)
            
            # Draw live selection rectangle
            x1, y1 = self.selection_start
            x2, y2 = event.x, event.y
            
            self.selection_rect = self.canvas.create_rectangle(
                x1, y1, x2, y2,
                outline='red',
                width=2,
                dash=(5, 5)
            )
    
    def on_mouse_up(self, event):
        """Handle mouse button release"""
        if self.selection_start:
            self.selection_end = (event.x, event.y)
            self.finalize_selection()
    
    def finalize_selection(self):
        """Finalize the region selection"""
        if not self.selection_start or not self.selection_end:
            return
        
        # Get the selected coordinates
        x1, y1 = self.selection_start
        x2, y2 = self.selection_end
        
        # Ensure coordinates are in correct order
        x_min, x_max = min(x1, x2), max(x1, x2)
        y_min, y_max = min(y1, y2), max(y1, y2)
        
        # Convert back to original screen coordinates
        if hasattr(self, 'scale_factor'):
            x_min = int(x_min / self.scale_factor)
            y_min = int(y_min / self.scale_factor)
            x_max = int(x_max / self.scale_factor)
            y_max = int(y_max / self.scale_factor)
        
        self.selected_region = {
            'x': x_min,
            'y': y_min,
            'width': x_max - x_min,
            'height': y_max - y_min,
            'confidence': 1.0,
            'debug_info': 'User-selected region'
        }
        
        print(f"Selected region: {self.selected_region}")
        
        # Save the configuration
        self.save_region_config()
        
        # Close the selector
        self.root.quit()
    
    def save_region_config(self):
        """Save the selected region to configuration file"""
        if not self.selected_region:
            return
        
        config = {
            'instruction_region': self.selected_region,
            'last_updated': datetime.now().isoformat(),
            'screen_resolution': {
                'width': self.screenshot.shape[1],
                'height': self.screenshot.shape[0]
            }
        }
        
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            print(f"Region configuration saved to {self.config_file}")
        except Exception as e:
            print(f"Error saving configuration: {e}")
    
    def load_region_config(self):
        """Load the region configuration from file"""
        if not os.path.exists(self.config_file):
            return None
        
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            return config.get('instruction_region')
        except Exception as e:
            print(f"Error loading configuration: {e}")
            return None
    
    def show_selector(self):
        """Show the interactive region selector"""
        # Show initial popup with instructions
        if not self.show_instruction_popup():
            return None
        
        # Capture screen
        self.screenshot = self.capture_full_screen()
        if self.screenshot is None:
            print("Failed to capture screen")
            return None
        
        # Resize for display
        display_image, self.scale_factor = self.resize_for_display(self.screenshot)
        
        # Create window
        self.root = tk.Tk()
        self.root.title("CodeBumble - Select Instruction Region")
        self.root.attributes('-topmost', True)
        
        # Add instructions
        instruction_frame = ttk.Frame(self.root)
        instruction_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(instruction_frame, text="🎯 Select Your Instruction Area", 
                 font=('Arial', 14, 'bold')).pack()
        ttk.Label(instruction_frame, 
                 text="Click and drag to draw a rectangle around the area containing coding instructions/exercises", 
                 font=('Arial', 10)).pack()
        ttk.Label(instruction_frame, 
                 text="This is where the AI will read the problem description", 
                 font=('Arial', 9, 'italic')).pack()
        
        # Create canvas for image display
        canvas_frame = ttk.Frame(self.root)
        canvas_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Convert image for tkinter
        rgb_image = cv2.cvtColor(display_image, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(rgb_image)
        self.photo = ImageTk.PhotoImage(pil_image)
        
        # Create canvas
        self.canvas = tk.Canvas(canvas_frame, width=display_image.shape[1], height=display_image.shape[0])
        self.canvas.pack()
        
        # Display image
        self.canvas.create_image(0, 0, anchor='nw', image=self.photo)
        
        # Bind mouse events
        self.canvas.bind('<Button-1>', self.on_mouse_down)
        self.canvas.bind('<B1-Motion>', self.on_mouse_move)
        self.canvas.bind('<ButtonRelease-1>', self.on_mouse_up)
        
        # Add buttons
        button_frame = ttk.Frame(self.root)
        button_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(button_frame, text="Cancel", 
                  command=self.root.quit).pack(side='right', padx=(5, 0))
        ttk.Button(button_frame, text="Reset Selection", 
                  command=self.reset_selection).pack(side='right', padx=(5, 0))
        
        # Show current configuration if exists
        current_region = self.load_region_config()
        if current_region:
            info_text = f"Current region: ({current_region['x']}, {current_region['y']}) " \
                       f"{current_region['width']}x{current_region['height']}"
            ttk.Label(button_frame, text=info_text, font=('Arial', 9)).pack(side='left')
        
        # Start the GUI
        self.root.mainloop()
        
        # Clean up
        if self.root:
            self.root.destroy()
        
        return self.selected_region
    
    def show_instruction_popup(self):
        """Show initial popup with instructions"""
        popup = tk.Tk()
        popup.title("CodeBumble - Region Selection")
        popup.geometry("500x400")
        popup.attributes('-topmost', True)
        popup.resizable(False, False)
        
        # Center the popup
        popup.update_idletasks()
        x = (popup.winfo_screenwidth() // 2) - (500 // 2)
        y = (popup.winfo_screenheight() // 2) - (400 // 2)
        popup.geometry(f"500x400+{x}+{y}")
        
        # Main frame
        main_frame = ttk.Frame(popup, padding=20)
        main_frame.pack(fill='both', expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="🔍 Select Instruction Area", 
                               font=('Arial', 16, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # Instructions
        instructions_frame = ttk.LabelFrame(main_frame, text="Instructions", padding=15)
        instructions_frame.pack(fill='x', pady=(0, 20))
        
        instruction_text = """
This tool will help you select the area on your screen that contains coding instructions and problem descriptions.

What you'll do:
1. Click "Start Selection" below
2. A screenshot of your screen will appear
3. Click and drag to draw a rectangle around the instruction area
4. The selected area will be used for text extraction

Tips:
• Select the area that contains the problem description
• Include any example inputs/outputs
• Avoid selecting the code editor area
• Make sure the area is clearly visible
        """
        
        instruction_label = ttk.Label(instructions_frame, text=instruction_text, 
                                     font=('Arial', 10), justify='left')
        instruction_label.pack(anchor='w')
        
        # Current region info (if exists)
        current_region = self.load_region_config()
        if current_region:
            info_frame = ttk.LabelFrame(main_frame, text="Current Configuration", padding=10)
            info_frame.pack(fill='x', pady=(0, 20))
            
            info_text = f"Current region: ({current_region['x']}, {current_region['y']}) " \
                       f"{current_region['width']}x{current_region['height']}"
            ttk.Label(info_frame, text=info_text, font=('Arial', 9)).pack()
            ttk.Label(info_frame, text="Click 'Start Selection' to change this region", 
                     font=('Arial', 9, 'italic')).pack()
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=(20, 0))
        
        # Variable to track user choice
        user_choice = {'proceed': False}
        
        def on_start():
            user_choice['proceed'] = True
            popup.destroy()
        
        def on_cancel():
            user_choice['proceed'] = False
            popup.destroy()
        
        # Start button
        start_button = ttk.Button(button_frame, text="Start Selection", 
                                 command=on_start, style='Accent.TButton')
        start_button.pack(side='right', padx=(10, 0))
        
        # Cancel button
        cancel_button = ttk.Button(button_frame, text="Cancel", 
                                  command=on_cancel)
        cancel_button.pack(side='right')
        
        # Focus on start button
        start_button.focus_set()
        
        # Bind Enter key to start button
        popup.bind('<Return>', lambda e: on_start())
        popup.bind('<Escape>', lambda e: on_cancel())
        
        # Wait for user response
        popup.wait_window()
        
        return user_choice['proceed']
    
    def reset_selection(self):
        """Reset the current selection"""
        if self.selection_rect:
            self.canvas.delete(self.selection_rect)
            self.selection_rect = None
        self.selection_start = None
        self.selection_end = None


def main():
    """Test the region selector"""
    selector = RegionSelector()
    region = selector.show_selector()
    
    if region:
        print(f"Selected region: {region}")
    else:
        print("No region selected")


if __name__ == "__main__":
    main()
