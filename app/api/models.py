"""Pydantic models for request/response validation."""

from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, validator
import logging

logger = logging.getLogger(__name__)


class Stakes(BaseModel):
    """Poker stakes definition."""
    sb: float
    bb: float
    currency: str = "USD"


class Seat(BaseModel):
    """Player seat information."""
    seat: int
    name: Optional[str] = None
    stack: Optional[float] = None
    in_hand: Optional[bool] = None
    acted: Optional[bool] = None
    put_in: Optional[float] = None
    is_hero: Optional[bool] = None
    position: Optional[str] = None  # UTG/HJ/CO/BTN/SB/BB


class TableState(BaseModel):
    """Complete table state for GTO decision making."""
    table_id: str
    hand_id: Optional[str] = None
    room: Optional[str] = None
    variant: str = "NLHE"
    max_seats: int = 6
    hero_seat: Optional[int] = None
    stakes: Stakes
    street: Literal["PREFLOP", "FLOP", "TURN", "RIVER", "SHOWDOWN"]
    board: List[str] = []  # ["7h", "2s", "2d"]
    hero_hole: Optional[List[str]] = None  # ["ah", "qs"]
    pot: float
    round_pot: Optional[float] = None
    to_call: Optional[float] = None
    bet_min: Optional[float] = None
    seats: List[Seat]
    action_clock_ms: Optional[int] = None
    timestamp: Optional[str] = None

    @validator("board", "hero_hole", pre=True)
    def _lower_cards(cls, v):
        """Normalize card notation to lowercase."""
        if v is None:
            return v
        return [c.lower() for c in v]

    @validator("hero_hole")
    def _validate_hero_cards(cls, v):
        """Validate hero cards are provided for decision making."""
        if v is None:
            logger.warning("Hero hole cards not provided - decision quality may be limited")
        return v


class GTODecision(BaseModel):
    """GTO decision recommendation."""
    action: Literal["Fold", "Check", "Call", "Bet", "BetPlus"]
    size: float = 0.0  # Bet/raise size as fraction of pot or absolute amount


class GTOMetrics(BaseModel):
    """Key metrics from GTO analysis."""
    equity: float  # Hero's equity against opponent ranges
    min_call: float  # Minimum amount to call
    min_bet: float  # Minimum bet size
    pot: float  # Current pot size
    players: int  # Number of active players
    ev: Optional[float] = None  # Expected value of recommended action
    exploitability: Optional[float] = None  # Nash distance metric


class GTOResponse(BaseModel):
    """Response from GTO decision endpoint."""
    ok: bool = True
    decision: GTODecision
    metrics: GTOMetrics
    strategy: str
    computation_time_ms: Optional[int] = None


class HealthResponse(BaseModel):
    """Health check response."""
    ok: bool = True
    version: str
    openspiel_available: bool = True
    cfr_solver_ready: bool = True


class StateResponse(BaseModel):
    """State retrieval response."""
    ok: bool = True
    data: Optional[TableState] = None
    timestamp: Optional[str] = None


class StateHistoryResponse(BaseModel):
    """State history response."""
    ok: bool = True
    data: List[Dict[str, Any]]
    count: int


class ErrorResponse(BaseModel):
    """Error response format."""
    ok: bool = False
    error: str
    details: Optional[Dict[str, Any]] = None
