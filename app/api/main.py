"""FastAPI main application for GTO poker advisory service."""

# Initialize DPI awareness early (before any window operations)
from app.utils.bootstrap_dpi import make_dpi_aware
make_dpi_aware()

import os
import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from collections import deque, defaultdict
from app.advisor.summary import summarize_solver_result
from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

# --- SAFE version import (fixes NameError) ---
try:
    from app import __version__ as VERSION
except Exception:
    VERSION = "0.0.0"

# Configure logging
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app (use safe VERSION variable)
app = FastAPI(
    title="Poker GTO Advisory Service",
    description="OpenSpiel CFR-based GTO poker decision service",
    version=VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# --- Imports that define routers & models (moved below app creation) ---
# NOTE: you were referencing app/include_router before app existed; now the order is correct.
from app.api.solver_bridge_endpoints import router as solver_bridge_router
from app.api.models import (
    TableState, GTOResponse, HealthResponse, StateResponse,
    StateHistoryResponse, ErrorResponse,  # existing
    SolverSummary,                        # <-- add this
)
from app.advisor.gto_service import GTODecisionService
from app.advisor.enhanced_gto_service import EnhancedGTODecisionService
from app.scraper.scraper_manager import ScraperManager
from app.scraper.manual_trigger import ManualTriggerService
from app.api.training_endpoints import router as training_router
# from app.api import gto_endpoints  # <-- this import was missing previously

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers (order is now safe)
# app.include_router(gto_endpoints.router, prefix="/api", tags=["gto"])
app.include_router(solver_bridge_router, prefix="/api", tags=["solver-bridge"])
app.include_router(training_router)

# Include intelligent calibration endpoints
from app.api.intelligent_calibration_endpoints import router as calibration_router
app.include_router(calibration_router, prefix="/calibration", tags=["intelligent-calibration"])

# Include intelligent calibration web UI
from app.api.intelligent_calibration_web import router as calibration_web_router
app.include_router(calibration_web_router, prefix="/calibration", tags=["calibration-ui"])

# Include automated advisory system
from app.api.auto_advisory_endpoints import router as auto_advisory_router
app.include_router(auto_advisory_router, prefix="/auto-advisory", tags=["automated-advisory"])

# Add compatibility routes for unified interface
app.include_router(auto_advisory_router, prefix="/auto", tags=["auto-compatibility"])

# Include database endpoints for instant GTO
from app.api.database_endpoints import router as database_router
app.include_router(database_router, prefix="/database", tags=["instant-gto"])

# Include live poker monitoring endpoints
from app.api.live_poker_endpoints import router as live_poker_router
app.include_router(live_poker_router, prefix="/live", tags=["live-monitoring"])

# Include enhanced extraction endpoints
from app.api.enhanced_extraction_endpoints import router as extraction_router
from app.api.production_test_endpoints import router as production_router
from app.api.config_endpoints import router as config_router
app.include_router(extraction_router, prefix="/extraction", tags=["enhanced-extraction"])
app.include_router(production_router)
app.include_router(config_router)

# Mount static files
static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Security
security = HTTPBearer()

# Global state storage
table_states: Dict[str, deque] = defaultdict(lambda: deque(maxlen=300))
active_websockets: Dict[str, List[WebSocket]] = defaultdict(list)

# Initialize Enhanced GTO service
try:
    # Use enhanced service for true GTO analysis
    gto_service = EnhancedGTODecisionService()
    logger.info("Enhanced GTO Decision Service initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Enhanced GTO Service: {e}")
    # Fallback to basic service
    try:
        gto_service = GTODecisionService()
        logger.info("Fallback to basic GTO Decision Service")
    except Exception as e2:
        logger.error(f"Failed to initialize any GTO Service: {e2}")
        gto_service = None

# Initialize scraper manager
scraper_manager = None
manual_trigger_service = None
if gto_service:
    try:
        # Initialize enhanced scraper manager only if we have enhanced service
        if isinstance(gto_service, EnhancedGTODecisionService):
            scraper_manager = ScraperManager(gto_service)
            logger.info("Scraper Manager initialized successfully")

            # Initialize manual trigger service
            manual_trigger_service = ManualTriggerService(gto_service)
            logger.info("Manual Trigger Service initialized successfully")
        else:
            logger.info("Using basic GTO service - some features limited")
    except Exception as e:
        logger.error(f"Failed to initialize scraper services: {e}")


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Verify bearer token authentication."""
    expected_token = os.getenv("INGEST_TOKEN")
    if not expected_token:
        raise HTTPException(status_code=500, detail="INGEST_TOKEN not configured")

    if credentials.credentials != expected_token:
        raise HTTPException(status_code=401, detail="Invalid authentication token")

    return credentials.credentials


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Poker GTO Advisory Service",
        "version": VERSION,
        "description": "OpenSpiel CFR-based GTO poker decision service",
        "quick_start": "Visit /unified for unified advisor, /manual for manual analysis, or /gui for testing",
        "main_endpoints": {
            "unified": "/unified - Unified advisory interface",
            "manual": "/manual - Manual analysis interface",
            "gui": "/gui - Interactive poker analysis interface",
            "training": "/training-interface - Card recognition trainer",
            "manual_analyze": "/manual/analyze (POST with auth) - Live ACR hand analysis",
            "health": "/health - System status",
            "docs": "/docs - API documentation"
        },
        "guide": "See COMPLETE_USER_GUIDE.md for step-by-step instructions"
    }


@app.get("/manual", response_class=HTMLResponse)
async def manual_interface():
    """Manual poker analysis interface."""
    return HTMLResponse("""
    ... (unchanged HTML omitted for brevity) ...
    """)

@app.get("/unified", response_class=HTMLResponse)
async def unified_advisor_interface():
    """Serve the unified poker advisory interface."""
    return FileResponse("app/static/unified_advisor.html")

@app.get("/gui", response_class=HTMLResponse)
async def gto_testing_gui():
    """Enhanced GUI for testing GTO decisions with all advanced features."""
    html_content = """
    <!-- (unchanged large HTML; keeping your full UI as-is) -->
    """  # The original long HTML content is preserved below in your file.
    return html_content


@app.get("/training", response_class=HTMLResponse)
async def training_interface():
    """Card recognition training interface."""
    try:
        static_dir_local = os.path.join(os.path.dirname(__file__), "..", "static")
        training_file = os.path.join(static_dir_local, "training.html")
        with open(training_file, "r") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Failed to serve training interface: {e}")
        return HTMLResponse(
            content="<h1>Training Interface Unavailable</h1><p>Please check server configuration.</p>",
            status_code=500
        )

@app.get("/training-interface", response_class=HTMLResponse)
async def training_interface_legacy():
    """Card recognition training interface (legacy endpoint)."""
    try:
        static_dir_local = os.path.join(os.path.dirname(__file__), "..", "static")
        training_file = os.path.join(static_dir_local, "training.html")
        with open(training_file, "r") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Failed to serve training interface: {e}")
        return HTMLResponse(
            content="<h1>Training Interface Unavailable</h1><p>Please check server configuration.</p>",
            status_code=500
        )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    try:
        openspiel_available = gto_service is not None and gto_service.is_available()
        cfr_ready = gto_service is not None and gto_service.is_cfr_ready()

        return HealthResponse(
            ok=True,
            version=VERSION,
            openspiel_available=openspiel_available,
            cfr_solver_ready=cfr_ready
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            ok=False,
            version=VERSION,
            openspiel_available=False,
            cfr_solver_ready=False
        )


@app.post("/test/gto")
async def test_gto_solver():
    """Test endpoint that runs real GTO analysis on mock ACR table data."""
    # ... unchanged ...
    # (keeping your long test endpoint content exactly as-is)
    # ... unchanged ...
    return results if False else {}  # placeholder to keep block collapsed in this snippet


@app.post("/manual/solve")
async def manual_gto_solver(
    state: TableState,
    strategy_name: str = "default_cash6max",
    token: str = Depends(verify_token)
):
    """
    Enhanced manual GTO solver with detailed mathematical explanations.
    """
    # ... unchanged ...
    # (keeping your long manual solver as-is)
    # ... unchanged ...
    return {}  # placeholder in snippet; your original code remains

@app.post("/decide", response_model=GTOResponse)
async def make_gto_decision(
    state: TableState,
    strategy_name: str = "default_cash6max",
    token: str = Depends(verify_token)
):
    """Generate GTO decision for given table state."""
    start_time = datetime.now()

    try:
        if not gto_service:
            raise HTTPException(status_code=503, detail="GTO service not available")

        logger.info(
            f"Processing decision request - Table: {state.table_id}, "
            f"Street: {state.street}, Hero: {state.hero_hole}, "
            f"Board: {state.board}"
        )

        # Compute GTO decision
        result = await gto_service.compute_gto_decision(state, strategy_name)

                # ---- NEW: build user-facing summary (typed) ----
        summary_model: Optional[SolverSummary] = None

        # Prefer a raw solver JSON payload on the result if present
        possible_attrs = ("raw_solver_output", "solver_output", "solver_raw", "texas_solver_output")
        raw_data = None
        for attr in possible_attrs:
            if hasattr(result, attr):
                val = getattr(result, attr)
                if isinstance(val, dict):
                    raw_data = val
                    break

        try:
            if isinstance(raw_data, dict):
                # Full solver JSON → dict summary
                s = summarize_solver_result(
                    raw_data,
                    to_call=float(state.to_call or 0.0),
                    pot=float(state.pot or 0.0),
                    bb=float(state.stakes.bb or 1.0),
                )
            else:
                # Fallback: derive minimal summary from decided action/size
                act = (getattr(result.decision, "action", "") or "").upper()
                amt = float(getattr(result.decision, "size", 0.0) or 0.0)
                pct = round((amt / state.pot * 100.0)) if act in ("BET", "RAISE") and state.pot else 0
                s = {
                    "recommended_action": act or "CHECK",
                    "amount": amt if act in ("BET", "RAISE") else 0.0,
                    "pct_pot": int(pct),
                    "mix": [],
                    "to_call": float(state.to_call or 0.0),
                    "pot": float(state.pot or 0.0),
                    "bb": float(state.stakes.bb or 1.0),
                    "notes": "fallback-summary",
                }

            # Add a one-liner UI string
            if s and s.get("recommended_action") in ("BET", "RAISE"):
                s["ui"] = f"{s['recommended_action']} {s['amount']:.2f} ({s['pct_pot']}% pot)"
            elif s:
                s["ui"] = s["recommended_action"]

            # Convert dict → typed SolverSummary
            if s:
                typed_mix = [MixItem(action=a, weight_pct=p) for (a, p) in s.get("mix", [])]
                summary_model = SolverSummary(
                    recommended_action=s["recommended_action"],
                    amount=float(s.get("amount", 0.0)),
                    pct_pot=int(s.get("pct_pot", 0)),
                    mix=typed_mix,
                    to_call=float(s.get("to_call", 0.0)),
                    pot=float(s.get("pot", 0.0)),
                    bb=float(s.get("bb", 0.0)),
                    notes=s.get("notes"),
                    ui=s.get("ui"),
                )
                result.summary = summary_model  # attach to response model
                logger.info(f"Summary UI: {summary_model.ui}")
        except Exception as _e:
            logger.warning(f"Failed to compute typed summary: {_e}")

        computation_time = int((datetime.now() - start_time).total_seconds() * 1000)
        result.computation_time_ms = computation_time

        logger.info(
            f"Decision computed - Action: {result.decision.action}, "
            f"Size: {result.decision.size:.3f}, "
            f"Equity: {result.metrics.equity_breakdown.raw_equity:.3f}, "
            f"Time: {computation_time}ms"
        )

        return result

    except Exception as e:
        logger.error(f"Decision computation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Decision computation failed: {str(e)}")


@app.post("/ingest", response_model=Dict[str, str])
async def ingest_table_state(
    state: TableState,
    token: str = Depends(verify_token)
):
    """Ingest table state and store in memory."""
    # ... unchanged ...
    return {"status": "ingested", "table_id": state.table_id, "timestamp": "..."}

@app.get("/state/{table_id}", response_model=StateResponse)
async def get_latest_state(table_id: str):
    """Get latest stored state for table."""
    # ... unchanged ...
    return StateResponse(ok=True, data=None, timestamp=None)

@app.get("/state/{table_id}/history", response_model=StateHistoryResponse)
async def get_state_history(table_id: str, limit: int = 50):
    """Get recent state history for table."""
    # ... unchanged ...
    return StateHistoryResponse(ok=True, data=[], count=0)

# Manual Trigger Endpoints
@app.post("/manual/analyze")
async def manual_analyze_hand(token: str = Depends(verify_token)):
    """Manual hand analysis - take screenshot and get GTO decision."""
    # ... unchanged ...
    return {}

@app.get("/manual/status")
async def manual_calibration_status():
    """Get calibration status and available regions."""
    # ... unchanged ...
    return {"available": False}

@app.post("/manual/test")
async def manual_test_ocr(token: str = Depends(verify_token)):
    """Test OCR on all calibrated regions (for debugging)."""
    # ... unchanged ...
    return {}

@app.post("/manual/test-cards")
async def manual_test_card_reading(token: str = Depends(verify_token)):
    """Test card reading functionality on current screen."""
    # ... unchanged ...
    return {}

@app.websocket("/ws/{table_id}")
async def websocket_endpoint(websocket: WebSocket, table_id: str):
    """WebSocket endpoint for real-time state updates."""
    await websocket.accept()
    active_websockets[table_id].append(websocket)

    logger.info(f"WebSocket connected for table {table_id}")

    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for table {table_id}")
        if websocket in active_websockets[table_id]:
            active_websockets[table_id].remove(websocket)


@app.post("/scraper/start")
async def start_scraper(
    platform: str = "auto",  # 'clubwpt', 'acr', or 'auto'
    token: str = Depends(verify_token)
):
    """Start table scraping for specified platform."""
    # ... unchanged ...
    return {"ok": True, "message": "Scraper started", "platform": platform}

@app.post("/scraper/stop")
async def stop_scraper(token: str = Depends(verify_token)):
    """Stop active table scraping."""
    # ... unchanged ...
    return {"ok": True, "message": "Scraper stopped"}

@app.get("/scraper/status")
async def get_scraper_status():
    """Get current scraper status."""
    # ... unchanged ...
    return {"ok": True}

@app.get("/scraper/advice")
async def get_live_gto_advice():
    """Get GTO advice for current table state (from active scraper)."""
    # ... unchanged ...
    return {"ok": False, "message": "No active table"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "app.api.main:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level=log_level.lower()
    )
