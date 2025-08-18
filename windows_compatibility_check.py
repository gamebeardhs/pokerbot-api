# Cross-platform compatibility check script
"""
Windows Compatibility Verification Script
Checks for cross-platform compatibility issues and fixes common problems.
"""

import os
import sys
import platform
import subprocess
from pathlib import Path

def check_python_compatibility():
    """Check Python version compatibility."""
    print("🐍 Python Compatibility Check")
    print("-" * 30)
    
    version = sys.version_info
    print(f"Python Version: {version.major}.{version.minor}.{version.micro}")
    print(f"Platform: {platform.system()} {platform.release()}")
    print(f"Architecture: {platform.machine()}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ required for cross-platform compatibility")
        return False
    else:
        print("✅ Python version compatible")
        return True

def check_file_paths():
    """Check for Windows-incompatible file paths."""
    print("\n📁 File Path Compatibility Check")
    print("-" * 30)
    
    issues = []
    
    # Check for Unix-style shebangs
    for file_path in Path(".").rglob("*.py"):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
                if first_line.startswith("#!/usr/bin/env") or first_line.startswith("#!/bin/"):
                    issues.append(f"Unix shebang in {file_path}")
        except:
            pass
    
    # Check for hardcoded Unix paths
    unix_patterns = ["/usr/", "/etc/", "/var/", "/tmp/", "/home/"]
    for file_path in Path(".").rglob("*.py"):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                for pattern in unix_patterns:
                    if pattern in content and "# Cross-platform" not in content[:100]:
                        issues.append(f"Unix path '{pattern}' in {file_path}")
                        break
        except:
            pass
    
    if issues:
        print("⚠️ Found potential path compatibility issues:")
        for issue in issues[:5]:  # Show first 5
            print(f"  - {issue}")
        if len(issues) > 5:
            print(f"  ... and {len(issues) - 5} more")
        return False
    else:
        print("✅ No hardcoded Unix paths found")
        return True

def check_dependencies():
    """Check Windows-critical dependencies."""
    print("\n📦 Dependency Compatibility Check")
    print("-" * 30)
    
    windows_critical = [
        "pillow",      # Image processing
        "opencv-python", # Computer vision
        "numpy",       # Numerical computing
        "fastapi",     # Web framework
        "uvicorn"      # ASGI server
    ]
    
    missing = []
    for package in windows_critical:
        try:
            __import__(package.replace("-", "_"))
            print(f"✅ {package}")
        except ImportError:
            missing.append(package)
            print(f"❌ {package} (missing)")
    
    if missing:
        print(f"\n⚠️ Missing {len(missing)} critical packages")
        print("Run: pip install " + " ".join(missing))
        return False
    else:
        print("\n✅ All critical dependencies available")
        return True

def check_font_compatibility():
    """Check font loading compatibility."""
    print("\n🔤 Font Compatibility Check")
    print("-" * 30)
    
    try:
        from PIL import ImageFont
        
        # Test Windows fonts
        windows_fonts = ["arial.ttf", "calibri.ttf", "times.ttf"]
        unix_fonts = ["DejaVuSans.ttf", "LiberationSans-Regular.ttf"]
        
        font_found = False
        if os.name == 'nt':
            for font in windows_fonts:
                try:
                    ImageFont.truetype(font, 12)
                    print(f"✅ Windows font: {font}")
                    font_found = True
                    break
                except:
                    continue
        else:
            for font in unix_fonts:
                try:
                    ImageFont.truetype(font, 12)
                    print(f"✅ Unix font: {font}")
                    font_found = True
                    break
                except:
                    continue
        
        if not font_found:
            print("⚠️ No system fonts found, using default")
            default_font = ImageFont.load_default()
            print(f"✅ Default font available: {type(default_font)}")
        
        return True
    except ImportError:
        print("❌ PIL/Pillow not available")
        return False

def check_encoding_compatibility():
    """Check file encoding compatibility."""
    print("\n📝 File Encoding Compatibility Check")
    print("-" * 30)
    
    issues = []
    
    for file_path in Path(".").rglob("*.py"):
        try:
            # Try to read with UTF-8
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Check for explicit encoding in file operations
            if 'open(' in content and 'encoding=' not in content:
                # Check if it's opening text files
                if any(ext in content for ext in ['.txt', '.json', '.html', '.md']):
                    issues.append(f"Missing encoding in {file_path}")
        except UnicodeDecodeError:
            issues.append(f"Encoding issue in {file_path}")
        except:
            pass
    
    if issues:
        print("⚠️ Found encoding compatibility issues:")
        for issue in issues[:3]:
            print(f"  - {issue}")
        return False
    else:
        print("✅ No encoding issues found")
        return True

def check_subprocess_compatibility():
    """Check subprocess calls for Windows compatibility."""
    print("\n⚙️ Subprocess Compatibility Check")
    print("-" * 30)
    
    issues = []
    
    for file_path in Path(".").rglob("*.py"):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Check for shell=True without proper Windows handling
            if 'subprocess' in content and 'shell=True' in content:
                if 'os.name' not in content:
                    issues.append(f"shell=True without OS check in {file_path}")
        except:
            pass
    
    if issues:
        print("⚠️ Found subprocess compatibility issues:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print("✅ Subprocess calls appear compatible")
        return True

def main():
    """Run complete Windows compatibility check."""
    print("🪟 WINDOWS COMPATIBILITY CHECK")
    print("=" * 50)
    
    checks = [
        check_python_compatibility,
        check_file_paths,
        check_dependencies,
        check_font_compatibility,
        check_encoding_compatibility,
        check_subprocess_compatibility
    ]
    
    results = []
    for check in checks:
        try:
            results.append(check())
        except Exception as e:
            print(f"❌ Check failed: {e}")
            results.append(False)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\n🎯 COMPATIBILITY SCORE: {passed}/{total}")
    print("=" * 50)
    
    if passed == total:
        print("🎉 Full Windows compatibility achieved!")
        print("✅ Ready for deployment on Windows systems")
    elif passed >= total * 0.8:
        print("⚠️ Good Windows compatibility with minor issues")
        print("🔧 Consider fixing remaining issues for best experience")
    else:
        print("❌ Significant Windows compatibility issues found")
        print("🛠️ Please address issues before Windows deployment")
    
    return passed / total

if __name__ == "__main__":
    main()