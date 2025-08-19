"""
Region utilities for percentage-based calibration.
Converts between relative (percentage) and absolute (pixel) coordinates.
"""

from typing import Dict, Tuple, Any
import logging

logger = logging.getLogger(__name__)

def abs_from_rel(rel_box: Tuple[float, float, float, float], 
                 client_w: int, client_h: int, 
                 client_x: int = 0, client_y: int = 0) -> Dict[str, int]:
    """Convert relative coordinates to absolute monitor coordinates.
    
    Args:
        rel_box: (rx, ry, rw, rh) as fractions 0.0-1.0
        client_w, client_h: ACR client window dimensions
        client_x, client_y: ACR client window screen position
    
    Returns:
        Dict with 'left', 'top', 'width', 'height' for MSS capture
    """
    rx, ry, rw, rh = rel_box
    
    return {
        "left": int(client_x + rx * client_w),
        "top": int(client_y + ry * client_h),
        "width": int(rw * client_w),
        "height": int(rh * client_h),
    }

def rel_from_abs(abs_coords: Tuple[int, int, int, int], 
                 client_w: int, client_h: int, 
                 client_x: int = 0, client_y: int = 0) -> Tuple[float, float, float, float]:
    """Convert absolute coordinates to relative percentages.
    
    Args:
        abs_coords: (x, y, width, height) absolute pixels
        client_w, client_h: ACR client window dimensions
        client_x, client_y: ACR client window screen position
    
    Returns:
        (rx, ry, rw, rh) as fractions 0.0-1.0
    """
    x, y, w, h = abs_coords
    
    # Convert to relative to client area
    rx = (x - client_x) / client_w if client_w > 0 else 0.0
    ry = (y - client_y) / client_h if client_h > 0 else 0.0
    rw = w / client_w if client_w > 0 else 0.0
    rh = h / client_h if client_h > 0 else 0.0
    
    return (rx, ry, rw, rh)

# Standard ACR regions as percentages (tuned for common ACR layouts)
DEFAULT_ACR_REGIONS = {
    "pot": (0.43, 0.38, 0.14, 0.06),           # Center pot area
    "hero_stack": (0.46, 0.82, 0.12, 0.07),   # Bottom center stack
    "board": (0.30, 0.30, 0.40, 0.12),        # Community cards area
    "hero_cards": (0.36, 0.72, 0.28, 0.10),   # Hero's cards
    "buttons": (0.35, 0.88, 0.30, 0.10),      # Action buttons
    "hero_timer_arc": (0.48, 0.86, 0.04, 0.04), # Timer indicator
    "villain_1_name": (0.20, 0.15, 0.15, 0.05),  # Top left player
    "villain_1_stack": (0.20, 0.20, 0.15, 0.05),
    "villain_2_name": (0.65, 0.15, 0.15, 0.05),  # Top right player  
    "villain_2_stack": (0.65, 0.20, 0.15, 0.05),
}

def validate_relative_regions(regions: Dict[str, Tuple[float, float, float, float]]) -> bool:
    """Validate that relative regions are within bounds."""
    for name, (rx, ry, rw, rh) in regions.items():
        if not (0.0 <= rx <= 1.0 and 0.0 <= ry <= 1.0 and 
                0.0 <= rw <= 1.0 and 0.0 <= rh <= 1.0):
            logger.error(f"Invalid region {name}: {(rx, ry, rw, rh)} - values must be 0.0-1.0")
            return False
        if rx + rw > 1.0 or ry + rh > 1.0:
            logger.error(f"Invalid region {name}: extends beyond window bounds")
            return False
    return True