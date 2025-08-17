#!/usr/bin/env python3
"""
Simple starter script for the Poker Advisory App.
Double-click this file to start the app on your desktop.
"""

import os
import sys
import subprocess
import webbrowser
import time
from pathlib import Path

def check_python():
    """Check if Python is available."""
    try:
        version = sys.version_info
        if version.major < 3 or (version.major == 3 and version.minor < 8):
            print("❌ Python 3.8+ required. Please update Python.")
            return False
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} found")
        return True
    except Exception as e:
        print(f"❌ Python check failed: {e}")
        return False

def install_dependencies():
    """Install required dependencies."""
    print("📦 Checking dependencies...")
    
    requirements_file = "requirements_local.txt"
    if os.path.exists(requirements_file):
        try:
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", requirements_file
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Dependencies installed successfully")
                return True
            else:
                print(f"❌ Dependency installation failed: {result.stderr}")
                return False
        except Exception as e:
            print(f"❌ Failed to install dependencies: {e}")
            return False
    else:
        print("⚠️  requirements_local.txt not found, trying basic install...")
        try:
            subprocess.run([
                sys.executable, "-m", "pip", "install", 
                "fastapi", "uvicorn", "pillow", "numpy", "opencv-python", "pandas", "pytesseract"
            ], check=True)
            print("✅ Basic dependencies installed")
            return True
        except Exception as e:
            print(f"❌ Basic dependency installation failed: {e}")
            return False

def start_server():
    """Start the FastAPI server."""
    print("🚀 Starting Poker Advisory App...")
    
    try:
        # Set default environment variables
        os.environ.setdefault("INGEST_TOKEN", "demo-token-123")
        os.environ.setdefault("LOG_LEVEL", "INFO")
        
        # Start the server
        import uvicorn
        
        print("🃏 Poker Advisory API Starting...")
        print("📍 Server will be available at: http://localhost:5000")
        print("📚 API Documentation: http://localhost:5000/docs")
        print("🎯 Training Interface: http://localhost:5000/training-interface")
        print("\n🔧 Loading components...")
        
        # Open browser after a short delay
        def open_browser():
            time.sleep(3)  # Wait for server to start
            webbrowser.open("http://localhost:5000")
        
        import threading
        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()
        
        # Start server
        uvicorn.run(
            "app.api.main:app",
            host="0.0.0.0",
            port=5000,
            reload=False,
            log_level="info"
        )
        
    except ImportError as e:
        print(f"❌ Failed to import required modules: {e}")
        print("Please install dependencies first:")
        print("pip install -r requirements_local.txt")
        return False
    except Exception as e:
        print(f"❌ Server start failed: {e}")
        return False

def main():
    """Main startup function."""
    print("🃏 Poker Advisory App Starter")
    print("=" * 40)
    
    # Check Python version
    if not check_python():
        input("Press Enter to exit...")
        return
    
    # Install dependencies
    if not install_dependencies():
        print("\n⚠️  You may need to install dependencies manually:")
        print("pip install fastapi uvicorn pillow numpy opencv-python pandas pytesseract")
        input("Press Enter to continue anyway or Ctrl+C to exit...")
    
    # Start the server
    try:
        start_server()
    except KeyboardInterrupt:
        print("\n\n👋 Poker Advisory App stopped by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
    
    input("Press Enter to exit...")

if __name__ == "__main__":
    main()