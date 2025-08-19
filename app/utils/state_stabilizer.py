"""
State stabilization and FPS jitter for poker table reading.
Ensures stable, consistent readings before emitting state changes.
"""

import time
import random
import logging
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict

logger = logging.getLogger(__name__)

class StateStabilizer:
    """Debounces OCR readings to ensure stability before emitting changes."""
    
    def __init__(self, required_matches: int = 2):
        """Initialize stabilizer.
        
        Args:
            required_matches: Number of consecutive identical readings required
        """
        self.required_matches = required_matches
        self.history: Dict[str, List[Any]] = defaultdict(list)
        self.last_stable: Dict[str, Any] = {}
        
    def is_stable(self, key: str, value: Any) -> bool:
        """Check if a value is stable (consistent across required readings).
        
        Args:
            key: Identifier for the value being tracked
            value: Current reading
            
        Returns:
            True if value is stable, False otherwise
        """
        # Add current value to history
        history = self.history[key]
        history.append(value)
        
        # Keep only recent history
        if len(history) > self.required_matches:
            history.pop(0)
        
        # Check if we have enough readings and they're all identical
        if len(history) == self.required_matches:
            is_stable = all(v == value for v in history)
            if is_stable:
                self.last_stable[key] = value
            return is_stable
            
        return False
    
    def get_stable_value(self, key: str) -> Optional[Any]:
        """Get the last stable value for a key."""
        return self.last_stable.get(key)
    
    def force_unstable(self, key: str):
        """Force a key to be considered unstable (clear history)."""
        if key in self.history:
            self.history[key].clear()
    
    def clear_all(self):
        """Clear all history and stable values."""
        self.history.clear()
        self.last_stable.clear()
    
    def get_status(self) -> Dict[str, Any]:
        """Get stabilizer status for debugging."""
        return {
            "tracking_keys": list(self.history.keys()),
            "stable_keys": list(self.last_stable.keys()),
            "required_matches": self.required_matches,
            "history_lengths": {k: len(v) for k, v in self.history.items()}
        }

class FPSJitter:
    """Adds random jitter to prevent detection by anti-bot systems."""
    
    def __init__(self, base_delay: float = 0.3, jitter_range: Tuple[float, float] = (0.18, 0.42)):
        """Initialize FPS jitter.
        
        Args:
            base_delay: Base delay between readings (seconds)
            jitter_range: (min, max) additional random delay
        """
        self.base_delay = base_delay
        self.jitter_min, self.jitter_max = jitter_range
        self.last_sleep = 0
        
    def sleep_with_jitter(self):
        """Sleep with randomized timing to avoid detection patterns."""
        # Add random jitter to base delay
        jitter = random.uniform(self.jitter_min, self.jitter_max)
        sleep_time = self.base_delay + jitter
        
        logger.debug(f"FPS jitter sleep: {sleep_time:.3f}s")
        time.sleep(sleep_time)
        self.last_sleep = sleep_time
        
    def get_effective_fps(self) -> float:
        """Get approximate FPS based on current timing."""
        if self.last_sleep > 0:
            return 1.0 / self.last_sleep
        return 1.0 / (self.base_delay + (self.jitter_min + self.jitter_max) / 2)

class ConfidenceGate:
    """Gates OCR results based on confidence thresholds."""
    
    def __init__(self, default_threshold: float = 0.6):
        """Initialize confidence gate.
        
        Args:
            default_threshold: Default confidence threshold (0.0-1.0)
        """
        self.default_threshold = default_threshold
        self.field_thresholds = {
            "money": 0.7,    # Higher threshold for critical financial data
            "stack": 0.7,    
            "buttons": 0.5,  # Lower threshold for action detection
            "name": 0.4,     # Lower threshold for player names
            "timer": 0.5,
        }
        
    def should_accept(self, confidence: float, field_type: str = "general") -> bool:
        """Check if confidence meets threshold for field type."""
        threshold = self.field_thresholds.get(field_type, self.default_threshold)
        return confidence >= threshold
    
    def filter_results(self, results: Dict[str, Dict[str, Any]]) -> Dict[str, str]:
        """Filter OCR results based on confidence thresholds."""
        filtered = {}
        
        for field_name, result in results.items():
            if isinstance(result, dict) and 'text' in result and 'confidence' in result:
                field_type = result.get('field_type', 'general')
                if self.should_accept(result['confidence'], field_type):
                    filtered[field_name] = result['text']
                else:
                    logger.debug(f"Filtered low confidence result for {field_name}: {result['confidence']:.2f}")
            else:
                # Handle non-dict results (backward compatibility)
                filtered[field_name] = str(result)
                
        return filtered

# Global instances
stabilizer = StateStabilizer(required_matches=2)
fps_jitter = FPSJitter(base_delay=0.3, jitter_range=(0.18, 0.42))  
confidence_gate = ConfidenceGate(default_threshold=0.6)