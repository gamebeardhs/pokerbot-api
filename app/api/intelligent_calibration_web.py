"""
Web interface endpoint for intelligent calibration system.
"""

from fastapi import APIRouter
from fastapi.responses import FileResponse, HTMLResponse
from pathlib import Path

router = APIRouter()

@router.get("/ui", response_class=HTMLResponse)
async def intelligent_calibration_ui():
    """Serve the intelligent calibration UI.""" 
    ui_path = Path("calibration_interface.html")
    if ui_path.exists():
        with open(ui_path, 'r', encoding='utf-8') as f:
            return HTMLResponse(content=f.read())
    else:
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head>
            <title>ACR Table Calibration</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; background-color: #0a0a0a; color: #ffffff; }
                .button { background-color: #4CAF50; color: white; border: none; padding: 15px 30px; cursor: pointer; font-size: 16px; margin: 10px; border-radius: 5px; }
                .button:hover { background-color: #45a049; }
                .status { margin: 20px 0; padding: 15px; background-color: #1a1a1a; border-radius: 5px; }
                .instructions { background-color: #1a1a2a; padding: 20px; border-radius: 5px; margin: 20px 0; }
            </style>
        </head>
        <body>
            <h1>ACR Table Calibration</h1>
            <div class="instructions">
                <h3>Setup Instructions:</h3>
                <p>1. Open ACR Poker client on your computer</p>
                <p>2. Join any poker table (not lobby)</p>
                <p>3. Make sure table is visible and not minimized</p>
                <p>4. Click Start Calibration below</p>
            </div>
            <button class="button" onclick="startCalibration()">Start Calibration</button>
            <div id="status" class="status" style="display: none;"></div>
            
            <script>
                async function startCalibration() {
                    document.getElementById('status').style.display = 'block';
                    document.getElementById('status').innerHTML = 'Starting calibration...';
                    
                    try {
                        const response = await fetch('/calibration/auto-calibrate', { method: 'POST' });
                        const result = await response.json();
                        
                        if (result.success) {
                            document.getElementById('status').innerHTML = 'Success! Accuracy: ' + (result.accuracy_score * 100).toFixed(1) + '%';
                        } else {
                            document.getElementById('status').innerHTML = 'Failed: ' + result.message;
                        }
                    } catch (error) {
                        document.getElementById('status').innerHTML = 'Error: ' + error.message;
                    }
                }
            </script>
        </body>
        </html>
        """)