"""
Stealth Features - Detection Avoidance and Process Hiding
Implements features to make the application undetectable.
"""

import os
import sys
import psutil
import random
import time
import threading
from typing import List, Dict, Optional
import logging

class StealthManager:
    """Manages stealth features to avoid detection"""
    
    def __init__(self, debug_mode: bool = False):
        self.debug_mode = debug_mode
        self.logger = logging.getLogger(__name__)
        
        # Process information masking
        self.fake_process_names = [
            'system_update_helper',
            'network_monitor_service',
            'backup_sync_agent',
            'media_optimization_tool',
            'cache_cleanup_service'
        ]
        
        # Activity patterns for stealth
        self.activity_patterns = {
            'low_profile': {
                'cpu_limit': 5.0,  # Max 5% CPU usage
                'memory_limit': 100,  # Max 100MB memory
                'network_delay': (2.0, 5.0),  # Random delay between network calls
                'typing_variance': 0.4  # High variance in typing patterns
            },
            'invisible': {
                'cpu_limit': 2.0,  # Max 2% CPU usage
                'memory_limit': 50,   # Max 50MB memory
                'network_delay': (5.0, 15.0),  # Longer delays
                'typing_variance': 0.6  # Very high variance
            }
        }
        
        self.current_profile = self.activity_patterns['low_profile']
        
        # Monitoring state
        self.is_monitoring = False
        self.resource_monitor_thread = None
        
    def enable_stealth_mode(self, profile: str = 'low_profile'):
        """Enable stealth mode with specified profile"""
        if profile in self.activity_patterns:
            self.current_profile = self.activity_patterns[profile]
            self.logger.info(f"Stealth mode enabled: {profile}")
        else:
            self.logger.warning(f"Unknown stealth profile: {profile}")
    
    def start_resource_monitoring(self):
        """Start monitoring and limiting resource usage"""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        self.resource_monitor_thread = threading.Thread(
            target=self._resource_monitor_loop,
            daemon=True
        )
        self.resource_monitor_thread.start()
        self.logger.debug("Resource monitoring started")
    
    def stop_resource_monitoring(self):
        """Stop resource monitoring"""
        self.is_monitoring = False
        if self.resource_monitor_thread:
            self.resource_monitor_thread.join(timeout=2.0)
        self.logger.debug("Resource monitoring stopped")
    
    def _resource_monitor_loop(self):
        """Monitor and control resource usage"""
        process = psutil.Process()
        
        while self.is_monitoring:
            try:
                # Check CPU usage
                cpu_percent = process.cpu_percent()
                if cpu_percent > self.current_profile['cpu_limit']:
                    self._throttle_cpu_usage()
                
                # Check memory usage
                memory_mb = process.memory_info().rss / 1024 / 1024
                if memory_mb > self.current_profile['memory_limit']:
                    self._manage_memory_usage()
                
                # Sleep before next check
                time.sleep(5.0)
                
            except Exception as e:
                self.logger.error(f"Resource monitoring error: {e}")
                time.sleep(10.0)
    
    def _throttle_cpu_usage(self):
        """Throttle CPU usage when limit exceeded"""
        self.logger.debug("CPU usage limit exceeded, throttling...")
        
        # Introduce random delays to reduce CPU usage
        delay = random.uniform(0.1, 0.5)
        time.sleep(delay)
    
    def _manage_memory_usage(self):
        """Manage memory usage when limit exceeded"""
        self.logger.debug("Memory usage limit exceeded, cleaning up...")
        
        # Trigger garbage collection
        import gc
        gc.collect()
        
        # Could implement cache clearing here
        # self.ai_client.clear_cache() if available
    
    def randomize_network_timing(self) -> float:
        """Generate randomized delay for network requests"""
        min_delay, max_delay = self.current_profile['network_delay']
        return random.uniform(min_delay, max_delay)
    
    def get_typing_variance(self) -> float:
        """Get typing variance for human-like patterns"""
        return self.current_profile['typing_variance']
    
    def mask_process_info(self):
        """Attempt to mask process information"""
        try:
            # Change process title if possible (Linux/Unix)
            if hasattr(os, 'setprogname'):
                fake_name = random.choice(self.fake_process_names)
                os.setprogname(fake_name)
            
            # Set process title for ps command (if available)
            try:
                import setproctitle
                fake_name = random.choice(self.fake_process_names)
                setproctitle.setproctitle(fake_name)
                self.logger.debug(f"Process title masked as: {fake_name}")
            except ImportError:
                pass  # setproctitle not available
                
        except Exception as e:
            self.logger.error(f"Failed to mask process info: {e}")
    
    def check_detection_risks(self) -> Dict[str, bool]:
        """Check for potential detection risks"""
        risks = {
            'high_cpu_usage': False,
            'high_memory_usage': False,
            'suspicious_process_name': False,
            'frequent_api_calls': False,
            'predictable_patterns': False
        }
        
        try:
            process = psutil.Process()
            
            # Check CPU usage
            cpu_percent = process.cpu_percent()
            if cpu_percent > 10.0:  # Above 10% is suspicious for background service
                risks['high_cpu_usage'] = True
            
            # Check memory usage
            memory_mb = process.memory_info().rss / 1024 / 1024
            if memory_mb > 200:  # Above 200MB is suspicious
                risks['high_memory_usage'] = True
            
            # Check process name
            process_name = process.name().lower()
            suspicious_keywords = ['bot', 'hack', 'cheat', 'auto', 'assist']
            if any(keyword in process_name for keyword in suspicious_keywords):
                risks['suspicious_process_name'] = True
            
        except Exception as e:
            self.logger.error(f"Error checking detection risks: {e}")
        
        return risks
    
    def apply_anti_detection_measures(self):
        """Apply comprehensive anti-detection measures"""
        self.logger.info("Applying anti-detection measures...")
        
        # Mask process information
        self.mask_process_info()
        
        # Start resource monitoring
        self.start_resource_monitoring()
        
        # Randomize initial startup delay
        startup_delay = random.uniform(10.0, 60.0)
        self.logger.debug(f"Initial startup delay: {startup_delay:.1f}s")
        time.sleep(startup_delay)
    
    def simulate_normal_user_behavior(self) -> Dict[str, float]:
        """Generate parameters to simulate normal user behavior"""
        # Simulate natural variations in human behavior
        return {
            'typing_speed_multiplier': random.uniform(0.7, 1.3),
            'pause_frequency': random.uniform(0.05, 0.15),
            'error_probability': random.uniform(0.01, 0.05),
            'thinking_pause_multiplier': random.uniform(0.8, 2.0)
        }
    
    def should_skip_action(self, action_type: str) -> bool:
        """Determine if an action should be skipped for stealth"""
        # Skip actions randomly to avoid predictable patterns
        skip_probabilities = {
            'screenshot': 0.1,  # Skip 10% of screenshots
            'typing_session': 0.2,  # Skip 20% of typing opportunities
            'api_call': 0.05,  # Skip 5% of API calls
        }
        
        probability = skip_probabilities.get(action_type, 0.0)
        return random.random() < probability
    
    def generate_stealth_delay(self, base_delay: float) -> float:
        """Generate stealth-aware delay with randomization"""
        # Add significant randomization to avoid detection
        variance = self.current_profile['typing_variance']
        randomized_delay = base_delay * random.uniform(1 - variance, 1 + variance)
        
        # Add occasional longer pauses to simulate human behavior
        if random.random() < 0.1:  # 10% chance of longer pause
            randomized_delay *= random.uniform(2.0, 5.0)
        
        return max(0.01, randomized_delay)

class ProcessHider:
    """Attempts to hide the process from detection"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.original_argv = sys.argv.copy()
    
    def hide_from_process_list(self):
        """Attempt to hide from process listing tools"""
        try:
            # Modify command line arguments visible to ps
            if len(sys.argv) > 1:
                # Replace with innocuous arguments
                sys.argv[1:] = ['--background-service', '--quiet']
            
            # Change working directory to system directory
            try:
                os.chdir('/tmp')
            except:
                pass  # Fallback to current directory
            
            self.logger.debug("Applied process hiding measures")
            
        except Exception as e:
            self.logger.error(f"Failed to hide process: {e}")
    
    def restore_process_info(self):
        """Restore original process information"""
        try:
            sys.argv = self.original_argv.copy()
        except Exception as e:
            self.logger.error(f"Failed to restore process info: {e}")

class NetworkStealth:
    """Manages network traffic to avoid detection"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.request_times = []
        self.max_requests_per_minute = 10
    
    def should_delay_request(self) -> bool:
        """Check if network request should be delayed"""
        current_time = time.time()
        
        # Clean old timestamps (older than 1 minute)
        self.request_times = [t for t in self.request_times 
                            if current_time - t < 60.0]
        
        # Check if we're approaching rate limit
        return len(self.request_times) >= self.max_requests_per_minute
    
    def record_request(self):
        """Record a network request"""
        self.request_times.append(time.time())
    
    def get_stealth_delay(self) -> float:
        """Get delay for network stealth"""
        if self.should_delay_request():
            # Longer delay when approaching rate limit
            return random.uniform(10.0, 30.0)
        else:
            # Normal stealth delay
            return random.uniform(1.0, 5.0)
