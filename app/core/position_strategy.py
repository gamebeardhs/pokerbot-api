"""Position-aware strategy for GTO decision making."""

import logging
from typing import Dict, List, Optional, Tuple
from app.api.models import Position, TableState, BettingAction
from app.core.range_analyzer import RangeAnalyzer
from app.core.board_analyzer import BoardAnalyzer

logger = logging.getLogger(__name__)


class PositionStrategy:
    """Implements position-aware poker strategy."""
    
    def __init__(self):
        """Initialize position strategy."""
        self.range_analyzer = RangeAnalyzer()
        self.board_analyzer = BoardAnalyzer()
        
        # Position-based strategy adjustments
        self.position_factors = {
            Position.UTG: {
                "tightness": 0.9,      # Very tight
                "aggression": 0.6,     # Conservative aggression
                "bluff_frequency": 0.2, # Low bluff frequency
                "value_threshold": 0.7  # High value threshold
            },
            Position.UTG1: {
                "tightness": 0.85,
                "aggression": 0.65,
                "bluff_frequency": 0.25,
                "value_threshold": 0.68
            },
            Position.MP: {
                "tightness": 0.8,
                "aggression": 0.7,
                "bluff_frequency": 0.3,
                "value_threshold": 0.65
            },
            Position.LJ: {
                "tightness": 0.75,
                "aggression": 0.75,
                "bluff_frequency": 0.35,
                "value_threshold": 0.62
            },
            Position.HJ: {
                "tightness": 0.7,
                "aggression": 0.8,
                "bluff_frequency": 0.4,
                "value_threshold": 0.6
            },
            Position.CO: {
                "tightness": 0.65,
                "aggression": 0.85,
                "bluff_frequency": 0.45,
                "value_threshold": 0.58
            },
            Position.BTN: {
                "tightness": 0.5,      # Very wide
                "aggression": 0.9,     # Very aggressive
                "bluff_frequency": 0.5, # High bluff frequency
                "value_threshold": 0.55 # Low value threshold
            },
            Position.SB: {
                "tightness": 0.6,
                "aggression": 0.75,
                "bluff_frequency": 0.4,
                "value_threshold": 0.6
            },
            Position.BB: {
                "tightness": 0.55,     # Wide defending range
                "aggression": 0.7,
                "bluff_frequency": 0.35,
                "value_threshold": 0.58
            }
        }
    
    def get_position_adjustment(self, hero_position: Position, 
                               aggressor_position: Optional[Position],
                               num_players: int) -> Dict[str, float]:
        """
        Get positional adjustments for strategy.
        
        Args:
            hero_position: Hero's position
            aggressor_position: Position of last aggressor (if any)
            num_players: Number of active players
            
        Returns:
            Dictionary of strategy adjustments
        """
        base_factors = self.position_factors.get(hero_position, {
            "tightness": 0.7,
            "aggression": 0.7,
            "bluff_frequency": 0.3,
            "value_threshold": 0.6
        })
        
        adjustments = base_factors.copy()
        
        # Adjust for relative position to aggressor
        if aggressor_position:
            relative_position = self._get_relative_position(hero_position, aggressor_position)
            
            if relative_position == "in_position":
                adjustments["aggression"] *= 1.2
                adjustments["bluff_frequency"] *= 1.3
                adjustments["value_threshold"] *= 0.95
            elif relative_position == "out_of_position":
                adjustments["aggression"] *= 0.85
                adjustments["bluff_frequency"] *= 0.7
                adjustments["value_threshold"] *= 1.1
                adjustments["tightness"] *= 1.1
        
        # Adjust for number of players
        if num_players <= 3:  # Short-handed
            adjustments["tightness"] *= 0.8
            adjustments["aggression"] *= 1.2
            adjustments["bluff_frequency"] *= 1.3
        elif num_players >= 6:  # Full ring
            adjustments["tightness"] *= 1.2
            adjustments["aggression"] *= 0.9
            adjustments["bluff_frequency"] *= 0.8
        
        # Clamp values to reasonable ranges
        for key in adjustments:
            adjustments[key] = max(0.1, min(1.5, adjustments[key]))
        
        return adjustments
    
    def _get_relative_position(self, hero_pos: Position, aggressor_pos: Position) -> str:
        """Determine if hero is in position relative to aggressor."""
        position_order = [
            Position.SB, Position.BB, Position.UTG, Position.UTG1, Position.UTG2,
            Position.MP, Position.MP1, Position.LJ, Position.HJ, Position.CO, Position.BTN
        ]
        
        try:
            hero_idx = position_order.index(hero_pos)
            agg_idx = position_order.index(aggressor_pos)
            
            # Special case for blinds
            if hero_pos == Position.SB and aggressor_pos == Position.BTN:
                return "out_of_position"
            if hero_pos == Position.BB and aggressor_pos in [Position.BTN, Position.SB]:
                return "out_of_position"
            
            # General case: later position = in position
            if hero_idx > agg_idx:
                return "in_position"
            elif hero_idx < agg_idx:
                return "out_of_position"
            else:
                return "same_position"
                
        except ValueError:
            return "unknown"
    
    def calculate_positional_equity_adjustment(self, hero_position: Position,
                                             opponents: List[Position],
                                             board: List[str]) -> float:
        """
        Calculate equity adjustment based on positional factors.
        
        Args:
            hero_position: Hero's position
            opponents: List of opponent positions
            board: Board cards
            
        Returns:
            Equity multiplier (0.8 - 1.2)
        """
        base_multiplier = 1.0
        
        # Position strength relative to field
        position_strength = self._calculate_position_strength(hero_position, opponents)
        
        # Board texture interaction with position
        board_category = self.board_analyzer.get_board_category(board)
        board_interaction = self._get_board_position_interaction(hero_position, board_category)
        
        # Initiative factor
        initiative_factor = self._get_initiative_factor(hero_position, opponents)
        
        # Combine factors
        multiplier = (position_strength * 0.4 + 
                     board_interaction * 0.3 + 
                     initiative_factor * 0.3)
        
        # Clamp to reasonable range
        return max(0.8, min(1.2, multiplier))
    
    def _calculate_position_strength(self, hero_position: Position, 
                                   opponents: List[Position]) -> float:
        """Calculate relative position strength."""
        position_values = {
            Position.UTG: 0.2, Position.UTG1: 0.3, Position.UTG2: 0.35,
            Position.MP: 0.4, Position.MP1: 0.45, Position.LJ: 0.5,
            Position.HJ: 0.6, Position.CO: 0.8, Position.BTN: 1.0,
            Position.SB: 0.3, Position.BB: 0.35
        }
        
        hero_value = position_values.get(hero_position, 0.5)
        
        # Adjust based on opponents' positions
        opp_values = [position_values.get(pos, 0.5) for pos in opponents]
        avg_opp_value = sum(opp_values) / len(opp_values) if opp_values else 0.5
        
        # Relative strength
        if avg_opp_value > 0:
            relative_strength = hero_value / avg_opp_value
        else:
            relative_strength = 1.0
        
        return max(0.5, min(1.5, relative_strength))
    
    def _get_board_position_interaction(self, position: Position, 
                                       board_category: str) -> float:
        """Get board texture interaction with position."""
        interactions = {
            # Position benefits on different board types
            Position.BTN: {
                "dry": 1.2, "wet": 1.1, "paired": 1.15, "monotone": 1.0,
                "connected": 1.1, "high_card": 1.2
            },
            Position.CO: {
                "dry": 1.15, "wet": 1.05, "paired": 1.1, "monotone": 0.95,
                "connected": 1.05, "high_card": 1.15
            },
            Position.HJ: {
                "dry": 1.1, "wet": 1.0, "paired": 1.05, "monotone": 0.9,
                "connected": 1.0, "high_card": 1.1
            },
            Position.UTG: {
                "dry": 0.9, "wet": 0.85, "paired": 0.9, "monotone": 0.8,
                "connected": 0.85, "high_card": 0.95
            },
            Position.BB: {
                "dry": 0.95, "wet": 0.9, "paired": 0.95, "monotone": 0.85,
                "connected": 0.9, "high_card": 1.0
            }
        }
        
        default_interaction = {
            "dry": 1.0, "wet": 0.95, "paired": 1.0, "monotone": 0.9,
            "connected": 0.95, "high_card": 1.05
        }
        
        position_interactions = interactions.get(position, default_interaction)
        return position_interactions.get(board_category, 1.0)
    
    def _get_initiative_factor(self, hero_position: Position, 
                              opponents: List[Position]) -> float:
        """Calculate initiative factor based on position."""
        # Late position generally has more initiative
        initiative_values = {
            Position.BTN: 1.2, Position.CO: 1.1, Position.HJ: 1.05,
            Position.LJ: 1.0, Position.MP: 0.95, Position.MP1: 0.95,
            Position.UTG2: 0.9, Position.UTG1: 0.85, Position.UTG: 0.8,
            Position.SB: 0.9, Position.BB: 0.85
        }
        
        return initiative_values.get(hero_position, 1.0)
    
    def get_betting_size_adjustment(self, hero_position: Position,
                                   board_category: str,
                                   action_type: str) -> float:
        """
        Get betting size adjustment based on position and board.
        
        Args:
            hero_position: Hero's position
            board_category: Type of board texture
            action_type: Type of action (bet, raise, etc.)
            
        Returns:
            Size multiplier for base bet sizing
        """
        base_adjustments = {
            # Position-based size adjustments
            Position.BTN: {"bet": 1.1, "raise": 1.2, "bluff": 1.3},
            Position.CO: {"bet": 1.05, "raise": 1.1, "bluff": 1.2},
            Position.HJ: {"bet": 1.0, "raise": 1.05, "bluff": 1.1},
            Position.UTG: {"bet": 0.9, "raise": 0.95, "bluff": 0.8},
            Position.BB: {"bet": 0.95, "raise": 1.0, "bluff": 0.9}
        }
        
        board_adjustments = {
            # Board-based size adjustments
            "dry": {"bet": 0.8, "raise": 0.9, "bluff": 1.2},
            "wet": {"bet": 1.2, "raise": 1.1, "bluff": 0.9},
            "paired": {"bet": 1.0, "raise": 1.0, "bluff": 1.1},
            "monotone": {"bet": 1.1, "raise": 1.0, "bluff": 0.8}
        }
        
        # Get adjustments
        pos_adj = base_adjustments.get(hero_position, {"bet": 1.0, "raise": 1.0, "bluff": 1.0})
        board_adj = board_adjustments.get(board_category, {"bet": 1.0, "raise": 1.0, "bluff": 1.0})
        
        position_mult = pos_adj.get(action_type, 1.0)
        board_mult = board_adj.get(action_type, 1.0)
        
        # Combine multiplicatively
        final_mult = position_mult * board_mult
        
        return max(0.5, min(2.0, final_mult))
    
    def should_take_initiative(self, hero_position: Position,
                              action_sequence: List[BettingAction],
                              board_category: str) -> float:
        """
        Calculate probability of taking initiative.
        
        Returns:
            Probability (0-1) of taking aggressive action
        """
        # Base initiative tendency by position
        base_initiative = {
            Position.BTN: 0.8, Position.CO: 0.75, Position.HJ: 0.7,
            Position.LJ: 0.65, Position.MP: 0.6, Position.MP1: 0.6,
            Position.UTG2: 0.5, Position.UTG1: 0.45, Position.UTG: 0.4,
            Position.SB: 0.55, Position.BB: 0.5
        }
        
        initiative = base_initiative.get(hero_position, 0.6)
        
        # Adjust based on previous actions
        if action_sequence:
            last_action = action_sequence[-1]
            if last_action.action in ["bet", "raise"]:
                initiative *= 0.7  # Less likely to re-raise
            elif last_action.action == "check":
                initiative *= 1.3  # More likely to bet after check
        
        # Adjust based on board texture
        board_initiative_adj = {
            "dry": 1.2,        # More initiative on dry boards
            "wet": 0.8,        # Less initiative on wet boards
            "paired": 1.0,     # Neutral on paired boards
            "monotone": 0.9,   # Slightly less on monotone
            "connected": 0.85  # Less on connected boards
        }
        
        initiative *= board_initiative_adj.get(board_category, 1.0)
        
        return max(0.1, min(0.9, initiative))
    
    def get_range_width_adjustment(self, hero_position: Position,
                                  street: str,
                                  num_opponents: int) -> float:
        """
        Get range width adjustment for position and street.
        
        Returns:
            Multiplier for base range width
        """
        # Base range width by position
        base_width = {
            Position.UTG: 0.6, Position.UTG1: 0.7, Position.UTG2: 0.75,
            Position.MP: 0.8, Position.MP1: 0.85, Position.LJ: 0.9,
            Position.HJ: 1.0, Position.CO: 1.2, Position.BTN: 1.4,
            Position.SB: 1.1, Position.BB: 1.3
        }
        
        width = base_width.get(hero_position, 1.0)
        
        # Adjust for street (tighten on later streets)
        street_adjustment = {
            "PREFLOP": 1.0,
            "FLOP": 0.8,
            "TURN": 0.6,
            "RIVER": 0.5
        }
        
        width *= street_adjustment.get(street, 1.0)
        
        # Adjust for number of opponents (tighten with more opponents)
        if num_opponents >= 3:
            width *= 0.8
        elif num_opponents >= 5:
            width *= 0.6
        
        return max(0.3, min(2.0, width))