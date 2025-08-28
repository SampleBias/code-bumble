"""
Text Extraction and OCR System
Handles text extraction from instruction panels using OCR.
"""

import cv2
import numpy as np
import pytesseract
import re
from typing import Optional, Dict, List
import logging
from PIL import Image

class TextExtractor:
    """Extracts and processes text from instruction panels"""
    
    def __init__(self, debug_mode: bool = False):
        self.debug_mode = debug_mode
        self.logger = logging.getLogger(__name__)
        
        # Configure Tesseract for better accuracy
        self.tesseract_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ.,;:!?()[]{}+-*/=<>_@#$%^&|\\"\' \t\n'
    
    def extract_text_from_region(self, screenshot: np.ndarray, region: Dict) -> str:
        """Extract text from a specific region using OCR"""
        try:
            # Extract region of interest
            x, y, w, h = region['x'], region['y'], region['width'], region['height']
            roi = screenshot[y:y+h, x:x+w]
            
            # Preprocess image for better OCR accuracy
            processed_roi = self._preprocess_for_ocr(roi)
            
            # Convert to PIL Image for Tesseract
            pil_image = Image.fromarray(processed_roi)
            
            # Extract text using Tesseract
            text = pytesseract.image_to_string(pil_image, config=self.tesseract_config)
            
            # Clean and format the extracted text
            cleaned_text = self._clean_extracted_text(text)
            
            if self.debug_mode:
                self.logger.debug(f"Extracted text length: {len(cleaned_text)}")
                self.logger.debug(f"First 200 chars: {cleaned_text[:200]}")
            
            return cleaned_text
            
        except Exception as e:
            self.logger.error(f"Failed to extract text from region: {e}")
            return ""
    
    def _preprocess_for_ocr(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image to improve OCR accuracy"""
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # Resize image for better OCR (OCR works better on larger images)
        height, width = gray.shape
        if height < 100 or width < 100:
            scale_factor = max(2.0, 100.0 / min(height, width))
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            gray = cv2.resize(gray, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
        
        # Apply Gaussian blur to reduce noise
        gray = cv2.GaussianBlur(gray, (1, 1), 0)
        
        # Apply adaptive threshold for better text contrast
        thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        
        # Apply morphological operations to clean up the image
        kernel = np.ones((1, 1), np.uint8)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
        
        return thresh
    
    def _clean_extracted_text(self, text: str) -> str:
        """Clean and format extracted text"""
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove common OCR artifacts
        text = re.sub(r'[|\\]', '', text)  # Remove common misread characters
        
        # Fix common character misreads
        replacements = {
            '0': 'O',  # Sometimes O is read as 0
            '1': 'l',  # Sometimes l is read as 1
            '5': 'S',  # Sometimes S is read as 5
        }
        
        # Only apply replacements in context where they make sense
        # This is a basic implementation - could be improved with more sophisticated logic
        
        # Strip leading/trailing whitespace
        text = text.strip()
        
        return text
    
    def extract_problem_details(self, text: str) -> Dict[str, str]:
        """Extract structured information from problem description"""
        details = {
            'title': '',
            'description': '',
            'examples': [],
            'constraints': '',
            'difficulty': '',
            'topics': []
        }
        
        try:
            lines = text.split('\n')
            
            # Try to identify title (usually first significant line)
            for line in lines:
                line = line.strip()
                if len(line) > 10 and not line.startswith(('Example', 'Input', 'Output', 'Constraint')):
                    details['title'] = line
                    break
            
            # Extract examples
            examples = self._extract_examples(text)
            details['examples'] = examples
            
            # Extract constraints
            constraints = self._extract_constraints(text)
            details['constraints'] = constraints
            
            # The rest is considered description
            details['description'] = text
            
        except Exception as e:
            self.logger.error(f"Failed to extract problem details: {e}")
            details['description'] = text
        
        return details
    
    def _extract_examples(self, text: str) -> List[Dict[str, str]]:
        """Extract examples from problem text"""
        examples = []
        
        # Look for example patterns
        example_pattern = r'Example\s*\d*:?\s*\n?(.*?)(?=Example|\n\n|Constraint|$)'
        matches = re.finditer(example_pattern, text, re.DOTALL | re.IGNORECASE)
        
        for match in matches:
            example_text = match.group(1).strip()
            
            # Try to parse input/output
            input_match = re.search(r'Input:?\s*(.+?)(?=Output|$)', example_text, re.DOTALL | re.IGNORECASE)
            output_match = re.search(r'Output:?\s*(.+?)(?=Explanation|$)', example_text, re.DOTALL | re.IGNORECASE)
            
            example = {
                'input': input_match.group(1).strip() if input_match else '',
                'output': output_match.group(1).strip() if output_match else '',
                'full_text': example_text
            }
            examples.append(example)
        
        return examples
    
    def _extract_constraints(self, text: str) -> str:
        """Extract constraints from problem text"""
        # Look for constraints section
        constraint_pattern = r'Constraint[s]?:?\s*(.+?)(?=\n\n|Example|$)'
        match = re.search(constraint_pattern, text, re.DOTALL | re.IGNORECASE)
        
        if match:
            return match.group(1).strip()
        
        return ""
    
    def is_valid_coding_problem(self, text: str) -> bool:
        """Check if extracted text appears to be a valid coding problem"""
        if len(text) < 50:  # Too short to be a meaningful problem
            return False
        
        # Look for common coding problem indicators
        indicators = [
            'function', 'return', 'input', 'output', 'example',
            'algorithm', 'complexity', 'constraint', 'given',
            'implement', 'write', 'code', 'solution'
        ]
        
        text_lower = text.lower()
        indicator_count = sum(1 for indicator in indicators if indicator in text_lower)
        
        # Should have at least 3 indicators to be considered a coding problem
        return indicator_count >= 3
    
    def extract_function_signature(self, text: str) -> Optional[str]:
        """Extract function signature if present in the problem"""
        # Look for function signature patterns
        patterns = [
            r'def\s+(\w+)\s*\([^)]*\)\s*:',  # Python
            r'function\s+(\w+)\s*\([^)]*\)\s*{',  # JavaScript
            r'public\s+\w+\s+(\w+)\s*\([^)]*\)\s*{',  # Java
            r'\w+\s+(\w+)\s*\([^)]*\)\s*{',  # C/C++
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)
        
        return None
