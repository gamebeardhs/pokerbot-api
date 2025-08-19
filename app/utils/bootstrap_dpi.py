"""
DPI awareness bootstrap for Windows compatibility.
Must be called early in application startup before any window operations.
"""

import sys
import logging

logger = logging.getLogger(__name__)

def make_dpi_aware():
    """Enable DPI awareness for Windows to prevent coordinate misalignment.
    
    This prevents issues where Windows scaling (125%, 150%, etc.) causes
    coordinate drift between Win32 APIs and actual screen pixels.
    """
    try:
        if sys.platform.startswith("win"):
            import ctypes
            
            # Try Per-Monitor v2 DPI awareness (Windows 10 v1703+)
            try:
                ctypes.windll.shcore.SetProcessDpiAwareness(2)
                logger.info("DPI awareness enabled: Per-Monitor v2")
                return True
            except (AttributeError, OSError):
                # Fallback to system DPI awareness
                try:
                    ctypes.windll.user32.SetProcessDPIAware()
                    logger.info("DPI awareness enabled: System DPI aware")
                    return True
                except (AttributeError, OSError):
                    logger.warning("Could not enable DPI awareness")
                    return False
        else:
            logger.debug("DPI awareness not needed on non-Windows platform")
            return True
            
    except Exception as e:
        logger.warning(f"DPI awareness setup failed: {e}")
        return False

def get_dpi_scaling():
    """Get current DPI scaling factor for Windows."""
    try:
        if sys.platform.startswith("win"):
            import ctypes
            from ctypes import wintypes
            
            # Get system DPI
            user32 = ctypes.windll.user32
            dc = user32.GetDC(0)
            gdi32 = ctypes.windll.gdi32
            dpi = gdi32.GetDeviceCaps(dc, 88)  # LOGPIXELSX
            user32.ReleaseDC(0, dc)
            
            scaling = dpi / 96.0  # 96 DPI = 100% scaling
            logger.debug(f"DPI scaling detected: {scaling:.2f}x ({dpi} DPI)")
            return scaling
        else:
            return 1.0
            
    except Exception as e:
        logger.warning(f"Could not detect DPI scaling: {e}")
        return 1.0