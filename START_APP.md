# 🚀 How to Start the Poker Advisory App on Your Desktop

## Prerequisites

**Python 3.11 or later** - Download from [python.org](https://python.org)

## Quick Start (Windows/Mac/Linux)

1. **Download and extract** the project to your desktop
2. **Open terminal/command prompt** in the project folder
3. **Install dependencies**:
   ```bash
   pip install -r requirements_local.txt
   ```
4. **Start the app**:
   ```bash
   python -m uvicorn app.api.main:app --host 0.0.0.0 --port 5000
   ```

**That's it!** App will be running at http://localhost:5000

## Alternative Start Methods

### Method 1: Simple Python Script
```bash
python start_app.py
```

### Method 2: Direct Module Run
```bash
python -c "import uvicorn; uvicorn.run('app.api.main:app', host='0.0.0.0', port=5000)"
```

### Method 3: Environment Variable
```bash
# Windows
set INGEST_TOKEN=your-token
python -m uvicorn app.api.main:app --host 0.0.0.0 --port 5000

# Mac/Linux  
export INGEST_TOKEN=your-token
python -m uvicorn app.api.main:app --host 0.0.0.0 --port 5000
```

## What Happens When You Start

The app will:
1. Load all 52 card templates
2. Initialize GTO decision engine
3. Calibrate ACR scraper regions
4. Start web server on port 5000

You'll see output like:
```
INFO: Enhanced GTO Decision Service initialized successfully
INFO: Loaded 52 templates
INFO: ACR scraper initialized - calibrated: True
INFO: Uvicorn running on http://0.0.0.0:5000
```

## Access the App

- **Main Interface**: http://localhost:5000
- **API Docs**: http://localhost:5000/docs
- **Training Interface**: http://localhost:5000/training-interface

## Desktop Integration

### Create Desktop Shortcut (Windows)
1. Create `start_poker_app.bat`:
   ```batch
   @echo off
   cd /d "C:\path\to\your\poker-app"
   python -m uvicorn app.api.main:app --host 0.0.0.0 --port 5000
   pause
   ```

### Create Mac App Bundle
1. Use Automator to create Application
2. Add Shell Script action:
   ```bash
   cd ~/Desktop/poker-app
   python -m uvicorn app.api.main:app --host 0.0.0.0 --port 5000
   ```

### Linux Desktop File
Create `poker-app.desktop`:
```ini
[Desktop Entry]
Name=Poker Advisory App
Exec=/usr/bin/python -m uvicorn app.api.main:app --host 0.0.0.0 --port 5000
Path=/home/user/poker-app
Terminal=true
Type=Application
```

## Troubleshooting

**Port already in use?**
```bash
python -m uvicorn app.api.main:app --host 0.0.0.0 --port 8000
```

**Missing dependencies?**
```bash
pip install fastapi uvicorn pillow numpy opencv-python pandas pytesseract
```

**Can't find Python?**
- Ensure Python is in your system PATH
- Try `python3` instead of `python`

## Background Service (Advanced)

### Windows Service
Use `nssm` (Non-Sucking Service Manager):
```bash
nssm install PokerApp
nssm set PokerApp Application "C:\Python\python.exe"
nssm set PokerApp AppParameters "-m uvicorn app.api.main:app --host 0.0.0.0 --port 5000"
nssm set PokerApp AppDirectory "C:\path\to\poker-app"
nssm start PokerApp
```

### Linux Systemd Service
Create `/etc/systemd/system/poker-app.service`:
```ini
[Unit]
Description=Poker Advisory API
After=network.target

[Service]
Type=simple
User=yourusername
WorkingDirectory=/home/yourusername/poker-app
ExecStart=/usr/bin/python -m uvicorn app.api.main:app --host 0.0.0.0 --port 5000
Restart=always

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl enable poker-app
sudo systemctl start poker-app
```

## Configuration

### Environment Variables
- `LOG_LEVEL`: Set to "DEBUG" for detailed logs
- `INGEST_TOKEN`: Authentication token for API access
- `PORT`: Change default port (default: 5000)

### Custom Settings
Edit `app/config/settings.py` for:
- GTO strategy parameters
- Card recognition confidence thresholds
- Cache settings
- OCR configuration

Your poker advisory system will be ready for desktop use with full GTO analysis and card recognition capabilities!