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
    ui_path = Path("acr_intelligent_calibration_ui.html")
    if ui_path.exists():
        with open(ui_path, 'r', encoding='utf-8') as f:
            return HTMLResponse(content=f.read())
    else:
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head><title>Calibration UI</title></head>
        <body>
            <h1>ACR Intelligent Calibration UI</h1>
            <p>UI file not found. Please ensure acr_intelligent_calibration_ui.html exists.</p>
        </body>
        </html>
        """)