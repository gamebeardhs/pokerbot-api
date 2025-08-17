# Windows Screenshot Permission Fix

## Issue Identified
- System logs show: 3840x2160 (your real desktop resolution)  
- Actual screenshots: 800x600 black screen
- This is a Windows display permissions/scaling issue

## Solutions (Try in Order)

### Solution 1: Run as Administrator
1. Close the poker advisory app
2. Right-click Command Prompt → "Run as administrator"  
3. Navigate to your PokerBrain folder
4. Run: `python start_app.py`

### Solution 2: Windows Display Settings
1. Right-click desktop → Display Settings
2. Set "Scale and layout" to 100% (not 125% or 150%)
3. Restart the poker advisory app
4. Test "Detect Table" again

### Solution 3: Screen Recording Permissions
1. Windows Settings → Privacy & Security
2. Go to "Screen Recording"
3. Allow apps to record your screen
4. Find Python in the list and enable it

### Solution 4: Alternative Screenshot Method
Add this to your start_app.py before the main code:

```python
import os
os.environ['DISPLAY_CAPTURE_METHOD'] = 'alternative'
```

### Solution 5: DPI Scaling Fix
1. Find your python.exe file
2. Right-click → Properties → Compatibility
3. Check "Override high DPI scaling behavior"  
4. Set to "Application"
5. Restart the app

## Test the Fix
After trying each solution:
1. Open ACR poker client (with green felt table visible)
2. Go to http://localhost:5000/calibration/ui
3. Click "Detect Table"
4. Should now show proper resolution and detect green areas

## Expected Results After Fix
- Screenshot resolution: 3840x2160 (your real desktop)
- Green area: 5-30% (depending on table size)
- Card regions: 2-7 detected
- Table detected: True