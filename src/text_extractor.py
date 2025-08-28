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
        
        # Tesseract configuration removed to avoid quoting issues
    
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
            
            # Extract text using Tesseract (no config to avoid quoting issues)
            text = pytesseract.image_to_string(pil_image)
            
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
        """Preprocess image to improve OCR accuracy for instruction text"""
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # Resize image for better OCR (OCR works better on larger images)
        height, width = gray.shape
        if height < 200 or width < 200:
            scale_factor = max(2.0, 200.0 / min(height, width))
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            gray = cv2.resize(gray, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
        
        # Apply bilateral filter to reduce noise while preserving edges
        gray = cv2.bilateralFilter(gray, 9, 75, 75)
        
        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization) for better contrast
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        gray = clahe.apply(gray)
        
        # Apply adaptive threshold for better text contrast
        thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        
        # Apply morphological operations to clean up the image
        kernel = np.ones((1, 1), np.uint8)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
        
        # Remove small noise
        kernel = np.ones((2, 2), np.uint8)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
        
        return thresh
    
    def _clean_extracted_text(self, text: str) -> str:
        """Clean and format extracted text for coding problems"""
        if not text:
            return ""
        
        # Remove excessive whitespace but preserve line breaks
        text = re.sub(r'[ \t]+', ' ', text)  # Multiple spaces/tabs to single space
        text = re.sub(r'\n\s*\n', '\n\n', text)  # Multiple newlines to double newline
        
        # Remove common OCR artifacts
        text = re.sub(r'[|\\]', '', text)  # Remove common misread characters
        
        # Fix common character misreads in coding context
        replacements = {
            '0': 'O',  # Sometimes O is read as 0 (in function names)
            '1': 'l',  # Sometimes l is read as 1 (in variable names)
            '5': 'S',  # Sometimes S is read as 5
            'rn': 'm',  # Sometimes m is read as rn
            'cl': 'd',  # Sometimes d is read as cl
        }
        
        # Apply replacements only in appropriate contexts
        for old, new in replacements.items():
            # Only replace in function names, variable names, etc.
            text = re.sub(r'\b' + old + r'\b', new, text)
        
        # Fix common coding-specific misreads
        text = re.sub(r'def\s+(\w+)', r'def \1', text)  # Fix function definitions
        text = re.sub(r'return\s+(\w+)', r'return \1', text)  # Fix return statements
        
        # Clean up common OCR issues in code blocks
        text = re.sub(r'(\w+)\s*=\s*(\w+)', r'\1 = \2', text)  # Fix assignments
        text = re.sub(r'(\w+)\s*\(\s*(\w+)', r'\1(\2', text)  # Fix function calls
        
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
            'topics': [],
            'function_signature': ''
        }
        
        try:
            lines = text.split('\n')
            
            # Try to identify title (usually first significant line)
            for line in lines:
                line = line.strip()
                if len(line) > 10 and not line.startswith(('Example', 'Input', 'Output', 'Constraint', 'Follow')):
                    details['title'] = line
                    break
            
            # Extract function signature if present
            function_sig = self.extract_function_signature(text)
            if function_sig:
                details['function_signature'] = function_sig
            
            # Extract examples
            examples = self._extract_examples(text)
            details['examples'] = examples
            
            # Extract constraints
            constraints = self._extract_constraints(text)
            details['constraints'] = constraints
            
            # Extract difficulty and topics if present
            difficulty = self._extract_difficulty(text)
            if difficulty:
                details['difficulty'] = difficulty
            
            topics = self._extract_topics(text)
            if topics:
                details['topics'] = topics
            
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
    
    def extract_instruction_text(self, screenshot: np.ndarray, left_region: Dict) -> str:
        """Extract instruction text specifically from the left side of the screenshot"""
        try:
            # Extract the left region (instruction panel)
            x, y, w, h = left_region['x'], left_region['y'], left_region['width'], left_region['height']
            
            if self.debug_mode:
                self.logger.debug(f"Extracting from region: x={x}, y={y}, w={w}, h={h}")
                self.logger.debug(f"Screenshot shape: {screenshot.shape}")
            
            # Ensure coordinates are within bounds
            height, width = screenshot.shape[:2]
            x = max(0, min(x, width-1))
            y = max(0, min(y, height-1))
            w = min(w, width - x)
            h = min(h, height - y)
            
            if w <= 0 or h <= 0:
                self.logger.error(f"Invalid region dimensions: w={w}, h={h}")
                return ""
            
            instruction_roi = screenshot[y:y+h, x:x+w]
            
            if self.debug_mode:
                self.logger.debug(f"ROI shape: {instruction_roi.shape}")
                # Save debug image
                cv2.imwrite('/tmp/debug_instruction_roi.png', instruction_roi)
                self.logger.debug("Saved debug ROI to /tmp/debug_instruction_roi.png")
            
            # Use simple approach like the working direct OCR
            # Convert to PIL Image for Tesseract (BGR to RGB)
            pil_image = Image.fromarray(cv2.cvtColor(instruction_roi, cv2.COLOR_BGR2RGB))
            
            # Extract text using Tesseract (no config to avoid quoting issues)
            text = pytesseract.image_to_string(pil_image)
            
            if self.debug_mode:
                self.logger.debug(f"Raw OCR text: {repr(text[:200])}")
            
            # Clean and format the extracted text
            cleaned_text = self._clean_extracted_text(text)
            
            if self.debug_mode:
                self.logger.debug(f"Extracted instruction text length: {len(cleaned_text)}")
                self.logger.debug(f"Instruction text preview: {cleaned_text[:300]}")
            
            return cleaned_text
            
        except Exception as e:
            self.logger.error(f"Failed to extract instruction text: {e}")
            import traceback
            traceback.print_exc()
            return ""
    
    def _preprocess_for_instruction_ocr(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image specifically for instruction text OCR"""
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # Resize for better OCR (instructions are usually smaller text)
        height, width = gray.shape
        if height < 300 or width < 300:
            scale_factor = max(2.5, 300.0 / min(height, width))
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            gray = cv2.resize(gray, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
        
        # Apply bilateral filter to reduce noise while preserving text edges
        gray = cv2.bilateralFilter(gray, 9, 75, 75)
        
        # Apply CLAHE for better contrast in instruction text
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        gray = clahe.apply(gray)
        
        # Apply adaptive threshold optimized for instruction text
        thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, 3
        )
        
        # Apply morphological operations to clean up instruction text
        kernel = np.ones((1, 1), np.uint8)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        
        # Remove small noise that might interfere with instruction text
        kernel = np.ones((2, 2), np.uint8)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
        
        return thresh
    
    def _extract_difficulty(self, text: str) -> str:
        """Extract difficulty level from problem text"""
        difficulty_patterns = [
            r'Difficulty:\s*(Easy|Medium|Hard)',
            r'(Easy|Medium|Hard)\s*difficulty',
            r'Level:\s*(Easy|Medium|Hard)',
            r'(Easy|Medium|Hard)'
        ]
        
        for pattern in difficulty_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return ""
    
    def _extract_topics(self, text: str) -> List[str]:
        """Extract topic tags from problem text"""
        topics = []
        
        # Common coding problem topics
        common_topics = [
            'Array', 'String', 'Hash Table', 'Dynamic Programming', 'Math',
            'Sorting', 'Greedy', 'Depth-First Search', 'Binary Search',
            'Database', 'Breadth-First Search', 'Tree', 'Matrix',
            'Two Pointers', 'Bit Manipulation', 'Stack', 'Heap',
            'Design', 'Graph', 'Simulation', 'Backtracking',
            'Sliding Window', 'Union Find', 'Linked List', 'Recursion'
        ]
        
        text_lower = text.lower()
        for topic in common_topics:
            if topic.lower() in text_lower:
                topics.append(topic)
        
        return topics
