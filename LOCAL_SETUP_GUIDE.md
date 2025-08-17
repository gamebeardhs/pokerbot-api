# Local Setup Guide for ACR Poker Advisory

## Why Local Setup is Required

The system needs direct access to your desktop to:
- Capture screenshots of your ACR poker client
- Detect poker table elements in real-time
- Provide GTO recommendations while you play

**Replit's remote environment cannot access your local ACR client.**

## Quick Local Setup (5 minutes)

### 1. Download Project Files
```bash
# Download the key files you need locally:
# - All files in app/ directory
# - requirements.txt
# - start_app.py
# - debug_table_detection.py
```

### 2. Install Dependencies
```bash
pip install fastapi uvicorn pillow opencv-python numpy
pip install open-spiel  # For true GTO calculations
```

### 3. Run Locally
```bash
# Start the local server
python start_app.py

# Or manually:
uvicorn app.api.main:app --host 127.0.0.1 --port 5000
```

### 4. Access Local Interface
Open in your browser: `http://localhost:5000/calibration/ui`

## Testing Local Detection

1. **Open ACR poker client** on your desktop
2. **Make sure table is visible** (not minimized)
3. **Click "Debug Local"** in the calibration interface
4. **Check the debug files** created in your folder:
   - `debug_screenshot.png` - Shows what was captured
   - `debug_annotated.png` - Shows detected regions

## Expected Results with ACR Open

When ACR table is properly detected, you should see:
- **Green area**: 15-40% (poker table felt)
- **Card regions**: 2-7 detected rectangles
- **Button regions**: 3-5 action buttons
- **Screenshot size**: Your actual desktop resolution (e.g., 1920x1080)

## What the System Does

1. **Real-time Detection**: Continuously monitors your poker table
2. **Card Recognition**: Reads your hole cards and community cards
3. **GTO Analysis**: Provides mathematically optimal decisions
4. **Position Awareness**: Adjusts strategy based on your position
5. **Stack Depth**: Considers effective stack sizes

## Read-Only Safety

- **NEVER clicks buttons for you**
- **ONLY provides advice**
- **You make all actual decisions**
- **Perfect for avoiding bot detection**

## Troubleshooting

**Issue**: "No poker table detected"
- Ensure ACR client is open and visible
- Table should have green felt background
- Not minimized or covered by other windows

**Issue**: "Permission denied" on screenshot
- Run as administrator (Windows)
- Grant screen recording permissions (Mac)

**Issue**: "OpenSpiel not found"
- System works without it (mathematical approximation)
- Install for true CFR calculations: `pip install open-spiel`

## File Downloads

You can download these files from the Replit project:
- `app/` (entire directory)
- `start_app.py`
- `debug_table_detection.py`  
- `requirements.txt`

## Contact

If you need help with local setup, you can:
1. Test with the debug tools first
2. Check debug_screenshot.png to see what's being captured
3. Verify ACR client is properly positioned