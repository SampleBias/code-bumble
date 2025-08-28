"""
Window Detection and Screenshot System
Handles browser window detection and screenshot capture for coding interfaces.
"""

import cv2
import numpy as np
import pyautogui
import time
from typing import Optional, Tuple, Dict, List
import logging
from dataclasses import dataclass

@dataclass
class WindowRegion:
    """Represents a detected window region"""
    x: int
    y: int
    width: int
    height: int
    confidence: float
    window_type: str  # 'browser', 'ide', 'instructions'

class WindowDetector:
    """Detects coding challenge interfaces in browser windows"""
    
    def __init__(self, debug_mode: bool = False):
        self.debug_mode = debug_mode
        self.logger = logging.getLogger(__name__)
        self.user_region = None
        self.load_user_region()
        
        # Disable pyautogui failsafe for smooth operation
        pyautogui.FAILSAFE = False
        
        # Common browser window indicators
        self.browser_indicators = [
            "chrome", "firefox", "safari", "edge", "brave"
        ]
        
        # IDE/coding interface indicators
        self.ide_indicators = [
            "code", "editor", "leetcode", "hackerrank", "codepen", 
            "codesandbox", "repl.it", "github", "gitlab"
        ]
    
    def capture_screen(self) -> np.ndarray:
        """Capture full screen screenshot"""
        try:
            screenshot = pyautogui.screenshot()
            screenshot_array = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            if screenshot_array is not None and screenshot_array.size > 0:
                return screenshot_array
            else:
                self.logger.error("Screenshot array is empty or None")
                return None
        except Exception as e:
            self.logger.error(f"Failed to capture screenshot: {e}")
            return None
    
    def detect_coding_interface(self, screenshot: np.ndarray) -> Optional[Dict]:
        """
        Detect coding challenge interface layout
        Returns dict with instruction_panel and code_editor regions
        """
        if screenshot is None:
            return None
            
        height, width = screenshot.shape[:2]
        
        # Use a simpler, more reliable approach
        # Assume typical coding challenge layout with instructions on LEFT
        layout = self._simple_layout_detection(width, height)
        
        if self.debug_mode:
            self.logger.debug(f"Detected layout: {layout}")
        
        return layout
    
    def _simple_layout_detection(self, width: int, height: int) -> Dict:
        """Simple layout detection based on typical coding challenge interfaces"""
        # Most coding challenges have instructions on the left (30-50% width)
        # and code editor on the right (50-70% width)
        
        instruction_width = int(width * 0.4)  # 40% of screen width
        editor_width = width - instruction_width
        
        layout = {
            'instruction_panel': {
                'x': 0,
                'y': 0,
                'width': instruction_width,
                'height': height,
                'confidence': 0.8,
                'debug_info': 'Simple left-side detection'
            },
            'code_editor': {
                'x': instruction_width,
                'y': 0,
                'width': editor_width,
                'height': height,
                'confidence': 0.8,
                'debug_info': 'Simple right-side detection'
            }
        }
        
        return layout
    
    def load_user_region(self):
        """Load user-selected region from configuration"""
        try:
            import json
            import os
            
            config_file = 'region_config.json'
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    self.user_region = config.get('instruction_region')
                    if self.user_region:
                        self.logger.info(f"Loaded user region: {self.user_region}")
            else:
                self.logger.info("No user region configuration found")
        except Exception as e:
            self.logger.error(f"Error loading user region: {e}")
    
    def get_instruction_region(self, screenshot: np.ndarray) -> Optional[Dict]:
        """Get instruction region - prefer user-selected over auto-detected"""
        if self.user_region:
            # Use user-selected region
            return self.user_region
        else:
            # Fall back to auto-detection
            layout = self.detect_coding_interface(screenshot)
            return layout.get('instruction_panel') if layout else None
    
    def _find_text_regions(self, gray_image: np.ndarray) -> List[WindowRegion]:
        """Find regions with high text density"""
        regions = []
        
        # Use edge detection to find text-like patterns
        edges = cv2.Canny(gray_image, 50, 150)
        
        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        height, width = gray_image.shape
        
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            
            # Filter by size - looking for substantial regions
            if w > width * 0.2 and h > height * 0.1:
                # Calculate text density in this region
                roi = gray_image[y:y+h, x:x+w]
                text_density = self._calculate_text_density(roi)
                
                if text_density > 0.3:  # Threshold for text-heavy regions
                    regions.append(WindowRegion(
                        x=x, y=y, width=w, height=h,
                        confidence=text_density,
                        window_type='text_region'
                    ))
        
        return regions
    
    def _calculate_text_density(self, roi: np.ndarray) -> float:
        """Calculate text density in a region of interest"""
        # Apply adaptive threshold to highlight text
        thresh = cv2.adaptiveThreshold(
            roi, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        
        # Count white pixels (text)
        white_pixels = np.sum(thresh == 255)
        total_pixels = roi.shape[0] * roi.shape[1]
        
        return white_pixels / total_pixels if total_pixels > 0 else 0
    
    def _analyze_layout(self, text_regions: List[WindowRegion], width: int, height: int) -> Optional[Dict]:
        """Analyze regions to identify instruction panel and code editor"""
        if len(text_regions) < 2:
            return None
        
        # Sort regions by x position (left to right)
        text_regions.sort(key=lambda r: r.x)
        
        # Look for typical coding challenge layout with instructions on LEFT
        for i, region in enumerate(text_regions):
            # Check if this could be an instruction panel (on LEFT side)
            if region.x < width * 0.6:  # Left side of screen
                # Look for code editor region on the right
                for other_region in text_regions[i+1:]:
                    if other_region.x > width * 0.4 and other_region.width > width * 0.3:
                        return {
                            'instruction_panel': {
                                'x': region.x,
                                'y': region.y,
                                'width': region.width,
                                'height': region.height,
                                'confidence': region.confidence
                            },
                            'code_editor': {
                                'x': other_region.x,
                                'y': other_region.y,
                                'width': other_region.width,
                                'height': other_region.height,
                                'confidence': other_region.confidence
                            }
                        }
        
        return None
    
    def _validate_coding_layout(self, layout: Dict) -> bool:
        """Validate that detected layout looks like a coding challenge interface"""
        instruction = layout.get('instruction_panel', {})
        editor = layout.get('code_editor', {})
        
        # Basic validation checks
        if not instruction or not editor:
            return False
        
        # Instruction panel should be on the LEFT side
        if instruction['x'] >= editor['x']:
            return False
        
        # Both regions should have reasonable confidence
        if instruction['confidence'] < 0.2 or editor['confidence'] < 0.2:
            return False
        
        # Regions should have reasonable sizes
        if instruction['width'] < 200 or editor['width'] < 300:
            return False
        
        return True
    
    def extract_instruction_text(self, screenshot: np.ndarray, instruction_region: Dict) -> str:
        """Extract text from instruction panel region"""
        x = instruction_region['x']
        y = instruction_region['y']
        w = instruction_region['width']
        h = instruction_region['height']
        
        # Extract region of interest
        roi = screenshot[y:y+h, x:x+w]
        
        # This will be implemented with OCR in the next module
        # For now, return placeholder
        return "Instruction text will be extracted here"
    
    def find_code_input_field(self, screenshot: np.ndarray, editor_region: Dict) -> Optional[Tuple[int, int]]:
        """Find the active code input field within the editor region"""
        # This will detect text cursor or active input field
        # For now, return center of editor region
        x = editor_region['x'] + editor_region['width'] // 2
        y = editor_region['y'] + editor_region['height'] // 2
        
        return (x, y)
    
    def is_coding_window_active(self) -> bool:
        """Check if a coding challenge window is currently active"""
        try:
            # Get active window title (platform-specific implementation needed)
            # For now, return True as placeholder
            return True
        except Exception as e:
            self.logger.error(f"Failed to check active window: {e}")
            return False
