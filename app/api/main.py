"""FastAPI main application for GTO poker advisory service."""

import os
import logging
import asyncio
from typing import Dict, List, Optional
from datetime import datetime
from collections import deque, defaultdict

from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import uvicorn

from app.api.models import (
    TableState, GTOResponse, HealthResponse, StateResponse, 
    StateHistoryResponse, ErrorResponse
)
from app.advisor.gto_service import GTODecisionService
from app.advisor.enhanced_gto_service import EnhancedGTODecisionService
from app.scraper.scraper_manager import ScraperManager
from app import __version__

# Configure logging
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Poker GTO Advisory Service",
    description="OpenSpiel CFR-based GTO poker decision service",
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
if gto_service:
    try:
        scraper_manager = ScraperManager(gto_service)
        logger.info("Scraper Manager initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize scraper manager: {e}")


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
        "version": __version__,
        "description": "OpenSpiel CFR-based GTO poker decision service",
        "endpoints": {
            "health": "/health",
            "decide": "/decide (POST with auth)",
            "ingest": "/ingest (POST with auth)",
            "state": "/state/{table_id}",
            "history": "/state/{table_id}/history",
            "websocket": "/ws/{table_id}",
            "gui": "/gui (testing interface)",
            "docs": "/docs"
        }
    }


@app.get("/gui", response_class=HTMLResponse)
async def gto_testing_gui():
    """Simple GUI for testing GTO decisions."""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>GTO Testing Interface</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; background-color: #000000; color: #ffffff; }
            .form-group { margin-bottom: 15px; }
            label { display: block; margin-bottom: 5px; font-weight: bold; color: #ffffff; }
            input, select, button { padding: 8px; margin-right: 10px; background-color: #333333; color: #ffffff; border: 1px solid #555555; }
            input[type="text"], input[type="number"], select { width: 120px; }
            button { background-color: #4CAF50; color: white; border: none; padding: 10px 20px; cursor: pointer; }
            button:hover { background-color: #45a049; }
            .card-input { width: 40px; }
            .results { margin-top: 20px; padding: 15px; background-color: #222222; border-radius: 5px; border: 1px solid #444444; }
            .gto-decision { font-size: 20px; font-weight: bold; color: #00BFFF; }
            .metrics { margin-top: 10px; color: #cccccc; }
            .error { color: #ff6666; }
            .loading { color: #FFA500; }
            small { color: #aaaaaa; }
            h1 { color: #ffffff; }
        </style>
    </head>
    <body>
        <h1>🃏 GTO Testing Interface</h1>
        
        <form id="gtoForm">
            <div class="form-group">
                <label>Hero Cards:</label>
                <input type="text" id="hero1" class="card-input" placeholder="Ah" maxlength="2">
                <input type="text" id="hero2" class="card-input" placeholder="Kd" maxlength="2">
                <small>(e.g., Ah, Kd)</small>
            </div>
            
            <div class="form-group">
                <label>Board Cards:</label>
                <input type="text" id="board1" class="card-input" placeholder="" maxlength="2">
                <input type="text" id="board2" class="card-input" placeholder="" maxlength="2">
                <input type="text" id="board3" class="card-input" placeholder="" maxlength="2">
                <input type="text" id="board4" class="card-input" placeholder="" maxlength="2">
                <input type="text" id="board5" class="card-input" placeholder="" maxlength="2">
                <small>(leave empty for preflop)</small>
            </div>
            
            <div class="form-group">
                <label>Street:</label>
                <select id="street">
                    <option value="PREFLOP">Preflop</option>
                    <option value="FLOP">Flop</option>
                    <option value="TURN">Turn</option>
                    <option value="RIVER">River</option>
                </select>
            </div>
            
            <div class="form-group">
                <label>Pot Size: $</label>
                <input type="number" id="pot" value="1.5" step="0.01" min="0">
            </div>
            
            <div class="form-group">
                <label>To Call: $</label>
                <input type="number" id="toCall" value="0.5" step="0.01" min="0">
            </div>
            
            <div class="form-group">
                <label>Min Bet: $</label>
                <input type="number" id="minBet" value="1.0" step="0.01" min="0">
            </div>
            
            <div class="form-group">
                <label>Stakes - Small Blind: $</label>
                <input type="number" id="sb" value="0.5" step="0.01" min="0">
                <label>Big Blind: $</label>
                <input type="number" id="bb" value="1.0" step="0.01" min="0">
            </div>
            
            <div class="form-group">
                <label>Hero Stack: $</label>
                <input type="number" id="heroStack" value="100.0" step="0.01" min="0">
            </div>
            
            <div class="form-group">
                <label>Number of Opponents:</label>
                <input type="number" id="opponents" value="1" min="1" max="5">
            </div>
            
            <button type="submit">Get GTO Decision</button>
        </form>
        
        <div id="results" class="results" style="display: none;">
            <div id="gtoDecision" class="gto-decision"></div>
            <div id="metrics" class="metrics"></div>
        </div>
        
        <script>
            document.getElementById('gtoForm').addEventListener('submit', async function(e) {
                e.preventDefault();
                
                const resultsDiv = document.getElementById('results');
                const decisionDiv = document.getElementById('gtoDecision');
                const metricsDiv = document.getElementById('metrics');
                
                // Show loading
                resultsDiv.style.display = 'block';
                decisionDiv.innerHTML = '<span class="loading">Computing GTO decision...</span>';
                metricsDiv.innerHTML = '';
                
                try {
                    // Collect form data
                    const heroCards = [];
                    const hero1 = document.getElementById('hero1').value.trim().toLowerCase();
                    const hero2 = document.getElementById('hero2').value.trim().toLowerCase();
                    if (hero1) heroCards.push(hero1);
                    if (hero2) heroCards.push(hero2);
                    
                    const boardCards = [];
                    for (let i = 1; i <= 5; i++) {
                        const card = document.getElementById('board' + i).value.trim().toLowerCase();
                        if (card) boardCards.push(card);
                    }
                    
                    const tableState = {
                        table_id: 'gui_test_' + Date.now(),
                        street: document.getElementById('street').value,
                        board: boardCards,
                        hero_hole: heroCards,
                        pot: parseFloat(document.getElementById('pot').value),
                        to_call: parseFloat(document.getElementById('toCall').value),
                        bet_min: parseFloat(document.getElementById('minBet').value),
                        stakes: {
                            sb: parseFloat(document.getElementById('sb').value),
                            bb: parseFloat(document.getElementById('bb').value),
                            currency: 'USD'
                        },
                        hero_seat: 1,
                        max_seats: parseInt(document.getElementById('opponents').value) + 1,
                        seats: [
                            {
                                seat: 1,
                                name: 'Hero',
                                stack: parseFloat(document.getElementById('heroStack').value),
                                in_hand: true,
                                is_hero: true
                            }
                        ]
                    };
                    
                    // Add opponent seats
                    const numOpponents = parseInt(document.getElementById('opponents').value);
                    for (let i = 0; i < numOpponents; i++) {
                        tableState.seats.push({
                            seat: i + 2,
                            name: 'Opponent' + (i + 1),
                            stack: 100.0,
                            in_hand: true,
                            is_hero: false
                        });
                    }
                    
                    // Make API call
                    const response = await fetch('/decide', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'Authorization': 'Bearer test-token-123'
                        },
                        body: JSON.stringify(tableState)
                    });
                    
                    if (!response.ok) {
                        throw new Error('API request failed: ' + response.statusText);
                    }
                    
                    const result = await response.json();
                    
                    // Display results
                    decisionDiv.innerHTML = `🎯 ${result.decision.action} ${result.decision.size > 0 ? '$' + result.decision.size.toFixed(2) : ''}`;
                    
                    metricsDiv.innerHTML = `
                        <strong>Metrics:</strong><br>
                        • Equity: ${(result.metrics.equity * 100).toFixed(1)}%<br>
                        • Expected Value: $${result.metrics.ev.toFixed(2)}<br>
                        • Computation Time: ${result.computation_time_ms}ms<br>
                        • Strategy: ${result.strategy}<br>
                        • Exploitability: ${(result.metrics.exploitability * 100).toFixed(2)}%
                    `;
                    
                } catch (error) {
                    decisionDiv.innerHTML = '<span class="error">Error: ' + error.message + '</span>';
                    metricsDiv.innerHTML = '';
                }
            });
        </script>
    </body>
    </html>
    """
    return html_content


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    try:
        openspiel_available = gto_service is not None and gto_service.is_available()
        cfr_ready = gto_service is not None and gto_service.is_cfr_ready()
        
        return HealthResponse(
            ok=True,
            version=__version__,
            openspiel_available=openspiel_available,
            cfr_solver_ready=cfr_ready
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            ok=False,
            version=__version__,
            openspiel_available=False,
            cfr_solver_ready=False
        )


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
            f"Equity: {result.metrics.equity:.3f}, "
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
