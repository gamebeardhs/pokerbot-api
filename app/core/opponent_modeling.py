"""Opponent modeling and exploitation for GTO+ strategy."""

import logging
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict, deque
from dataclasses import dataclass
from app.api.models import PlayerStats, BettingAction, Position, TableState

logger = logging.getLogger(__name__)


@dataclass
class HandHistory:
    """Single hand history for analysis."""
    hand_id: str
    position: Position
    preflop_action: str
    flop_action: Optional[str] = None
    turn_action: Optional[str] = None
    river_action: Optional[str] = None
    showdown_hand: Optional[str] = None
    vpip: bool = False
    pfr: bool = False
    three_bet: bool = False
    c_bet: bool = False
    fold_to_c_bet: bool = False
    went_to_showdown: bool = False
    won_at_showdown: bool = False


class OpponentModeling:
    """Tracks opponent tendencies and suggests exploitative adjustments."""
    
    def __init__(self, max_history_per_player: int = 100):
        """Initialize opponent modeling system."""
        self.max_history = max_history_per_player
        
        # Player databases
        self.player_stats: Dict[str, PlayerStats] = {}
        self.hand_histories: Dict[str, deque] = defaultdict(lambda: deque(maxlen=self.max_history))
        self.recent_actions: Dict[str, List[BettingAction]] = defaultdict(list)
        
        # Dynamic adjustments
        self.exploit_thresholds = {
            "vpip_tight": 15.0,      # VPIP below this = tight
            "vpip_loose": 35.0,      # VPIP above this = loose
            "pfr_passive": 8.0,      # PFR below this = passive
            "pfr_aggressive": 20.0,  # PFR above this = aggressive
            "three_bet_low": 2.0,    # 3-bet below this = weak
            "three_bet_high": 8.0,   # 3-bet above this = aggressive
            "cbet_low": 40.0,        # C-bet below this = weak
            "cbet_high": 80.0,       # C-bet above this = aggressive
            "fold_to_cbet_high": 70.0  # Fold to c-bet above this = weak
        }
    
    def update_player_action(self, player_name: str, action: BettingAction,
                           position: Position, street: str, 
                           board: Optional[List[str]] = None) -> None:
        """
        Update player statistics with new action.
        
        Args:
            player_name: Player identifier
            action: Betting action taken
            position: Player's position
            street: Current street
            board: Board cards (if applicable)
        """
        try:
            # Initialize player if new
            if player_name not in self.player_stats:
                self.player_stats[player_name] = PlayerStats()
            
            stats = self.player_stats[player_name]
            stats.hands_observed += 1
            
            # Track recent actions
            self.recent_actions[player_name].append(action)
            if len(self.recent_actions[player_name]) > 20:  # Keep last 20 actions
                self.recent_actions[player_name].pop(0)
            
            # Update street-specific stats
            if street == "PREFLOP":
                self._update_preflop_stats(stats, action)
            elif street == "FLOP":
                self._update_flop_stats(stats, action, board)
            elif street in ["TURN", "RIVER"]:
                self._update_later_street_stats(stats, action, street)
            
            # Calculate derived statistics
            self._recalculate_derived_stats(stats)
            
        except Exception as e:
            logger.error(f"Failed to update player action: {e}")
    
    def _update_preflop_stats(self, stats: PlayerStats, action: BettingAction) -> None:
        """Update preflop statistics."""
        # Find the player name for this stats object
        current_player_name = None
        for name, stat_obj in self.player_stats.items():
            if stat_obj is stats:
                current_player_name = name
                break
        
        if not current_player_name:
            return  # Can't update without player name
            
        if action.action in ["call", "bet", "raise"]:
            # VPIP - voluntarily put money in pot
            vpip_count = sum(1 for hand in self.hand_histories.get(current_player_name, []) 
                           if getattr(hand, 'vpip', False))
            stats.vpip = (vpip_count + 1) / stats.hands_observed * 100
            
            if action.action in ["bet", "raise"]:
                # PFR - preflop raise
                pfr_count = sum(1 for hand in self.hand_histories.get(current_player_name, [])
                              if getattr(hand, 'pfr', False))
                stats.pfr = (pfr_count + 1) / stats.hands_observed * 100
                
                # Check for 3-bet (simplified detection)
                if action.amount > action.total_committed * 2:  # Rough 3-bet detection
                    three_bet_count = sum(1 for hand in self.hand_histories.get(current_player_name, [])
                                        if getattr(hand, 'three_bet', False))
                    stats.three_bet = (three_bet_count + 1) / stats.hands_observed * 100
    
    def _update_flop_stats(self, stats: PlayerStats, action: BettingAction, 
                          board: Optional[List[str]]) -> None:
        """Update flop statistics."""
        # Get player name for this stats object
        current_player_name = None
        for name, stat_obj in self.player_stats.items():
            if stat_obj is stats:
                current_player_name = name
                break
        
        if not current_player_name:
            return  # Can't update without player name
            
        if action.action in ["bet", "raise"]:
            # C-bet detection (simplified - assumes first aggressive action is c-bet)
            cbet_count = sum(1 for hand in self.hand_histories.get(current_player_name, [])
                           if getattr(hand, 'c_bet', False))
            stats.cbet_flop = (cbet_count + 1) / max(1, stats.hands_observed) * 100
        
        elif action.action == "fold":
            # Fold to c-bet (simplified detection)
            fold_count = sum(1 for hand in self.hand_histories.get(current_player_name, [])
                           if getattr(hand, 'fold_to_c_bet', False))
            stats.fold_to_cbet = (fold_count + 1) / max(1, stats.hands_observed) * 100
    
    def _update_later_street_stats(self, stats: PlayerStats, action: BettingAction, 
                                  street: str) -> None:
        """Update turn/river statistics."""
        # Get player name for this stats object
        current_player_name = None
        for name, stat_obj in self.player_stats.items():
            if stat_obj is stats:
                current_player_name = name
                break
        
        if current_player_name and street == "TURN" and action.action in ["bet", "raise"]:
            cbet_count = sum(1 for hand in self.hand_histories.get(current_player_name, [])
                           if getattr(hand, 'c_bet', False))
            stats.cbet_turn = (cbet_count + 1) / max(1, stats.hands_observed) * 100
    
    def _recalculate_derived_stats(self, stats: PlayerStats) -> None:
        """Recalculate derived statistics."""
        # Aggression factor: (Bet + Raise) / Call
        # Get player name for this stats object
        current_player_name = None
        for name, stat_obj in self.player_stats.items():
            if stat_obj is stats:
                current_player_name = name
                break
        
        recent_actions = self.recent_actions.get(current_player_name, []) if current_player_name else []
        if recent_actions:
            aggressive_actions = sum(1 for a in recent_actions 
                                   if a.action in ["bet", "raise"])
            passive_actions = sum(1 for a in recent_actions 
                                if a.action == "call")
            
            if passive_actions > 0:
                stats.aggression_factor = aggressive_actions / passive_actions
            else:
                stats.aggression_factor = aggressive_actions
    
    def get_player_type(self, player_name: str) -> str:
        """
        Classify player type based on statistics.
        
        Returns:
            Player type like 'TAG', 'LAG', 'tight_passive', etc.
        """
        if player_name not in self.player_stats:
            return "unknown"
        
        stats = self.player_stats[player_name]
        
        # Not enough data
        if stats.hands_observed < 20:
            return "insufficient_data"
        
        # Classify based on VPIP and PFR
        vpip = stats.vpip
        pfr = stats.pfr
        
        if vpip < self.exploit_thresholds["vpip_tight"]:
            if pfr < self.exploit_thresholds["pfr_passive"]:
                return "tight_passive"  # Rock
            else:
                return "tight_aggressive"  # TAG
        elif vpip > self.exploit_thresholds["vpip_loose"]:
            if pfr < self.exploit_thresholds["pfr_passive"]:
                return "loose_passive"  # Calling station
            else:
                return "loose_aggressive"  # LAG
        else:  # Middle VPIP
            if pfr < self.exploit_thresholds["pfr_passive"]:
                return "passive"
            elif pfr > self.exploit_thresholds["pfr_aggressive"]:
                return "aggressive"
            else:
                return "balanced"
    
    def get_exploitative_adjustments(self, opponent_name: str, 
                                   situation: str,
                                   board: Optional[List[str]] = None) -> Dict[str, float]:
        """
        Get exploitative adjustments against specific opponent.
        
        Args:
            opponent_name: Target opponent
            situation: Situation type ('preflop', 'cbet', 'bluff', etc.)
            board: Board cards if relevant
            
        Returns:
            Dictionary of adjustment factors
        """
        if opponent_name not in self.player_stats:
            return {}
        
        stats = self.player_stats[opponent_name]
        player_type = self.get_player_type(opponent_name)
        
        adjustments = {}
        
        if situation == "preflop":
            adjustments = self._get_preflop_adjustments(stats, player_type)
        elif situation == "cbet":
            adjustments = self._get_cbet_adjustments(stats, player_type)
        elif situation == "bluff":
            adjustments = self._get_bluff_adjustments(stats, player_type)
        elif situation == "value_bet":
            adjustments = self._get_value_bet_adjustments(stats, player_type)
        
        return adjustments
    
    def _get_preflop_adjustments(self, stats: PlayerStats, 
                               player_type: str) -> Dict[str, float]:
        """Get preflop exploitative adjustments."""
        adjustments = {
            "open_frequency": 1.0,
            "3bet_frequency": 1.0,
            "call_frequency": 1.0,
            "4bet_frequency": 1.0,
            "fold_frequency": 1.0
        }
        
        if player_type == "tight_passive":
            # Exploit by opening wider, 3-betting less for value
            adjustments["open_frequency"] = 1.3
            adjustments["3bet_frequency"] = 0.7
            adjustments["call_frequency"] = 1.2
        
        elif player_type == "loose_passive":
            # Exploit by value betting more, bluffing less
            adjustments["open_frequency"] = 1.1
            adjustments["3bet_frequency"] = 1.3  # More value 3-bets
            adjustments["call_frequency"] = 0.8   # Tighter calls
        
        elif player_type == "tight_aggressive":
            # Respect their raises, widen calling ranges slightly
            adjustments["open_frequency"] = 0.9
            adjustments["3bet_frequency"] = 0.8
            adjustments["call_frequency"] = 1.1
        
        elif player_type == "loose_aggressive":
            # Tighten up, let them bluff into us
            adjustments["open_frequency"] = 0.8
            adjustments["3bet_frequency"] = 0.9
            adjustments["call_frequency"] = 1.2
        
        return adjustments
    
    def _get_cbet_adjustments(self, stats: PlayerStats, 
                            player_type: str) -> Dict[str, float]:
        """Get continuation bet adjustments."""
        adjustments = {
            "cbet_frequency": 1.0,
            "cbet_size": 1.0,
            "call_cbet_frequency": 1.0,
            "raise_cbet_frequency": 1.0
        }
        
        # Adjust based on opponent's fold-to-cbet tendency
        if stats.fold_to_cbet > self.exploit_thresholds["fold_to_cbet_high"]:
            # Opponent folds too much to c-bets
            adjustments["cbet_frequency"] = 1.4  # C-bet more
            adjustments["cbet_size"] = 1.2       # Larger size
        elif stats.fold_to_cbet < 40.0:
            # Opponent doesn't fold enough
            adjustments["cbet_frequency"] = 0.7  # C-bet less
            adjustments["cbet_size"] = 0.8       # Smaller size
        
        # Adjust based on opponent's c-bet frequency
        if stats.cbet_flop > self.exploit_thresholds["cbet_high"]:
            # Opponent c-bets too much
            adjustments["call_cbet_frequency"] = 1.3
            adjustments["raise_cbet_frequency"] = 1.2
        elif stats.cbet_flop < self.exploit_thresholds["cbet_low"]:
            # Opponent doesn't c-bet enough
            adjustments["call_cbet_frequency"] = 0.8
            adjustments["raise_cbet_frequency"] = 0.7
        
        return adjustments
    
    def _get_bluff_adjustments(self, stats: PlayerStats, 
                             player_type: str) -> Dict[str, float]:
        """Get bluffing adjustments."""
        adjustments = {
            "bluff_frequency": 1.0,
            "bluff_size": 1.0,
            "bluff_catcher_call": 1.0
        }
        
        if player_type in ["tight_passive", "tight_aggressive"]:
            # Tight players fold too much
            adjustments["bluff_frequency"] = 1.3
            adjustments["bluff_size"] = 1.1
        elif player_type in ["loose_passive", "loose_aggressive"]:
            # Loose players call too much
            adjustments["bluff_frequency"] = 0.7
            adjustments["bluff_catcher_call"] = 1.2
        
        # Adjust based on aggression factor
        if stats.aggression_factor > 2.0:
            # Very aggressive opponent - they might be bluffing
            adjustments["bluff_catcher_call"] = 1.3
        elif stats.aggression_factor < 0.5:
            # Very passive opponent - bluff more
            adjustments["bluff_frequency"] = 1.4
        
        return adjustments
    
    def _get_value_bet_adjustments(self, stats: PlayerStats, 
                                  player_type: str) -> Dict[str, float]:
        """Get value betting adjustments."""
        adjustments = {
            "value_bet_frequency": 1.0,
            "value_bet_size": 1.0,
            "thin_value_frequency": 1.0
        }
        
        if player_type == "loose_passive":
            # Calling stations - bet thinner for value
            adjustments["value_bet_frequency"] = 1.2
            adjustments["thin_value_frequency"] = 1.4
            adjustments["value_bet_size"] = 1.1
        elif player_type == "tight_aggressive":
            # Won't call light - need stronger hands
            adjustments["value_bet_frequency"] = 0.9
            adjustments["thin_value_frequency"] = 0.7
        
        return adjustments
    
    def get_opponent_range_estimate(self, opponent_name: str,
                                  action_sequence: List[BettingAction],
                                  position: Position,
                                  board: List[str]) -> List[str]:
        """
        Estimate opponent's current range based on actions and tendencies.
        
        Returns:
            List of hand combinations in opponent's estimated range
        """
        if opponent_name not in self.player_stats:
            # Use default ranges if no data
            from app.core.range_analyzer import RangeAnalyzer
            range_analyzer = RangeAnalyzer()
            return range_analyzer.get_preflop_range(position, "open")
        
        stats = self.player_stats[opponent_name]
        player_type = self.get_player_type(opponent_name)
        
        # Start with position-based range
        from app.core.range_analyzer import RangeAnalyzer
        range_analyzer = RangeAnalyzer()
        base_range = range_analyzer.get_preflop_range(position, "open")
        
        # Adjust range based on player type
        range_multiplier = self._get_range_width_multiplier(player_type)
        
        # Apply VPIP-based adjustment
        if stats.hands_observed >= 20:
            vpip_adjustment = stats.vpip / 20.0  # Normalize around 20% VPIP
            range_multiplier *= vpip_adjustment
        
        # Adjust range size (simplified)
        if range_multiplier > 1.0:
            # Add more hands (simplified approach)
            additional_hands = ["A2s", "A3s", "A4s", "K2s", "K3s", "Q2s", "J2s", "T2s"]
            base_range.extend(additional_hands[:int((range_multiplier - 1.0) * 10)])
        elif range_multiplier < 1.0:
            # Remove hands (keep strongest portion)
            keep_count = int(len(base_range) * range_multiplier)
            base_range = base_range[:keep_count]
        
        return base_range
    
    def _get_range_width_multiplier(self, player_type: str) -> float:
        """Get range width multiplier based on player type."""
        multipliers = {
            "tight_passive": 0.7,
            "tight_aggressive": 0.8,
            "loose_passive": 1.4,
            "loose_aggressive": 1.3,
            "balanced": 1.0,
            "aggressive": 1.1,
            "passive": 1.2
        }
        return multipliers.get(player_type, 1.0)
    
    def get_meta_adjustments(self, table_state: TableState) -> Dict[str, Any]:
        """
        Get table-wide meta adjustments based on all opponents.
        
        Returns:
            Dictionary with table dynamics and adjustments
        """
        active_opponents = [seat for seat in table_state.seats 
                          if seat.in_hand and not seat.is_hero]
        
        if not active_opponents:
            return {}
        
        # Analyze table dynamics
        player_types = []
        avg_vpip = 0.0
        avg_aggression = 0.0
        
        for seat in active_opponents:
            if seat.name and seat.name in self.player_stats:
                stats = self.player_stats[seat.name]
                player_type = self.get_player_type(seat.name)
                player_types.append(player_type)
                avg_vpip += stats.vpip
                avg_aggression += stats.aggression_factor
        
        # Only provide adjustments if we have actual opponent data
        if not player_types:
            return {"table_dynamic": "no_data"}
        
        avg_vpip /= len(player_types)
        avg_aggression /= len(player_types)
        
        # Determine table dynamics
        table_dynamic = "unknown"
        if avg_vpip < 20.0:
            table_dynamic = "tight"
        elif avg_vpip > 30.0:
            table_dynamic = "loose"
        else:
            table_dynamic = "balanced"
        
        if avg_aggression > 1.5:
            table_dynamic += "_aggressive"
        elif avg_aggression < 0.8:
            table_dynamic += "_passive"
        
        # Generate meta adjustments
        adjustments = {
            "table_dynamic": table_dynamic,
            "avg_vpip": avg_vpip,
            "avg_aggression": avg_aggression,
            "range_adjustment": 1.0,
            "aggression_adjustment": 1.0,
            "bluff_frequency_adjustment": 1.0
        }
        
        # Adjust strategy based on table dynamic
        if "tight" in table_dynamic:
            adjustments["range_adjustment"] = 1.2  # Play wider
            adjustments["bluff_frequency_adjustment"] = 1.3
        elif "loose" in table_dynamic:
            adjustments["range_adjustment"] = 0.8  # Play tighter
            adjustments["bluff_frequency_adjustment"] = 0.7
        
        if "aggressive" in table_dynamic:
            adjustments["aggression_adjustment"] = 0.9  # Be more conservative
        elif "passive" in table_dynamic:
            adjustments["aggression_adjustment"] = 1.2  # Be more aggressive
        
        return adjustments