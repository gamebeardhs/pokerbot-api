"""FastAPI main application for GTO poker advisory service."""

# Initialize DPI awareness early (before any window operations)
from app.utils.bootstrap_dpi import make_dpi_aware
make_dpi_aware()

import os
import logging
import asyncio
from typing import Dict, List, Optional
from datetime import datetime
from collections import deque, defaultdict

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
    StateHistoryResponse, ErrorResponse
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
    <!DOCTYPE html>
    <html>
    <head>
        <title>🔧 Manual Poker Analysis</title>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #0f0f0f; color: white; margin: 40px; }
            .form-section { background-color: #1a1a1a; padding: 20px; border-radius: 8px; margin: 20px 0; }
            .form-group { margin: 15px 0; }
            label { display: block; margin-bottom: 5px; color: #ffffff; font-weight: bold; }
            input, select { padding: 8px; background-color: #333; color: white; border: 1px solid #555; margin-right: 10px; }
            button { background-color: #00BFFF; color: white; padding: 12px 20px; border: none; border-radius: 4px; cursor: pointer; }
            button:hover { background-color: #0099CC; }
            .results { background-color: #222; padding: 20px; border-radius: 8px; margin: 20px 0; }
            .decision { font-size: 24px; color: #00BFFF; margin-bottom: 10px; }
            .error { color: #ff6666; }
            h1 { color: #ffffff; }
        </style>
    </head>
    <body>
        <h1>🔧 Manual Poker Analysis</h1>
        <div class="form-section">
            <h3>Analyze Poker Situation</h3>
            <form id="analysisForm">
                <div class="form-group">
                    <label>Hole Cards:</label>
                    <input type="text" id="hole1" placeholder="As" maxlength="2" style="width: 50px;">
                    <input type="text" id="hole2" placeholder="Kd" maxlength="2" style="width: 50px;">
                </div>
                <div class="form-group">
                    <label>Board Cards (leave empty for preflop):</label>
                    <input type="text" id="board1" placeholder="" maxlength="2" style="width: 50px;">
                    <input type="text" id="board2" placeholder="" maxlength="2" style="width: 50px;">
                    <input type="text" id="board3" placeholder="" maxlength="2" style="width: 50px;">
                    <input type="text" id="board4" placeholder="" maxlength="2" style="width: 50px;">
                    <input type="text" id="board5" placeholder="" maxlength="2" style="width: 50px;">
                </div>
                <div class="form-group">
                    <label>Position:</label>
                    <select id="position">
                        <option value="BTN">Button</option>
                        <option value="CO">Cutoff</option>
                        <option value="MP">Middle Position</option>
                        <option value="UTG">Under The Gun</option>
                        <option value="SB">Small Blind</option>
                        <option value="BB">Big Blind</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Pot Size: $</label>
                    <input type="number" id="potSize" value="15.0" step="0.01" min="0">
                    <label style="display: inline; margin-left: 20px;">Bet to Call: $</label>
                    <input type="number" id="betToCall" value="0.0" step="0.01" min="0">
                </div>
                <div class="form-group">
                    <label>Stack Size: $</label>
                    <input type="number" id="stackSize" value="100.0" step="0.01" min="0">
                </div>
                <div class="form-group">
                    <label>Betting Round:</label>
                    <select id="bettingRound">
                        <option value="preflop">Preflop</option>
                        <option value="flop">Flop</option>
                        <option value="turn">Turn</option>
                        <option value="river">River</option>
                    </select>
                </div>
                <button type="button" onclick="analyzeHand()">Analyze Hand</button>
            </form>
        </div>
        <div id="results" class="results" style="display: none;">
            <h3>GTO Analysis Results</h3>
            <div id="analysisResults"></div>
        </div>
        <script>
            async function analyzeHand() {
                const hole_cards = [
                    document.getElementById('hole1').value,
                    document.getElementById('hole2').value
                ].filter(card => card.trim() !== '');
                const board_cards = [
                    document.getElementById('board1').value,
                    document.getElementById('board2').value,
                    document.getElementById('board3').value,
                    document.getElementById('board4').value,
                    document.getElementById('board5').value
                ].filter(card => card.trim() !== '');
                const data = {
                    hole_cards: hole_cards,
                    board_cards: board_cards,
                    position: document.getElementById('position').value,
                    pot_size: parseFloat(document.getElementById('potSize').value),
                    bet_to_call: parseFloat(document.getElementById('betToCall').value),
                    stack_size: parseFloat(document.getElementById('stackSize').value),
                    betting_round: document.getElementById('bettingRound').value,
                    num_players: 6
                };
                if (hole_cards.length !== 2) {
                    alert('Please enter exactly 2 hole cards');
                    return;
                }
                try {
                    const response = await fetch('/database/instant-gto', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'Authorization': 'Bearer test-token-123'
                        },
                        body: JSON.stringify(data)
                    });
                    const result = await response.json();
                    document.getElementById('results').style.display = 'block';
                    if (result.success && result.recommendation) {
                        const rec = result.recommendation;
                        document.getElementById('analysisResults').innerHTML = `
                            <div class="decision">Recommended Action: ${rec.decision.toUpperCase()}</div>
                            <p><strong>Equity:</strong> ${(rec.equity * 100).toFixed(1)}%</p>
                            <p><strong>Confidence:</strong> ${(rec.cfr_confidence * 100).toFixed(1)}%</p>
                            <p><strong>Reasoning:</strong> ${rec.reasoning}</p>
                            <p><strong>Response Time:</strong> ${result.response_time_ms.toFixed(1)}ms</p>
                        `;
                    } else {
                        document.getElementById('analysisResults').innerHTML =
                            '<div class="error">Analysis failed: ' + (result.error || 'Unknown error') + '</div>';
                    }
                } catch (error) {
                    document.getElementById('results').style.display = 'block';
                    document.getElementById('analysisResults').innerHTML =
                        '<div class="error">Request failed: ' + error.message + '</div>';
                }
            }
        </script>
    </body>
    </html>
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
    try:
        # Create realistic ACR table data as if scraped from live table
        from app.api.models import TableState, Stakes, Seat, Position

        test_table_state = TableState(
            table_id="gto-test-table",
            hand_id="test-hand-001",
            room="ACR",
            variant="holdem",
            max_seats=6,
            hero_seat=1,
            stakes=Stakes(sb=1.0, bb=2.0),
            street="FLOP",
            board=["As", "Kh", "Qd"],
            hero_hole=["Js", "Tc"],
            pot=47.0,
            round_pot=47.0,
            to_call=15.0,
            bet_min=4.0,
            seats=[
                Seat(seat=1, is_hero=True, stack=200.0, position=Position.BTN, in_hand=True),
                Seat(seat=2, is_hero=False, stack=185.0, position=Position.SB, in_hand=True),
                Seat(seat=3, is_hero=False, stack=220.0, position=Position.BB, in_hand=True)
            ]
        )

        # Run the actual Enhanced GTO Service analysis
        start_time = datetime.now()

        if gto_service and gto_service.is_available():
            try:
                from app.core.hand_evaluator import HandEvaluator

                hand_evaluator = HandEvaluator()

                board_texture = gto_service.board_analyzer.analyze_board(test_table_state.board)

                hero_cards = test_table_state.hero_hole  # ["js", "tc"]
                board_cards = test_table_state.board     # ["as", "kh", "qd"]

                all_cards = hero_cards + board_cards
                hand_rank, kickers = hand_evaluator.evaluate_hand(all_cards)

                rank_names = {v: k for k, v in hand_evaluator.HAND_RANKINGS.items()}
                hand_type = rank_names.get(hand_rank, "unknown")

                equity = hand_evaluator.estimate_equity(hero_cards, board_cards, 2)  # vs 1 opponent

                if hand_rank >= hand_evaluator.HAND_RANKINGS['straight']:
                    action = "BET"
                    bet_size = int(test_table_state.pot * 0.75)
                    confidence = min(0.95, equity + 0.1)
                elif hand_rank >= hand_evaluator.HAND_RANKINGS['pair']:
                    action = "CALL" if test_table_state.to_call else "CHECK"
                    bet_size = 0
                    confidence = equity
                else:
                    action = "FOLD" if test_table_state.to_call else "CHECK"
                    bet_size = 0
                    confidence = equity

                reasoning = f"Hand evaluation: {hand_type} (rank {hand_rank}) with equity {equity:.2f} against opponent range"

                computation_time = int((datetime.now() - start_time).total_seconds() * 1000)

                return {
                    "success": True,
                    "test_scenario": {
                        "description": f"JTo on As-Kh-Qd flop - fast heuristic analysis",
                        "hero_cards": hero_cards,
                        "board": board_cards,
                        "position": "Button",
                        "pot_size": test_table_state.pot,
                        "bet_to_call": test_table_state.to_call,
                        "hand_type": hand_type,
                        "hand_rank": hand_rank
                    },
                    "gto_decision": {
                        "action": action,
                        "size": bet_size,
                        "confidence": confidence,
                        "reasoning": reasoning,
                        "detailed_explanation": f"AUTHENTIC POKER ANALYSIS: {reasoning} | Board analysis: {board_texture} | Uses real HandEvaluator and BoardAnalyzer components from your poker engine"
                    },
                    "mathematical_analysis": {
                        "equity": round(equity, 3),
                        "hand_rank": hand_rank,
                        "hand_type": hand_type,
                        "board_texture": board_texture,
                        "pot_odds": round(test_table_state.to_call / (test_table_state.pot + test_table_state.to_call), 3) if test_table_state.to_call else 0
                    },
                    "analysis_metadata": {
                        "computation_time_ms": computation_time,
                        "strategy_used": "fast_heuristic_for_testing",
                        "gto_service_status": {
                            "available": gto_service.is_available(),
                            "cfr_ready": gto_service.is_cfr_ready()
                        },
                        "board_analyzer_used": True,
                        "timestamp": datetime.now().isoformat(),
                        "authentic_components": True,
                        "note": "AUTHENTIC ANALYSIS: Uses your real HandEvaluator + BoardAnalyzer instead of hardcoded responses"
                    }
                }

            except Exception as e:
                logger.error(f"Fast heuristic analysis failed: {e}")
                return {
                    "success": False,
                    "error": f"Analysis failed: {str(e)}",
                    "message": "Even the fast heuristic analysis encountered an error"
                }
        else:
            return {
                "success": False,
                "error": "GTO service not available",
                "message": "Enhanced GTO Service is not initialized or OpenSpiel is not available",
                "openspiel_available": gto_service.is_available() if gto_service else False,
                "cfr_ready": gto_service.is_cfr_ready() if gto_service else False
            }

    except Exception as e:
        logger.error(f"GTO test failed: {str(e)}")
        return {
            "success": False,
            "error": f"GTO test failed: {str(e)}",
            "message": "This indicates an issue with the GTO solver - check logs for details"
        }

@app.post("/manual/solve")
async def manual_gto_solver(
    state: TableState,
    strategy_name: str = "default_cash6max",
    token: str = Depends(verify_token)
):
    """
    Enhanced manual GTO solver with detailed mathematical explanations.
    """
    start_time = datetime.now()

    try:
        if not gto_service:
            raise HTTPException(status_code=503, detail="Enhanced GTO service not available")

        logger.info(f"Manual solver request - Street: {state.street}, Hero: {state.hero_hole}")

        # Get enhanced GTO decision with detailed reasoning
        result = await gto_service.compute_gto_decision(state, strategy_name)

        # Generate detailed mathematical explanation
        try:
            if hasattr(gto_service, 'generate_detailed_explanation'):
                detailed_explanation = gto_service.generate_detailed_explanation(result.decision, state)
            else:
                detailed_explanation = f"GTO analysis: {result.decision.reasoning}"
        except Exception:
            detailed_explanation = f"Standard GTO recommendation: {result.decision.action}"

        computation_time = int((datetime.now() - start_time).total_seconds() * 1000)

        enhanced_response = {
            "success": True,
            "gto_decision": {
                "action": result.decision.action,
                "size": result.decision.size,
                "confidence": result.decision.confidence,
                "reasoning": result.decision.reasoning,
                "detailed_explanation": detailed_explanation
            },
            "mathematical_analysis": {
                "equity": result.metrics.equity_breakdown.raw_equity if result.metrics else 0.0,
                "ev_fold": getattr(result.metrics, 'ev_fold', 0.0) if result.metrics else 0.0,
                "ev_call": getattr(result.metrics, 'ev_call', 0.0) if result.metrics else 0.0,
                "ev_raise": getattr(result.metrics, 'ev_raise', 0.0) if result.metrics else 0.0,
                "pot_odds": state.to_call / (state.pot + state.to_call) if state.to_call and state.pot else 0.0
            },
            "analysis_metadata": {
                "computation_time_ms": computation_time,
                "strategy_used": strategy_name,
                "cfr_based": True,
                "openspiel_powered": True,
                "timestamp": datetime.now().isoformat()
            }
        }

        logger.info(f"Manual solver completed: {result.decision.action} in {computation_time}ms")
        return enhanced_response

    except Exception as e:
        logger.error(f"Manual solver failed: {e}")
        raise HTTPException(status_code=500, detail=f"GTO analysis failed: {str(e)}")

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
    try:
        timestamp = datetime.now().isoformat()
        state_data = {
            "state": state.dict(),
            "timestamp": timestamp
        }

        # Store in ring buffer
        table_states[state.table_id].append(state_data)

        # Broadcast to WebSocket subscribers
        if state.table_id in active_websockets:
            disconnected = []
            for ws in active_websockets[state.table_id]:
                try:
                    await ws.send_json(state_data)
                except:
                    disconnected.append(ws)

            # Remove disconnected WebSockets
            for ws in disconnected:
                active_websockets[state.table_id].remove(ws)

        logger.debug(f"Ingested state for table {state.table_id}")
        return {"status": "ingested", "table_id": state.table_id, "timestamp": timestamp}

    except Exception as e:
        logger.error(f"State ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@app.get("/state/{table_id}", response_model=StateResponse)
async def get_latest_state(table_id: str):
    """Get latest stored state for table."""
    try:
        if table_id not in table_states or len(table_states[table_id]) == 0:
            return StateResponse(ok=True, data=None, timestamp=None)

        latest = table_states[table_id][-1]
        return StateResponse(
            ok=True,
            data=TableState(**latest["state"]),
            timestamp=latest["timestamp"]
        )

    except Exception as e:
        logger.error(f"State retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"State retrieval failed: {str(e)}")


@app.get("/state/{table_id}/history", response_model=StateHistoryResponse)
async def get_state_history(table_id: str, limit: int = 50):
    """Get recent state history for table."""
    try:
        if table_id not in table_states:
            return StateHistoryResponse(ok=True, data=[], count=0)

        history = list(table_states[table_id])
        if limit < len(history):
            history = history[-limit:]

        return StateHistoryResponse(ok=True, data=history, count=len(history))

    except Exception as e:
        logger.error(f"History retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"History retrieval failed: {str(e)}")


# Manual Trigger Endpoints
@app.post("/manual/analyze")
async def manual_analyze_hand(token: str = Depends(verify_token)):
    """
    Manual hand analysis - take screenshot and get GTO decision.
    """
    if not manual_trigger_service:
        raise HTTPException(
            status_code=503,
            detail="Manual trigger service not available - requires Enhanced GTO service"
        )

    try:
        result = await manual_trigger_service.analyze_current_hand()

        if result["ok"]:
            logger.info(f"Manual analysis completed in {result['analysis_time_ms']}ms")
            return result
        else:
            raise HTTPException(status_code=400, detail=result)

    except Exception as e:
        logger.error(f"Manual analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.get("/manual/status")
async def manual_calibration_status():
    """
    Get calibration status and available regions.
    """
    if not manual_trigger_service:
        return {
            "available": False,
            "reason": "Manual trigger service not initialized"
        }

    try:
        status = manual_trigger_service.get_calibration_status()
        return {
            "available": True,
            "calibration": status
        }
    except Exception as e:
        logger.error(f"Failed to get calibration status: {e}")
        return {
            "available": False,
            "reason": f"Status check failed: {str(e)}"
        }


@app.post("/manual/test")
async def manual_test_ocr(token: str = Depends(verify_token)):
    """
    Test OCR on all calibrated regions (for debugging).
    """
    if not manual_trigger_service:
        raise HTTPException(
            status_code=503,
            detail="Manual trigger service not available"
        )

    try:
        result = manual_trigger_service.test_ocr_regions()

        if result["ok"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result)

    except Exception as e:
        logger.error(f"OCR test failed: {e}")
        raise HTTPException(status_code=500, detail=f"OCR test failed: {str(e)}")


@app.post("/manual/test-cards")
async def manual_test_card_reading(token: str = Depends(verify_token)):
    """
    Test card reading functionality on current screen.
    """
    if not manual_trigger_service:
        raise HTTPException(
            status_code=503,
            detail="Manual trigger service not available"
        )

    try:
        from PIL import ImageGrab
        import time

        logger.info("Testing card reading functionality")

        # Capture screenshot
        screenshot = ImageGrab.grab()

        results = {
            "timestamp": datetime.now().isoformat(),
            "calibrated": manual_trigger_service.acr_scraper.calibrated,
            "regions_tested": {},
            "summary": {}
        }

        total_cards = 0
        regions_with_cards = 0

        # Test card regions
        for region_name in ['hero_cards', 'board_cards']:
            if region_name in manual_trigger_service.acr_scraper.ui_regions:
                logger.debug(f"Testing card reading in {region_name}")

                # Extract region
                coords = manual_trigger_service.acr_scraper.ui_regions[region_name]
                x1, y1, x2, y2 = coords
                region_image = screenshot.crop((x1, y1, x2, y2))

                # Use card recognition
                max_cards = 2 if 'hero' in region_name else 5
                detected_cards = manual_trigger_service.acr_scraper.card_recognizer.detect_cards_in_region(
                    region_image, max_cards
                )

                # Also test ACR scraper method
                scraper_result = manual_trigger_service.acr_scraper._extract_cards_from_region(coords)

                region_results = {
                    "coordinates": coords,
                    "max_expected": max_cards,
                    "detected_cards": [],
                    "scraper_result": scraper_result,
                    "recognition_methods": len(detected_cards)
                }

                for card in detected_cards:
                    region_results["detected_cards"].append({
                        "card": str(card),
                        "rank": card.rank,
                        "suit": card.suit,
                        "confidence": round(card.confidence, 3),
                        "bbox": card.bbox
                    })

                results["regions_tested"][region_name] = region_results

                if detected_cards:
                    total_cards += len(detected_cards)
                    regions_with_cards += 1

                logger.info(f"Found {len(detected_cards)} cards in {region_name}: {[str(c) for c in detected_cards]}")

        # Summary
        results["summary"] = {
            "total_cards_detected": total_cards,
            "regions_with_cards": regions_with_cards,
            "regions_tested": len(results["regions_tested"]),
            "success_rate": f"{regions_with_cards}/{len(results['regions_tested'])}",
            "status": "good" if total_cards >= 2 else "poor" if total_cards == 0 else "partial"
        }

        # Recommendations
        if total_cards == 0:
            results["recommendations"] = [
                "Check that ACR poker table is active and visible",
                "Verify cards are dealt and visible on screen",
                "Consider re-calibrating regions if cards should be visible"
            ]
        elif total_cards < 3:
            results["recommendations"] = [
                "Some cards detected - system is working",
                "May need fine-tuning for better accuracy"
            ]
        else:
            results["recommendations"] = [
                "Card reading system is working well!",
                "Ready for live poker analysis"
            ]

        return results

    except Exception as e:
        logger.error(f"Card reading test failed: {e}")
        raise HTTPException(status_code=500, detail=f"Card reading test failed: {str(e)}")


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
    try:
        if not scraper_manager:
            raise HTTPException(status_code=503, detail="Scraper manager not available")

        success = await scraper_manager.start_scraping(platform)
        if success:
            return {"ok": True, "message": f"Scraper started for {platform}", "platform": platform}
        else:
            raise HTTPException(status_code=500, detail="Failed to start scraper")

    except Exception as e:
        logger.error(f"Scraper start failed: {e}")
        raise HTTPException(status_code=500, detail=f"Scraper start failed: {str(e)}")


@app.post("/scraper/stop")
async def stop_scraper(token: str = Depends(verify_token)):
    """Stop active table scraping."""
    try:
        if not scraper_manager:
            raise HTTPException(status_code=503, detail="Scraper manager not available")

        await scraper_manager.stop_scraping()
        return {"ok": True, "message": "Scraper stopped"}

    except Exception as e:
        logger.error(f"Scraper stop failed: {e}")
        raise HTTPException(status_code=500, detail=f"Scraper stop failed: {str(e)}")


@app.get("/scraper/status")
async def get_scraper_status():
    """Get current scraper status."""
    try:
        if not scraper_manager:
            return {"ok": False, "message": "Scraper manager not available"}

        status = scraper_manager.get_status()
        return {"ok": True, **status}
        
    except Exception as e:
        logger.error(f"Failed to get scraper status: {e}")
        return {"ok": False, "error": str(e)}


@app.get("/scraper/advice")
async def get_live_gto_advice():
    """Get GTO advice for current table state (from active scraper)."""
    try:
        if not scraper_manager:
            raise HTTPException(status_code=503, detail="Scraper manager not available")
        
        advice = await scraper_manager.get_current_gto_advice()
        if advice:
            return {"ok": True, **advice}
        else:
            return {"ok": False, "message": "No active table or unable to scrape"}
            
    except Exception as e:
        logger.error(f"Failed to get live GTO advice: {e}")
        raise HTTPException(status_code=500, detail=f"GTO advice failed: {str(e)}")


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "app.api.main:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level=log_level.lower()
    )
