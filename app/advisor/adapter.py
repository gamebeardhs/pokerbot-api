"""Table state adapter to convert JSON input to OpenSpiel game format."""

import logging
from typing import Dict, List, Optional, Tuple
from app.api.models import TableState, Seat

try:
    import pyspiel
    PYSPIEL_AVAILABLE = True
except ImportError:
    pyspiel = None
    PYSPIEL_AVAILABLE = False

logger = logging.getLogger(__name__)


class TableStateAdapter:
    """Adapts table state JSON to OpenSpiel game format."""
    
    CARD_MAPPING = {
        # Suits: h=hearts, d=diamonds, c=clubs, s=spades
        'h': 0, 'd': 1, 'c': 2, 's': 3,
        # Ranks: 2-9, T=10, J=11, Q=12, K=13, A=14
        '2': 0, '3': 1, '4': 2, '5': 3, '6': 4, '7': 5, '8': 6, '9': 7,
        't': 8, 'j': 9, 'q': 10, 'k': 11, 'a': 12
    }
    
    STREET_MAPPING = {
        "PREFLOP": 0,
        "FLOP": 1, 
        "TURN": 2,
        "RIVER": 3
    }
    
    def __init__(self):
        """Initialize adapter."""
        self.logger = logging.getLogger(__name__)
    
    def adapt_to_openspiel(self, state: TableState) -> Dict:
        """Convert TableState to OpenSpiel-compatible format."""
        if not PYSPIEL_AVAILABLE:
            # Return a basic format that can be used for mathematical approximations
            return self._adapt_to_basic_format(state)
        
        try:
            # Find hero and active players
            hero_seat = self._find_hero_seat(state)
            active_players = self._get_active_players(state)
            
            # Convert cards to OpenSpiel format
            hero_cards = self._convert_cards_to_openspiel(state.hero_hole or [])
            board_cards = self._convert_cards_to_openspiel(state.board)
            
            # Calculate pot sizes and betting info
            pot_info = self._calculate_pot_info(state)
            
            # Build game context
            game_context = {
                'game_type': 'no_limit_holdem',
                'num_players': len(active_players),
                'hero_position': self._get_hero_position(hero_seat, active_players),
                'street': self.STREET_MAPPING.get(state.street, 0),
                'hero_cards': hero_cards,
                'board_cards': board_cards,
                'pot_size': pot_info['total_pot'],
                'round_pot': pot_info['round_pot'],
                'to_call': state.to_call or 0,
                'min_bet': state.bet_min or state.stakes.bb,
                'big_blind': state.stakes.bb,
                'small_blind': state.stakes.sb,
                'stacks': self._get_player_stacks(active_players),
                'betting_history': self._construct_betting_history(state),
                'positions': self._assign_positions(active_players, state.max_seats)
            }
            
            return game_context
            
        except Exception as e:
            self.logger.error(f"Failed to adapt table state: {e}")
            return self._adapt_to_basic_format(state)
    
    def _find_hero_seat(self, state: TableState) -> Optional[int]:
        """Find hero's seat number."""
        if state.hero_seat:
            return state.hero_seat
            
        for seat in state.seats:
            if seat.is_hero:
                return seat.seat
                
        return None
    
    def _get_active_players(self, state: TableState) -> List[Seat]:
        """Get list of active players in the hand."""
        active = []
        for seat in state.seats:
            if seat.in_hand and seat.stack is not None and seat.stack > 0:
                active.append(seat)
        
        # Sort by seat number
        return sorted(active, key=lambda x: x.seat)
    
    def _convert_cards_to_openspiel(self, cards: List[str]) -> List[int]:
        """Convert card strings to OpenSpiel integer format."""
        if not cards:
            return []
            
        openspiel_cards = []
        for card_str in cards:
            if len(card_str) != 2:
                continue
                
            rank_char = card_str[0].lower()
            suit_char = card_str[1].lower()
            
            if rank_char in self.CARD_MAPPING and suit_char in self.CARD_MAPPING:
                # OpenSpiel card format: rank * 4 + suit
                rank = self.CARD_MAPPING[rank_char]
                suit = self.CARD_MAPPING[suit_char]
                card_id = rank * 4 + suit
                openspiel_cards.append(card_id)
        
        return openspiel_cards
    
    def _calculate_pot_info(self, state: TableState) -> Dict:
        """Calculate pot-related information."""
        total_pot = state.pot
        round_pot = state.round_pot or 0
        
        # If round pot not provided, estimate from player contributions
        if round_pot == 0:
            round_contributions = sum(seat.put_in or 0 for seat in state.seats if seat.put_in)
            round_pot = round_contributions
        
        return {
            'total_pot': total_pot,
            'round_pot': round_pot,
            'effective_pot': total_pot + round_pot
        }
    
    def _get_hero_position(self, hero_seat: Optional[int], active_players: List[Seat]) -> int:
        """Get hero's position relative to other active players."""
        if not hero_seat:
            return 0
            
        for i, player in enumerate(active_players):
            if player.seat == hero_seat:
                return i
        return 0
    
    def _get_player_stacks(self, active_players: List[Seat]) -> List[float]:
        """Get stack sizes for all active players."""
        return [player.stack or 0 for player in active_players]
    
    def _construct_betting_history(self, state: TableState) -> List[List[int]]:
        """Construct betting history for OpenSpiel."""
        # This is a simplified version - in a full implementation,
        # you would need to track actual betting actions
        num_players = len([s for s in state.seats if s.in_hand])
        history = []
        
        # Pre-flop blinds
        if state.street in ["PREFLOP", "FLOP", "TURN", "RIVER"]:
            preflop_actions = []
            for seat in state.seats:
                if seat.in_hand and seat.put_in:
                    # Simplified: assume put_in represents their total contribution
                    preflop_actions.append(int(seat.put_in * 100))  # Convert to cents
            history.append(preflop_actions)
        
        return history
    
    def _assign_positions(self, active_players: List[Seat], max_seats: int) -> Dict[int, str]:
        """Assign position names to seats."""
        positions = {}
        num_active = len(active_players)
        
        if num_active == 2:  # Heads-up
            positions[active_players[0].seat] = "SB"
            positions[active_players[1].seat] = "BB" 
        elif num_active <= 6:  # 6-max
            position_names = ["UTG", "MP", "CO", "BTN", "SB", "BB"]
            for i, player in enumerate(active_players):
                pos_idx = (i - num_active + len(position_names)) % len(position_names)
                positions[player.seat] = position_names[pos_idx]
        else:  # Full ring
            position_names = ["UTG", "UTG+1", "UTG+2", "MP", "MP+1", "LJ", "HJ", "CO", "BTN", "SB", "BB"]
            for i, player in enumerate(active_players):
                pos_idx = (i - num_active + len(position_names)) % len(position_names)
                positions[player.seat] = position_names[pos_idx]
                
        return positions
    
    def _adapt_to_basic_format(self, state: TableState) -> Dict:
        """Fallback format when OpenSpiel is not available."""
        return {
            'hero_cards': state.hero_hole or [],
            'board_cards': state.board,
            'pot_size': state.pot_size,
            'position': state.position,
            'street': state.street,
            'bet_to_call': getattr(state, 'bet_to_call', 0),
            'stack_size': getattr(state, 'effective_stack', 0),
            'num_players': len([s for s in state.seats if s.in_hand]),
            'openspiel_available': PYSPIEL_AVAILABLE
        }
