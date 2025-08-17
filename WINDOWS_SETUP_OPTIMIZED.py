#!/usr/bin/env python3
"""
Windows-Optimized Poker Advisory App Setup
Handles Windows-specific installation, dependencies, and startup.
"""

import os
import sys
import subprocess
import webbrowser
import time
import platform
import winreg
from pathlib import Path
import zipfile
import shutil

class WindowsPokerSetup:
    """Windows-optimized setup and configuration."""
    
    def __init__(self):
        self.is_windows = platform.system() == "Windows"
        self.script_dir = Path(__file__).parent
        self.requirements_checked = False
        
    def check_windows_requirements(self):
        """Check Windows-specific requirements."""
        print("🪟 Windows Environment Check")
        print("-" * 30)
        
        checks = []
        
        # Check Windows version
        try:
            version = sys.getwindowsversion()
            if version.major >= 10:
                checks.append("✅ Windows 10/11 detected")
            else:
                checks.append("⚠️ Windows 7/8 (compatibility mode)")
        except:
            checks.append("⚠️ Windows version unknown")
        
        # Check Python installation
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        if sys.version_info >= (3, 8):
            checks.append(f"✅ Python {python_version}")
        else:
            checks.append(f"❌ Python {python_version} (need 3.8+)")
        
        # Check pip
        try:
            import pip
            checks.append("✅ pip available")
        except ImportError:
            checks.append("❌ pip not found")
        
        # Check Visual C++ Redistributable (needed for some packages)
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                               r"SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64")
            checks.append("✅ Visual C++ Redistributable")
            winreg.CloseKey(key)
        except:
            checks.append("⚠️ Visual C++ Redistributable (may be needed)")
        
        for check in checks:
            print(f"  {check}")
        
        self.requirements_checked = True
        return True
    
    def install_windows_dependencies(self):
        """Install Windows-optimized dependencies."""
        print("\n📦 Installing Windows Dependencies")
        print("-" * 35)
        
        # Windows-specific package order (avoid conflicts)
        windows_packages = [
            # Core Python packages first
            "setuptools>=65.0.0",
            "wheel>=0.37.0",
            "pip>=22.0.0",
            
            # FastAPI and server
            "fastapi>=0.100.0",
            "uvicorn[standard]>=0.23.0", 
            "pydantic>=2.0.0",
            "python-multipart>=0.0.6",
            
            # Image processing (order matters on Windows)
            "numpy>=1.21.0",  # Must be first for OpenCV
            "Pillow>=9.0.0",
            "opencv-python>=4.7.0.72",
            
            # Data processing
            "pandas>=1.5.0",
            "requests>=2.28.0",
            
            # Optional: Tesseract OCR (requires system install)
            # Will skip if tesseract not installed
        ]
        
        success_count = 0
        
        for package in windows_packages:
            try:
                print(f"📦 Installing {package}...")
                result = subprocess.run([
                    sys.executable, "-m", "pip", "install", 
                    "--upgrade", "--prefer-binary", package
                ], capture_output=True, text=True, timeout=300)
                
                if result.returncode == 0:
                    print(f"✅ {package}")
                    success_count += 1
                else:
                    print(f"⚠️ {package} (skipped)")
                    
            except subprocess.TimeoutExpired:
                print(f"⏰ {package} (timeout, skipped)")
            except Exception as e:
                print(f"❌ {package} (error: {e})")
        
        # Try to install pytesseract if tesseract is available
        try:
            # Check if tesseract is in PATH
            subprocess.run(["tesseract", "--version"], 
                         capture_output=True, check=True)
            
            subprocess.run([sys.executable, "-m", "pip", "install", "pytesseract"], 
                         capture_output=True, check=True)
            print("✅ pytesseract (tesseract found)")
        except:
            print("⚠️ pytesseract skipped (tesseract not found)")
            print("   Install Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki")
        
        print(f"\n📊 Installed {success_count}/{len(windows_packages)} packages")
        return success_count > len(windows_packages) * 0.7  # 70% success rate
    
    def create_windows_shortcuts(self):
        """Create Windows desktop shortcuts."""
        print("\n🔗 Creating Windows Shortcuts")
        print("-" * 30)
        
        try:
            import winshell
            from win32com.client import Dispatch
            
            desktop = winshell.desktop()
            
            # Create desktop shortcut
            path = os.path.join(desktop, "Poker Advisory App.lnk")
            target = str(self.script_dir / "start_app.py")
            wDir = str(self.script_dir)
            icon = target
            
            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(path)
            shortcut.Targetpath = sys.executable
            shortcut.Arguments = f'"{target}"'
            shortcut.WorkingDirectory = wDir
            shortcut.IconLocation = icon
            shortcut.save()
            
            print("✅ Desktop shortcut created")
            
        except ImportError:
            # Fallback: Create batch file
            batch_content = f"""@echo off
cd /d "{self.script_dir}"
"{sys.executable}" start_app.py
pause
"""
            batch_path = self.script_dir / "Start Poker App.bat"
            batch_path.write_text(batch_content)
            print("✅ Batch file created (Start Poker App.bat)")
            
        except Exception as e:
            print(f"⚠️ Shortcut creation failed: {e}")
    
    def configure_windows_firewall(self):
        """Configure Windows Firewall for the app."""
        print("\n🛡️ Windows Firewall Configuration")
        print("-" * 35)
        
        try:
            # Add firewall rule for Python (if not exists)
            cmd = [
                "netsh", "advfirewall", "firewall", "add", "rule",
                "name=Poker Advisory App",
                "dir=in", "action=allow", "protocol=TCP", "localport=5000",
                "program=" + sys.executable
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Firewall rule added for port 5000")
            else:
                print("⚠️ Firewall rule failed (may need admin)")
                
        except Exception as e:
            print(f"⚠️ Firewall configuration failed: {e}")
            print("   You may need to manually allow Python through Windows Firewall")
    
    def check_screenshot_permissions(self):
        """Check Windows screenshot permissions."""
        print("\n📸 Screenshot Permissions Check")
        print("-" * 32)
        
        try:
            # Test screenshot capability
            import PIL.ImageGrab as ImageGrab
            screenshot = ImageGrab.grab(bbox=(0, 0, 100, 100))
            
            if screenshot and screenshot.size == (100, 100):
                print("✅ Screenshot permissions working")
                return True
            else:
                print("❌ Screenshot failed - check permissions")
                print("   Go to Settings > Privacy > Screen recording")
                print("   Allow Python/Terminal to record screen")
                return False
                
        except Exception as e:
            print(f"❌ Screenshot test failed: {e}")
            print("   Install: pip install pillow")
            return False
    
    def optimize_windows_performance(self):
        """Optimize Windows-specific performance settings."""
        print("\n⚡ Windows Performance Optimization")
        print("-" * 37)
        
        optimizations = []
        
        # Set process priority
        try:
            import psutil
            current_process = psutil.Process()
            current_process.nice(psutil.HIGH_PRIORITY_CLASS)
            optimizations.append("✅ High priority process")
        except:
            optimizations.append("⚠️ Process priority (psutil not available)")
        
        # Set environment variables
        os.environ["OPENCV_LOG_LEVEL"] = "ERROR"  # Reduce OpenCV logging
        os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"  # Reduce TensorFlow logging
        optimizations.append("✅ Reduced logging verbosity")
        
        # Windows-specific paths
        os.environ["TESSDATA_PREFIX"] = r"C:\Program Files\Tesseract-OCR\tessdata"
        optimizations.append("✅ Tesseract path configured")
        
        for opt in optimizations:
            print(f"  {opt}")
        
        return True
    
    def run_windows_setup(self):
        """Run complete Windows setup."""
        print("🪟 WINDOWS POKER ADVISORY SETUP")
        print("=" * 40)
        
        if not self.is_windows:
            print("❌ This script is designed for Windows")
            return False
        
        # Run all setup steps
        setup_steps = [
            ("Requirements Check", self.check_windows_requirements),
            ("Install Dependencies", self.install_windows_dependencies),
            ("Screenshot Permissions", self.check_screenshot_permissions),
            ("Performance Optimization", self.optimize_windows_performance),
            ("Create Shortcuts", self.create_windows_shortcuts),
            ("Firewall Configuration", self.configure_windows_firewall),
        ]
        
        results = []
        for step_name, step_func in setup_steps:
            try:
                result = step_func()
                results.append(result)
            except Exception as e:
                print(f"❌ {step_name} failed: {e}")
                results.append(False)
        
        # Summary
        success_count = sum(1 for r in results if r)
        total_steps = len(results)
        
        print(f"\n🎯 SETUP SUMMARY")
        print("-" * 20)
        print(f"Completed: {success_count}/{total_steps} steps")
        
        if success_count >= total_steps * 0.8:
            print("✅ Windows setup successful!")
            print("\n🚀 Ready to start:")
            print("   - Double-click 'Start Poker App.bat'")
            print("   - Or run: python start_app.py")
            return True
        else:
            print("⚠️ Some setup steps failed")
            print("   App may still work with reduced functionality")
            return False

def main():
    """Main Windows setup function."""
    setup = WindowsPokerSetup()
    
    if setup.run_windows_setup():
        print("\n🃏 Starting Poker Advisory App...")
        
        # Auto-start the app
        try:
            os.chdir(setup.script_dir)
            subprocess.run([sys.executable, "start_app.py"])
        except KeyboardInterrupt:
            print("\n👋 Setup complete. Run start_app.py to begin.")
        except Exception as e:
            print(f"\n⚠️ Auto-start failed: {e}")
            print("Manually run: python start_app.py")
    
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()