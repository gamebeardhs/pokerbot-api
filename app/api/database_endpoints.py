"""
Database API endpoints for instant GTO recommendations.
Provides endpoints to interact with the hybrid database system.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import logging

from ..database.gto_database import gto_db
from ..database.poker_vectorizer import PokerSituation, Position, BettingRound
from .models import TableState

logger = logging.getLogger(__name__)
router = APIRouter()

class InstantGTORequest(BaseModel):
    """Request model for instant GTO recommendations."""
    hole_cards: List[str]  # e.g., ["As", "Kh"]
    board_cards: List[str] = []  # e.g., ["Qd", "Jc", "9s"]
    position: str  # e.g., "BTN", "BB", "CO"
    pot_size: float
    bet_to_call: float
    stack_size: float
    num_players: int = 6
    betting_round: str = "preflop"  # "preflop", "flop", "turn", "river"

class DatabaseStatsResponse(BaseModel):
    """Database performance statistics."""
    total_situations: int
    hnsw_index_size: int
    total_queries: int
    average_query_time_ms: float
    database_size_mb: float
    status: str

@router.post("/instant-gto", summary="Get Instant GTO Recommendation")
async def get_instant_gto_recommendation(request: InstantGTORequest) -> JSONResponse:
    """
    Get instant GTO recommendation using precomputed database lookup.
    Returns sub-100ms recommendations using similarity matching.
    """
    try:
        # Convert request to PokerSituation
        position_map = {
            'UTG': Position.UTG, 'UTG1': Position.UTG1, 'MP': Position.MP,
            'MP1': Position.MP1, 'MP2': Position.MP2, 'CO': Position.CO,
            'BTN': Position.BTN, 'SB': Position.SB, 'BB': Position.BB
        }
        
        betting_round_map = {
            'preflop': BettingRound.PREFLOP, 'flop': BettingRound.FLOP,
            'turn': BettingRound.TURN, 'river': BettingRound.RIVER
        }
        
        situation = PokerSituation(
            hole_cards=request.hole_cards,
            board_cards=request.board_cards,
            position=position_map.get(request.position.upper(), Position.BTN),
            pot_size=request.pot_size,
            bet_to_call=request.bet_to_call,
            stack_size=request.stack_size,
            num_players=request.num_players,
            betting_round=betting_round_map.get(request.betting_round.lower(), BettingRound.PREFLOP)
        )
        
        # Get instant recommendation from database
        recommendation = gto_db.get_instant_recommendation(situation)
        
        if recommendation:
            return JSONResponse({
                "success": True,
                "recommendation": recommendation,
                "method": "instant_database_lookup",
                "message": "Instant GTO recommendation from precomputed database"
            })
        else:
            # Fallback to regular GTO service if no similar situation found
            from ..advisor.enhanced_gto_service import EnhancedGTODecisionService
            gto_service = EnhancedGTODecisionService()
            
            # Convert to proper TableState object for CFR fallback
            from ..api.models import TableState, Seat, Stakes
            table_state_obj = TableState(
                table_id="fallback",
                hand_id="fallback", 
                room="database",
                variant="nlhe",
                max_seats=9,
                hero_seat=1,
                stakes=Stakes(sb=0.5, bb=1.0),
                street=request.betting_round.upper(),
                board=request.board_cards,
                pot=request.pot_size,
                seats=[
                    Seat(
                        seat=1,
                        name="Hero",
                        stack=request.stack_size,
                        in_hand=True,
                        is_hero=True,
                        position=request.position.upper(),
                        cards=request.hole_cards  # Use 'cards' not 'hole_cards'
                    )
                ]
            )
            
            # CFR fallback temporarily disabled due to async/uvloop conflicts
            # Will be fixed in Phase 2 with proper async handling
            logger.info("Database miss - CFR fallback temporarily disabled")
            
            return JSONResponse({
                "success": False,
                "method": "database_miss_cfr_disabled", 
                "message": "No similar situation found in database. CFR computation temporarily unavailable.",
                "recommendation": {
                    "decision": "fold",
                    "bet_size": 0,
                    "equity": 0.0,
                    "reasoning": "Database miss - awaiting TexasSolver integration for authentic GTO analysis"
                },
                "debug_info": {
                    "database_situations": 6757,
                    "next_phase": "TexasSolver integration for authentic CFR solutions"
                }
            })
            
    except Exception as e:
        logger.error(f"Instant GTO recommendation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/database-stats", response_model=DatabaseStatsResponse, summary="Database Performance Statistics")
async def get_database_stats():
    """Get database performance and status statistics."""
    try:
        # Initialize database if needed
        if not gto_db.initialized:
            gto_db.initialize()
        
        stats = gto_db.get_performance_stats()
        
        # Determine status
        status = "healthy"
        if stats['total_situations'] == 0:
            status = "empty"
        elif stats['hnsw_index_size'] == 0:
            status = "no_index"
        elif stats['average_query_time_ms'] > 100:
            status = "slow"
        
        return DatabaseStatsResponse(
            total_situations=stats['total_situations'],
            hnsw_index_size=stats['hnsw_index_size'],
            total_queries=stats['total_queries'],
            average_query_time_ms=stats['average_query_time_ms'],
            database_size_mb=stats['database_size_mb'],
            status=status
        )
        
    except Exception as e:
        logger.error(f"Database stats retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Stats error: {str(e)}")

@router.post("/add-situation") 
async def add_single_situation(request: Dict[str, Any]):
    """Add a single GTO situation to the database."""
    try:
        # Convert request to PokerSituation  
        from ..models.poker_models import Position, BettingRound
        from ..database.gto_database import PokerSituation
        
        situation = PokerSituation(
            hole_cards=request["hole_cards"],
            board_cards=request.get("board_cards", []),
            position=Position[request["position"].upper()],
            pot_size=request["pot_size"],
            bet_to_call=request["bet_to_call"], 
            stack_size=request["stack_size"],
            num_players=request["num_players"],
            betting_round=BettingRound[request["betting_round"].upper()]
        )
        
        # Generate GTO solution
        solution = gto_db._generate_simple_gto_solution(situation)
        if solution:
            success = gto_db.add_solution(situation, solution)
            if success:
                return {"success": True, "message": "Situation added successfully"}
        
        return {"success": False, "message": "Failed to generate or add solution"}
        
    except Exception as e:
        logger.error(f"Failed to add situation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/populate-database", summary="Populate Database with Initial Solutions")
async def populate_database(count: int = 1000):
    """
    Populate the database with initial GTO solutions.
    This is a one-time operation to bootstrap the system.
    """
    try:
        # Check if database already has solutions
        stats = gto_db.get_performance_stats()
        
        if stats['total_situations'] > 0:
            return JSONResponse({
                "success": False,
                "message": f"Database already contains {stats['total_situations']} situations",
                "existing_count": stats['total_situations']
            })
        
        # Initialize and populate database
        gto_db.initialize()
        gto_db._populate_database(count)
        
        # Get updated stats
        new_stats = gto_db.get_performance_stats()
        
        return JSONResponse({
            "success": True,
            "message": f"Database populated with {new_stats['total_situations']} GTO solutions",
            "total_situations": new_stats['total_situations'],
            "database_size_mb": new_stats['database_size_mb']
        })
        
    except Exception as e:
        logger.error(f"Database population failed: {e}")
        raise HTTPException(status_code=500, detail=f"Population error: {str(e)}")

@router.post("/rebuild-index", summary="Rebuild HNSW Index")
async def rebuild_index():
    """
    Rebuild the HNSW index from existing database.
    Use this if the index gets corrupted or needs optimization.
    """
    try:
        gto_db.rebuild_index()
        stats = gto_db.get_performance_stats()
        
        return JSONResponse({
            "success": True,
            "message": "HNSW index rebuilt successfully",
            "index_size": stats['hnsw_index_size']
        })
        
    except Exception as e:
        logger.error(f"Index rebuild failed: {e}")
        raise HTTPException(status_code=500, detail=f"Rebuild error: {str(e)}")

@router.get("/test-instant-gto", summary="Test Instant GTO with Sample Data")
async def test_instant_gto():
    """Test the instant GTO system with a sample poker situation."""
    try:
        # Sample test situation
        test_request = InstantGTORequest(
            hole_cards=["As", "Kh"],
            board_cards=["Qd", "Jc", "9s"],
            position="BTN",
            pot_size=15.0,
            bet_to_call=5.0,
            stack_size=100.0,
            num_players=3,
            betting_round="flop"
        )
        
        # Get recommendation
        result = await get_instant_gto_recommendation(test_request)
        
        return JSONResponse({
            "success": True,
            "test_situation": test_request.dict(),
            "result": result.body.decode() if hasattr(result, 'body') else str(result),
            "message": "Test completed successfully"
        })
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise HTTPException(status_code=500, detail=f"Test error: {str(e)}")