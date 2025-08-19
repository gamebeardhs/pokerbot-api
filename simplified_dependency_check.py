#!/usr/bin/env python3
"""
Simple dependency checker for poker advisory system.
Avoids GUI dependencies that cause issues in headless environments.
"""

import sys
import subprocess
import importlib
from typing import Dict, List, Tuple, Optional

def check_package_installed(package_name: str) -> Tuple[bool, Optional[str]]:
    """Check if a package is installed and return version."""
    try:
        # Skip packages that require X11/GUI in headless environments
        if package_name in ['pyautogui', 'mss']:
            try:
                # Try importing without initializing GUI components
                if package_name == 'pyautogui':
                    import pyautogui._pyautogui_x11 as test_module
                elif package_name == 'mss':
                    import mss.base as test_module
                return True, "installed"
            except ImportError:
                return False, None
            except Exception:
                # Package exists but can't initialize in headless environment
                return True, "installed (no GUI)"
        
        module = importlib.import_module(package_name.replace('-', '_'))
        version = getattr(module, '__version__', 'unknown')
        return True, version
    except ImportError:
        return False, None

def check_system_requirements() -> Dict[str, any]:
    """Check system-level requirements."""
    results = {
        'python_version': sys.version,
        'python_compatible': sys.version_info >= (3, 8),
        'platform': sys.platform
    }
    
    # Check for Tesseract OCR
    try:
        result = subprocess.run(['tesseract', '--version'], 
                              capture_output=True, text=True, timeout=5)
        results['tesseract_available'] = result.returncode == 0
        if results['tesseract_available']:
            version_line = result.stdout.split('\n')[0]
            results['tesseract_version'] = version_line
    except (subprocess.TimeoutExpired, FileNotFoundError):
        results['tesseract_available'] = False
        results['tesseract_version'] = None
    
    return results

def main():
    """Main dependency check function."""
    print("🔍 POKER ADVISORY SYSTEM - DEPENDENCY STATUS")
    print("=" * 60)
    
    # System requirements
    sys_info = check_system_requirements()
    print(f"\n📋 SYSTEM STATUS:")
    print(f"   Python Version: {sys_info['python_version'].split()[0]}")
    print(f"   Python Compatible: {'✅' if sys_info['python_compatible'] else '❌'}")
    print(f"   Platform: {sys_info['platform']}")
    print(f"   Tesseract OCR: {'✅' if sys_info['tesseract_available'] else '❌'}")
    
    # Core packages
    core_packages = [
        'fastapi', 'uvicorn', 'pydantic', 'requests', 'websockets'
    ]
    
    print(f"\n📦 CORE DEPENDENCIES:")
    core_installed = 0
    for pkg in core_packages:
        is_installed, version = check_package_installed(pkg)
        status = "✅" if is_installed else "❌"
        version_info = f"v{version}" if is_installed else "not installed"
        print(f"   {status} {pkg}: {version_info}")
        if is_installed:
            core_installed += 1
    
    # Vision packages
    vision_packages = [
        'opencv-python', 'pillow', 'numpy', 'pytesseract', 'imagehash'
    ]
    
    print(f"\n📷 COMPUTER VISION:")
    vision_installed = 0
    for pkg in vision_packages:
        is_installed, version = check_package_installed(pkg)
        status = "✅" if is_installed else "❌"
        version_info = f"v{version}" if is_installed else "not installed"
        print(f"   {status} {pkg}: {version_info}")
        if is_installed:
            vision_installed += 1
    
    # Optional packages
    optional_packages = [
        ('easyocr', 'Enhanced OCR'),
        ('scikit-learn', 'Machine Learning'),
        ('pandas', 'Data Processing'),
        ('open_spiel', 'Game Theory'),
        ('trafilatura', 'Web Scraping')
    ]
    
    print(f"\n🔧 OPTIONAL FEATURES:")
    for pkg, desc in optional_packages:
        is_installed, version = check_package_installed(pkg)
        status = "✅" if is_installed else "⚪"
        version_info = f"v{version}" if is_installed else "not installed"
        print(f"   {status} {pkg} ({desc}): {version_info}")
    
    # Summary
    total_core = len(core_packages)
    total_vision = len(vision_packages)
    core_percent = (core_installed / total_core) * 100
    vision_percent = (vision_installed / total_vision) * 100
    
    print(f"\n📊 SUMMARY:")
    print(f"   Core Dependencies: {core_installed}/{total_core} ({core_percent:.0f}%)")
    print(f"   Vision Dependencies: {vision_installed}/{total_vision} ({vision_percent:.0f}%)")
    
    if core_installed == total_core and vision_installed == total_vision:
        print(f"\n🚀 STATUS: SYSTEM READY FOR DEPLOYMENT")
    else:
        print(f"\n⚠️  STATUS: MISSING DEPENDENCIES")
        missing = []
        for pkg in core_packages:
            is_installed, _ = check_package_installed(pkg)
            if not is_installed:
                missing.append(pkg)
        for pkg in vision_packages:
            is_installed, _ = check_package_installed(pkg)
            if not is_installed:
                missing.append(pkg)
        
        if missing:
            print(f"   Missing: {', '.join(missing)}")
            print(f"   Install: pip install {' '.join(missing)}")

if __name__ == "__main__":
    main()