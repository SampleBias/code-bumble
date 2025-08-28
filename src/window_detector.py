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
            return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
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
        
        # Look for typical coding challenge layout:
        # - Instructions panel on right (30-50% of width)
        # - Code editor on left (50-70% of width)
        
        # Detect text-heavy regions (likely instructions)
        gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
        
        # Find regions with high text density
        text_regions = self._find_text_regions(gray)
        
        # Analyze layout to identify instruction panel vs code editor
        layout = self._analyze_layout(text_regions, width, height)
        
        if layout and self._validate_coding_layout(layout):
            return layout
            
        return None
    
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
        
        # Look for typical coding challenge layout
        for i, region in enumerate(text_regions):
            # Check if this could be an instruction panel (usually on right)
            if region.x > width * 0.4:  # Right side of screen
                # Look for code editor region on the left
                for other_region in text_regions[:i]:
                    if other_region.x < width * 0.6 and other_region.width > width * 0.3:
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
        
        # Instruction panel should be on the right side
        if instruction['x'] <= editor['x']:
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
