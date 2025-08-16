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
import uvicorn

from app.api.models import (
    TableState, GTOResponse, HealthResponse, StateResponse, 
    StateHistoryResponse, ErrorResponse
)
from app.advisor.gto_service import GTODecisionService
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

# Initialize GTO service
try:
    gto_service = GTODecisionService()
    logger.info("GTO Decision Service initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize GTO service: {e}")
    gto_service = None


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
            "docs": "/docs"
        }
    }


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


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "app.api.main:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level=log_level.lower()
    )
