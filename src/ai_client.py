"""
AI Client for Gemini Integration
Handles communication with Google's Gemini Flash 2.5 Pro API.
"""

import google.generativeai as genai
import time
import logging
from typing import Optional, Dict, List
import json
import asyncio
from dataclasses import dataclass

@dataclass
class CodeResponse:
    """Represents a code generation response"""
    code: str
    language: str
    explanation: str
    confidence: float
    execution_time: float
    reasoning: str  # AI's step-by-step reasoning
    problem_analysis: str  # Analysis of the problem
    approach: str  # Solution approach taken
    raw_response: str  # Complete raw response from AI

class GeminiClient:
    """Client for interacting with Gemini Flash 2.5 Pro API"""
    
    def __init__(self, api_key: str, debug_mode: bool = False):
        self.api_key = api_key
        self.debug_mode = debug_mode
        self.logger = logging.getLogger(__name__)
        
        # Configure Gemini
        genai.configure(api_key=api_key)
        
        # Use Flash 2.5 Pro model
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # Response cache to avoid redundant API calls
        self.response_cache = {}
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.5  # Minimum seconds between requests
    
    def generate_code_solution(self, problem_text: str, language: str = "python") -> Optional[CodeResponse]:
        """Generate code solution for the given problem"""
        try:
            # Check cache first
            cache_key = self._generate_cache_key(problem_text, language)
            if cache_key in self.response_cache:
                self.logger.debug("Returning cached response")
                return self.response_cache[cache_key]
            
            # Rate limiting
            self._apply_rate_limit()
            
            # Prepare prompt
            prompt = self._build_code_generation_prompt(problem_text, language)
            
            start_time = time.time()
            
            # Generate response
            response = self.model.generate_content(prompt)
            
            execution_time = time.time() - start_time
            
            # Parse response
            code_response = self._parse_code_response(response.text, language, execution_time)
            
            # Cache the response
            self.response_cache[cache_key] = code_response
            
            if self.debug_mode:
                self.logger.debug(f"Generated code solution in {execution_time:.2f}s")
                self.logger.debug(f"Code length: {len(code_response.code)} characters")
            
            return code_response
            
        except Exception as e:
            self.logger.error(f"Failed to generate code solution: {e}")
            return None
    
    def _build_code_generation_prompt(self, problem_text: str, language: str) -> str:
        """Build optimized prompt for code generation with reasoning"""
        prompt = f"""
You are an expert programmer solving coding challenges. Analyze the following problem and provide a complete, working solution with detailed reasoning.

PROBLEM:
{problem_text}

REQUIREMENTS:
1. First, analyze the problem step by step
2. Explain your approach and reasoning
3. Write clean, efficient code in {language}
4. Include proper variable names and comments
5. Handle edge cases appropriately
6. Optimize for readability and performance

RESPONSE FORMAT:
Please structure your response as follows:

ANALYSIS:
[Your step-by-step analysis of the problem]

APPROACH:
[Your solution approach and algorithm choice]

REASONING:
[Your detailed reasoning for the solution]

SOLUTION:
[Your complete code solution]

IMPORTANT: 
- Provide detailed reasoning for accuracy verification
- Use proper indentation for {language}
- Include comments explaining key parts of the solution

Please provide your complete analysis and solution:"""
        
        return prompt
    
    def _parse_code_response(self, response_text: str, language: str, execution_time: float) -> CodeResponse:
        """Parse the AI response into structured format with reasoning"""
        # Store raw response
        raw_response = response_text
        
        # Extract different sections
        analysis = self._extract_section(response_text, "ANALYSIS:")
        approach = self._extract_section(response_text, "APPROACH:")
        reasoning = self._extract_section(response_text, "REASONING:")
        solution = self._extract_section(response_text, "SOLUTION:")
        
        # Clean the code solution
        code = self._clean_code_response(solution if solution else response_text)
        
        # Extract explanation if present
        explanation = ""
        if "Explanation:" in response_text or "Note:" in response_text:
            parts = response_text.split("Explanation:")
            if len(parts) > 1:
                explanation = parts[1].strip()
            else:
                parts = response_text.split("Note:")
                if len(parts) > 1:
                    explanation = parts[1].strip()
        
        # Calculate confidence based on response quality
        confidence = self._calculate_response_confidence(code, language)
        
        return CodeResponse(
            code=code,
            language=language,
            explanation=explanation,
            confidence=confidence,
            execution_time=execution_time,
            reasoning=reasoning,
            problem_analysis=analysis,
            approach=approach,
            raw_response=raw_response
        )
    
    def _clean_code_response(self, response_text: str) -> str:
        """Clean and format the code response"""
        # Remove markdown code blocks if present
        if "```" in response_text:
            # Extract code from markdown blocks
            import re
            code_blocks = re.findall(r'```(?:\w+)?\n?(.*?)```', response_text, re.DOTALL)
            if code_blocks:
                response_text = code_blocks[0]
        
        # Remove common prefixes
        prefixes_to_remove = [
            "Here's the solution:",
            "Solution:",
            "Code:",
            "Answer:",
        ]
        
        for prefix in prefixes_to_remove:
            if response_text.strip().startswith(prefix):
                response_text = response_text.strip()[len(prefix):].strip()
        
        # Remove trailing explanations
        lines = response_text.split('\n')
        code_lines = []
        
        for line in lines:
            # Stop at explanation markers
            if any(marker in line.lower() for marker in ['explanation:', 'note:', 'time complexity:', 'space complexity:']):
                break
            code_lines.append(line)
        
        return '\n'.join(code_lines).strip()
    
    def _calculate_response_confidence(self, code: str, language: str) -> float:
        """Calculate confidence score for the generated code"""
        confidence = 1.0
        
        # Basic checks
        if len(code) < 10:
            confidence *= 0.2
        
        # Language-specific checks
        if language.lower() == "python":
            if "def " not in code and "class " not in code:
                confidence *= 0.7
            if "return" not in code:
                confidence *= 0.8
        elif language.lower() == "javascript":
            if "function" not in code and "=>" not in code:
                confidence *= 0.7
        
        # Check for proper indentation
        lines = code.split('\n')
        indented_lines = sum(1 for line in lines if line.startswith(('    ', '\t')))
        if len(lines) > 3 and indented_lines == 0:
            confidence *= 0.6
        
        return max(0.1, min(1.0, confidence))
    
    def _extract_section(self, text: str, section_name: str) -> str:
        """Extract a specific section from the response text"""
        try:
            if section_name not in text:
                return ""
            
            # Find the start of the section
            start_idx = text.find(section_name) + len(section_name)
            
            # Find the next section or end of text
            next_sections = ["ANALYSIS:", "APPROACH:", "REASONING:", "SOLUTION:"]
            end_idx = len(text)
            
            for next_section in next_sections:
                if next_section in text[start_idx:]:
                    next_idx = text.find(next_section, start_idx)
                    if next_idx < end_idx:
                        end_idx = next_idx
            
            # Extract and clean the section
            section_text = text[start_idx:end_idx].strip()
            return section_text
            
        except Exception as e:
            self.logger.error(f"Failed to extract section {section_name}: {e}")
            return ""
    
    def _generate_cache_key(self, problem_text: str, language: str) -> str:
        """Generate cache key for the request"""
        import hashlib
        content = f"{problem_text}_{language}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _apply_rate_limit(self):
        """Apply rate limiting to avoid API limits"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last_request
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def validate_api_key(self) -> bool:
        """Validate that the API key is working"""
        try:
            # Simple test request
            test_response = self.model.generate_content("Hello, respond with 'OK'")
            return "ok" in test_response.text.lower()
        except Exception as e:
            self.logger.error(f"API key validation failed: {e}")
            return False
    
    def clear_cache(self):
        """Clear the response cache"""
        self.response_cache.clear()
        self.logger.info("Response cache cleared")
    
    async def generate_code_solution_async(self, problem_text: str, language: str = "python") -> Optional[CodeResponse]:
        """Async version of code generation for better performance"""
        # For now, wrap sync method in async
        # TODO: Implement true async when Gemini supports it
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.generate_code_solution, problem_text, language)
