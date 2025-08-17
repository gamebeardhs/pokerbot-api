"""
Anti-detection stealth system for poker bot operation.
Implements professional bot evasion techniques.
"""

import time
import random
import threading
from typing import Dict, List, Tuple
import logging
import os
import psutil
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class StealthConfig:
    """Configuration for stealth operations."""
    min_action_delay: float = 0.8  # Minimum seconds between actions
    max_action_delay: float = 3.2  # Maximum seconds between actions
    thinking_time_base: float = 1.5  # Base thinking time
    thinking_time_variance: float = 0.8  # Variance in thinking time
    mouse_jitter_enabled: bool = True
    process_masking_enabled: bool = True
    timing_randomization: bool = True

class HumanBehaviorSimulator:
    """Simulates human-like behavior patterns."""
    
    def __init__(self, config: StealthConfig = StealthConfig()):
        self.config = config
        self.last_action_time = 0
        self.action_history = []
        self.session_start = time.time()
        
    def calculate_action_delay(self, action_type: str, pot_size: float = 0) -> float:
        """Calculate human-like delay before action."""
        base_delay = self.config.min_action_delay
        
        # Adjust delay based on action complexity
        if action_type in ['fold']:
            delay_factor = 0.7  # Quick folds
        elif action_type in ['check', 'call']:
            delay_factor = 1.0  # Normal speed
        elif action_type in ['bet', 'raise']:
            delay_factor = 1.5  # More thinking for aggressive actions
        else:
            delay_factor = 1.0
        
        # Pot size consideration (bigger pots = more thinking)
        pot_factor = min(1.5, 1.0 + (pot_size / 100.0) * 0.1)
        
        # Random variance
        variance = random.uniform(-self.config.thinking_time_variance, 
                                 self.config.thinking_time_variance)
        
        total_delay = (base_delay * delay_factor * pot_factor) + variance
        
        # Ensure within bounds
        return max(self.config.min_action_delay, 
                  min(self.config.max_action_delay, total_delay))
    
    def add_session_variance(self, base_delay: float) -> float:
        """Add session-based variance to appear more human."""
        session_time = time.time() - self.session_start
        
        # Fatigue factor (slower after long sessions)
        if session_time > 3600:  # After 1 hour
            fatigue_factor = 1.1 + (session_time - 3600) / 7200  # Slower after 2+ hours
            base_delay *= min(1.3, fatigue_factor)
        
        # Recent action clustering (avoid too many quick actions)
        recent_actions = [a for a in self.action_history if time.time() - a < 30]
        if len(recent_actions) > 5:  # Many recent actions
            base_delay *= 1.2
        
        return base_delay
    
    def wait_for_action(self, action_type: str, pot_size: float = 0):
        """Wait appropriate time before taking action."""
        current_time = time.time()
        
        # Calculate base delay
        delay = self.calculate_action_delay(action_type, pot_size)
        
        # Add session variance
        delay = self.add_session_variance(delay)
        
        # Ensure minimum time between actions
        time_since_last = current_time - self.last_action_time
        if time_since_last < self.config.min_action_delay:
            additional_delay = self.config.min_action_delay - time_since_last
            delay += additional_delay
        
        # Record action timing
        self.action_history.append(current_time)
        self.last_action_time = current_time
        
        # Keep only recent history
        self.action_history = [t for t in self.action_history if current_time - t < 300]
        
        logger.debug(f"Waiting {delay:.2f}s before {action_type} action")
        time.sleep(delay)

class ProcessStealth:
    """Handle process-level stealth operations."""
    
    def __init__(self):
        self.original_process_name = None
        self.stealth_enabled = False
        
    def enable_stealth_mode(self):
        """Enable process stealth features."""
        try:
            # Change process title to appear innocent
            innocent_names = [
                "Calculator",
                "Notepad", 
                "System Monitor",
                "Task Manager",
                "Windows Update"
            ]
            
            stealth_name = random.choice(innocent_names)
            
            # Platform-specific process name changing
            if os.name == 'nt':  # Windows
                try:
                    import ctypes
                    ctypes.windll.kernel32.SetConsoleTitleW(stealth_name)
                except:
                    pass
            
            self.stealth_enabled = True
            logger.info(f"Stealth mode enabled: {stealth_name}")
            
        except Exception as e:
            logger.warning(f"Failed to enable process stealth: {e}")
    
    def disable_stealth_mode(self):
        """Disable stealth mode and restore normal operation."""
        if self.original_process_name:
            try:
                if os.name == 'nt':
                    import ctypes
                    ctypes.windll.kernel32.SetConsoleTitleW(self.original_process_name)
            except:
                pass
        
        self.stealth_enabled = False
        logger.info("Stealth mode disabled")

class ClickPatternRandomizer:
    """Randomize mouse click patterns to appear human."""
    
    def __init__(self):
        self.click_history = []
        
    def get_human_click_offset(self, region_center: Tuple[int, int], 
                              region_size: Tuple[int, int]) -> Tuple[int, int]:
        """
        Generate human-like click offset within a region.
        Avoids always clicking exact center.
        """
        center_x, center_y = region_center
        width, height = region_size
        
        # Human clicks tend to be slightly off-center
        # Gaussian distribution around center with 30% of region as std dev
        offset_x = random.gauss(0, width * 0.15)
        offset_y = random.gauss(0, height * 0.15)
        
        # Clamp to region bounds
        max_offset_x = width // 3
        max_offset_y = height // 3
        
        offset_x = max(-max_offset_x, min(max_offset_x, offset_x))
        offset_y = max(-max_offset_y, min(max_offset_y, offset_y))
        
        final_x = int(center_x + offset_x)
        final_y = int(center_y + offset_y)
        
        # Record click pattern
        self.click_history.append((final_x, final_y, time.time()))
        
        # Keep only recent clicks
        self.click_history = [c for c in self.click_history if time.time() - c[2] < 60]
        
        return final_x, final_y
    
    def simulate_mouse_movement(self, start: Tuple[int, int], 
                               end: Tuple[int, int]) -> List[Tuple[int, int]]:
        """
        Generate natural mouse movement path between two points.
        Includes slight curves and speed variations.
        """
        start_x, start_y = start
        end_x, end_y = end
        
        # Calculate path
        distance = ((end_x - start_x)**2 + (end_y - start_y)**2)**0.5
        
        if distance < 50:  # Short movements are more direct
            return [start, end]
        
        # Generate curved path with control points
        steps = max(5, int(distance / 20))
        path_points = []
        
        for i in range(steps + 1):
            t = i / steps
            
            # Bezier curve with slight randomness
            curve_offset = random.gauss(0, distance * 0.05)
            
            # Linear interpolation with curve
            x = start_x + t * (end_x - start_x) + curve_offset * (1 - 2*abs(t - 0.5))
            y = start_y + t * (end_y - start_y) + curve_offset * (1 - 2*abs(t - 0.5))
            
            path_points.append((int(x), int(y)))
        
        return path_points

class StealthManager:
    """Main stealth manager coordinating all anti-detection measures."""
    
    def __init__(self, config: StealthConfig = StealthConfig()):
        self.config = config
        self.behavior_sim = HumanBehaviorSimulator(config)
        self.process_stealth = ProcessStealth()
        self.click_randomizer = ClickPatternRandomizer()
        self.monitoring_enabled = False
        
    def enable_stealth(self):
        """Enable all stealth measures."""
        if self.config.process_masking_enabled:
            self.process_stealth.enable_stealth_mode()
        
        self.monitoring_enabled = True
        logger.info("Stealth manager enabled")
    
    def disable_stealth(self):
        """Disable all stealth measures."""
        self.process_stealth.disable_stealth_mode()
        self.monitoring_enabled = False
        logger.info("Stealth manager disabled")
    
    def wait_before_action(self, action_type: str, pot_size: float = 0):
        """Wait appropriate time before poker action."""
        if self.config.timing_randomization:
            self.behavior_sim.wait_for_action(action_type, pot_size)
    
    def get_human_click_position(self, region_bounds: Tuple[int, int, int, int]) -> Tuple[int, int]:
        """Get human-like click position for region."""
        x, y, w, h = region_bounds
        center = (x + w//2, y + h//2)
        size = (w, h)
        
        if self.config.mouse_jitter_enabled:
            return self.click_randomizer.get_human_click_offset(center, size)
        else:
            return center
    
    def simulate_thinking(self, complexity_factor: float = 1.0):
        """Simulate human thinking time."""
        if self.config.timing_randomization:
            thinking_time = self.config.thinking_time_base * complexity_factor
            variance = random.uniform(-0.3, 0.3) * thinking_time
            total_time = max(0.5, thinking_time + variance)
            
            logger.debug(f"Simulating thinking for {total_time:.2f}s")
            time.sleep(total_time)
    
    def get_stealth_stats(self) -> Dict:
        """Get current stealth status and statistics."""
        return {
            "stealth_enabled": self.monitoring_enabled,
            "process_masked": self.process_stealth.stealth_enabled,
            "actions_recorded": len(self.behavior_sim.action_history),
            "clicks_recorded": len(self.click_randomizer.click_history),
            "session_time": time.time() - self.behavior_sim.session_start
        }

# Global stealth manager
stealth_manager = StealthManager()

def enable_stealth_mode(config: StealthConfig = StealthConfig()):
    """Enable global stealth mode."""
    global stealth_manager
    stealth_manager = StealthManager(config)
    stealth_manager.enable_stealth()

def disable_stealth_mode():
    """Disable global stealth mode."""
    stealth_manager.disable_stealth()

def wait_human_like(action_type: str, pot_size: float = 0):
    """Wait human-like time before action."""
    stealth_manager.wait_before_action(action_type, pot_size)