"""Pydantic models for request/response validation."""

from typing import List, Optional, Literal, Dict, Any, Union
from pydantic import BaseModel, validator, Field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class Stakes(BaseModel):
    """Poker stakes definition."""
    sb: float
    bb: float
    currency: str = "USD"


class Position(str, Enum):
    """Standard poker positions."""
    UTG = "UTG"
    UTG1 = "UTG+1"
    UTG2 = "UTG+2"
    MP = "MP"
    MP1 = "MP+1"
    LJ = "LJ"
    HJ = "HJ"
    CO = "CO"
    BTN = "BTN"
    SB = "SB"
    BB = "BB"


class ActionType(str, Enum):
    """Poker action types."""
    FOLD = "fold"
    CHECK = "check"
    CALL = "call"
    BET = "bet"
    RAISE = "raise"
    ALL_IN = "all_in"


class BettingAction(BaseModel):
    """Individual betting action."""
    seat: int
    action: ActionType
    amount: float = 0.0
    total_committed: float = 0.0  # Total amount player has put in this street
    is_all_in: bool = False
    timestamp: Optional[str] = None


class PlayerStats(BaseModel):
    """Player statistics for opponent modeling."""
    hands_observed: int = 0
    vpip: float = 0.0  # Voluntarily put money in pot %
    pfr: float = 0.0   # Pre-flop raise %
    three_bet: float = 0.0  # 3-bet %
    cbet_flop: float = 0.0  # Continuation bet flop %
    cbet_turn: float = 0.0  # Continuation bet turn %
    fold_to_cbet: float = 0.0  # Fold to c-bet %
    aggression_factor: float = 1.0  # (Bet + Raise) / Call
    wtsd: float = 0.0  # Went to showdown %
    w_wsf: float = 0.0  # Won when saw flop %
    

class Seat(BaseModel):
    """Enhanced player seat information."""
    seat: int
    name: Optional[str] = None
    stack: Optional[float] = None
    in_hand: Optional[bool] = None
    acted: Optional[bool] = None
    put_in: Optional[float] = None  # Amount put in this street
    total_invested: Optional[float] = None  # Total invested this hand
    is_hero: Optional[bool] = None
    position: Optional[Position] = None
    stats: Optional[PlayerStats] = None
    is_all_in: bool = False
    stack_bb: Optional[float] = None  # Stack in big blinds
    
    @validator("stack_bb", always=True)
    def calculate_stack_bb(cls, v, values):
        """Calculate stack in big blinds."""
        if v is not None:
            return v
        stack = values.get("stack")
        # We'll calculate this when we have stakes info
        return None


class BoardTexture(BaseModel):
    """Board texture analysis for GTO decisions."""
    paired: bool = False
    trips: bool = False
    quads: bool = False
    flush_possible: bool = False
    straight_possible: bool = False
    wetness_score: float = 0.0  # 0-1, higher = wetter
    connectivity_score: float = 0.0  # 0-1, higher = more connected
    high_card_score: float = 0.0  # 0-1, higher = more high cards
    draw_heavy: bool = False
    

class RangeInfo(BaseModel):
    """Player range information."""
    seat: int
    position: Position
    preflop_range: List[str] = []  # Hand combinations like ["AA", "KK", "AKs"]
    current_range: List[str] = []  # Range after actions on current street
    range_equity: float = 0.0  # Equity vs hero's range
    range_strength: float = 0.0  # Overall range strength
    

class StreetAction(BaseModel):
    """Complete action sequence for a street."""
    street: Literal["PREFLOP", "FLOP", "TURN", "RIVER"]
    actions: List[BettingAction] = []
    pot_size_start: float = 0.0
    pot_size_end: float = 0.0
    aggressor_seat: Optional[int] = None  # Last player to bet/raise
    action_type: Optional[Literal["open", "call", "raise", "3bet", "4bet", "5bet", "shove"]] = None
    aggressor_position: Optional[Position] = None  # Position of last aggressor
    

class TableState(BaseModel):
    """Complete table state for advanced GTO decision making."""
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
    
    # Enhanced GTO-specific fields
    betting_history: List[StreetAction] = []  # Complete betting history
    board_texture: Optional[BoardTexture] = None
    player_ranges: List[RangeInfo] = []  # Estimated ranges for all players
    effective_stacks: Dict[int, float] = {}  # Effective stack vs each opponent
    spr: Optional[float] = None  # Stack-to-pot ratio
    button_seat: Optional[int] = None  # Position of button
    sb_seat: Optional[int] = None
    bb_seat: Optional[int] = None
    rake_cap: Optional[float] = None
    rake_percentage: Optional[float] = None
    
    # Action context for decision making
    current_aggressor_seat: Optional[int] = None  # Seat of player who made current bet
    current_action_type: Optional[Literal["open", "call", "raise", "3bet", "4bet", "5bet", "shove"]] = None
    hero_position_vs_aggressor: Optional[Literal["in_position", "out_of_position", "heads_up"]] = None
    num_raises_this_street: int = 0  # Number of raises on current street

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
    """Enhanced GTO decision recommendation."""
    action: Literal["Fold", "Check", "Call", "Bet", "BetPlus", "All-in"]
    size: float = 0.0  # Bet/raise size (absolute amount)
    size_bb: float = 0.0  # Size in big blinds
    size_pot_fraction: float = 0.0  # Size as fraction of pot
    confidence: float = 0.0  # Decision confidence (0-1)
    frequency: float = 0.0  # How often to take this action in GTO
    alternative_actions: List[Dict[str, Any]] = []  # Other viable actions with frequencies
    reasoning: str = ""  # Brief explanation of decision
    

class EquityBreakdown(BaseModel):
    """Detailed equity analysis."""
    raw_equity: float  # Pure hand strength equity
    fold_equity: float  # Equity from opponent folds
    realize_equity: float  # Adjusted for positional disadvantage
    vs_calling_range: float  # Equity vs range that calls
    vs_folding_range: float  # Equity vs range that folds
    draw_equity: float = 0.0  # Additional equity from draws


class GTOMetrics(BaseModel):
    """Comprehensive GTO analysis metrics."""
    equity_breakdown: EquityBreakdown
    min_call: float  # Minimum amount to call
    min_bet: float  # Minimum bet size
    pot: float  # Current pot size
    players: int  # Number of active players
    ev: Optional[float] = None  # Expected value of recommended action
    exploitability: Optional[float] = None  # Nash distance metric
    
    # Stack and pot considerations
    spr: float  # Stack-to-pot ratio
    effective_stack: float  # Effective stack vs closest opponent
    pot_odds: float  # Current pot odds if facing bet
    
    # Range vs range metrics
    range_advantage: float  # Our range strength vs opponent range
    nut_advantage: float  # Advantage in strongest hands
    bluff_catchers: float  # Portion of range that's bluff catchers
    
    # Board and position
    board_favorability: float  # How much board favors our range
    positional_advantage: float  # Positional edge (-1 to 1)
    initiative: bool  # Whether we have betting lead
    
    # Multi-street considerations  
    commitment_threshold: float  # Stack size where we're committed
    reverse_implied_odds: float  # Risk of losing more on later streets
    
    # Opponent modeling
    opponent_tendencies: Dict[int, Dict[str, float]] = {}  # Exploitative adjustments


class GTOResponse(BaseModel):
    """Enhanced response from GTO decision endpoint."""
    ok: bool = True
    decision: GTODecision
    metrics: GTOMetrics
    strategy: str
    computation_time_ms: Optional[int] = None
    
    # Multi-street planning
    game_plan: Dict[str, Any] = {}  # Strategy for future streets
    decision_tree: Optional[Dict[str, Any]] = None  # Simplified game tree
    
    # Exploitative elements
    exploitative_adjustments: List[str] = []  # List of adjustments made
    gto_baseline: Optional[GTODecision] = None  # Pure GTO decision for comparison


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
