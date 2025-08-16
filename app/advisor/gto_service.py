"""GTO decision service using OpenSpiel CFR algorithms."""

import os
import asyncio
import logging
from typing import Dict, Optional, Tuple
import json
from datetime import datetime

from app.api.models import TableState, GTOResponse, GTODecision, GTOMetrics
from app.advisor.adapter import TableStateAdapter
from app.core.openspiel_wrapper import OpenSpielWrapper
from app.core.strategy_cache import StrategyCache

logger = logging.getLogger(__name__)


class GTODecisionService:
    """Service for computing GTO poker decisions using OpenSpiel CFR."""
    
    def __init__(self):
        """Initialize the GTO decision service."""
        self.adapter = TableStateAdapter()
        self.openspiel_wrapper = OpenSpielWrapper()
        self.strategy_cache = StrategyCache()
        self.strategies_path = "app/strategies"
        
        # Load default strategies
        self._load_strategies()
        
        logger.info("GTO Decision Service initialized")
    
    def _load_strategies(self):
        """Load strategy configurations from JSON files."""
        try:
            strategy_files = {
                "default_cash6max": "default_cash6max.json",
                "default_mtt": "default_mtt.json"
            }
            
            self.strategies = {}
            for name, filename in strategy_files.items():
                filepath = os.path.join(self.strategies_path, filename)
                if os.path.exists(filepath):
                    with open(filepath, 'r') as f:
                        self.strategies[name] = json.load(f)
                    logger.info(f"Loaded strategy: {name}")
                else:
                    logger.warning(f"Strategy file not found: {filepath}")
                    # Create default strategy
                    self.strategies[name] = self._create_default_strategy()
                    
        except Exception as e:
            logger.error(f"Failed to load strategies: {e}")
            # Fallback to default strategies
            self.strategies = {
                "default_cash6max": self._create_default_strategy(),
                "default_mtt": self._create_default_strategy()
            }
    
    def _create_default_strategy(self) -> Dict:
        """Create a default GTO-oriented strategy."""
        return {
            "cfr_iterations": 10000,
            "max_compute_time_ms": 500,
            "preflop_raise_size": 3.0,
            "cbet_frequency": 0.65,
            "bluff_frequency": 0.33,
            "value_bet_threshold": 0.65,
            "fold_threshold": 0.25,
            "aggression_factor": 1.2,
            "position_adjustment": True
        }
    
    def is_available(self) -> bool:
        """Check if the service is available."""
        try:
            return self.openspiel_wrapper.is_available()
        except:
            return False
    
    def is_cfr_ready(self) -> bool:
        """Check if CFR solver is ready."""
        try:
            return self.openspiel_wrapper.is_cfr_ready()
        except:
            return False
    
    async def compute_gto_decision(
        self, 
        state: TableState, 
        strategy_name: str = "default_cash6max"
    ) -> GTOResponse:
        """Compute GTO decision for given table state."""
        try:
            start_time = datetime.now()
            
            # Get strategy configuration
            strategy = self.strategies.get(strategy_name, self.strategies["default_cash6max"])
            
            # Adapt table state to OpenSpiel format
            game_context = self.adapter.adapt_to_openspiel(state)
            
            # Check strategy cache first
            cache_key = self._generate_cache_key(game_context)
            cached_result = self.strategy_cache.get(cache_key)
            
            if cached_result:
                logger.debug("Using cached GTO decision")
                return self._build_response(cached_result, strategy_name, state)
            
            # Compute GTO solution using CFR
            cfr_result = await self._compute_cfr_solution(game_context, strategy)
            
            # Convert CFR result to decision
            decision_result = self._convert_cfr_to_decision(cfr_result, game_context, state)
            
            # Cache the result
            self.strategy_cache.set(cache_key, decision_result)
            
            computation_time = (datetime.now() - start_time).total_seconds() * 1000
            logger.info(f"GTO decision computed in {computation_time:.2f}ms")
            
            return self._build_response(decision_result, strategy_name, state)
            
        except Exception as e:
            logger.error(f"GTO decision computation failed: {e}")
            # Fallback to heuristic decision
            return self._fallback_decision(state, strategy_name)
    
    async def _compute_cfr_solution(self, game_context: Dict, strategy: Dict) -> Dict:
        """Compute CFR solution for the given game context."""
        try:
            max_iterations = strategy.get("cfr_iterations", 10000)
            max_time_ms = strategy.get("max_compute_time_ms", 500)
            
            # Run CFR computation asynchronously to avoid blocking
            loop = asyncio.get_event_loop()
            cfr_result = await loop.run_in_executor(
                None,
                self.openspiel_wrapper.compute_cfr_strategy,
                game_context,
                max_iterations,
                max_time_ms
            )
            
            return cfr_result
            
        except Exception as e:
            logger.error(f"CFR computation failed: {e}")
            raise
    
    def _convert_cfr_to_decision(
        self, 
        cfr_result: Dict, 
        game_context: Dict, 
        state: TableState
    ) -> Dict:
        """Convert CFR result to poker decision format."""
        try:
            # Extract key metrics from CFR result
            equity = cfr_result.get("equity", 0.5)
            ev = cfr_result.get("expected_value", 0)
            action_probabilities = cfr_result.get("action_probabilities", {})
            
            # Determine best action based on CFR probabilities
            best_action = max(action_probabilities, key=action_probabilities.get)
            action_prob = action_probabilities[best_action]
            
            # Convert OpenSpiel action to poker action
            decision = self._openspiel_action_to_poker(
                best_action, action_prob, game_context, state
            )
            
            # Calculate metrics
            metrics = {
                "equity": equity,
                "min_call": state.to_call or 0,
                "min_bet": state.bet_min or state.stakes.bb,
                "pot": state.pot,
                "players": len([s for s in state.seats if s.in_hand]),
                "ev": ev,
                "exploitability": cfr_result.get("exploitability", 0)
            }
            
            return {
                "decision": decision,
                "metrics": metrics
            }
            
        except Exception as e:
            logger.error(f"CFR to decision conversion failed: {e}")
            raise
    
    def _openspiel_action_to_poker(
        self, 
        openspiel_action: str, 
        probability: float,
        game_context: Dict, 
        state: TableState
    ) -> Dict:
        """Convert OpenSpiel action to poker decision format with proper bet sizing."""
        
        to_call = state.to_call or 0
        pot_size = state.pot
        min_bet = state.bet_min or state.stakes.bb
        
        # Action mapping from OpenSpiel to poker terms
        if openspiel_action == "fold":
            return {"action": "Fold", "size": 0}
        
        elif openspiel_action == "check":
            if to_call > 0:
                # Can't check when facing a bet - this is an error, default to fold
                return {"action": "Fold", "size": 0}
            return {"action": "Check", "size": 0}
        
        elif openspiel_action == "call":
            if to_call <= 0:
                # No bet to call - check instead
                return {"action": "Check", "size": 0}
            return {"action": "Call", "size": to_call}
        
        elif "bet" in openspiel_action or "raise" in openspiel_action:
            if to_call > 0:
                # Facing a bet - this is a raise/3-bet situation
                return self._calculate_raise_size(probability, pot_size, to_call, min_bet)
            else:
                # No bet to face - this is an opening bet
                return self._calculate_bet_size(probability, pot_size, min_bet)
        
        # Default fallback
        if to_call > 0:
            return {"action": "Call", "size": to_call}
        else:
            return {"action": "Check", "size": 0}
    
    def _calculate_bet_size(self, probability: float, pot_size: float, min_bet: float) -> Dict:
        """Calculate opening bet size."""
        # Opening bet sizing based on confidence
        if probability > 0.8:  # Very confident - large bet
            bet_size = pot_size * 0.75
            action = "BetPlus"
        elif probability > 0.6:  # Confident - standard bet
            bet_size = pot_size * 0.5
            action = "Bet"
        elif probability > 0.4:  # Moderate - small bet
            bet_size = pot_size * 0.33
            action = "Bet"
        else:  # Low confidence - min bet
            bet_size = min_bet
            action = "Bet"
        
        bet_size = max(bet_size, min_bet)
        return {"action": action, "size": bet_size}
    
    def _calculate_raise_size(self, probability: float, pot_size: float, to_call: float, min_bet: float) -> Dict:
        """Calculate raise/3-bet size when facing a bet."""
        total_pot_after_call = pot_size + to_call
        
        if probability > 0.8:  # Very confident - large 3-bet
            raise_size = to_call + (total_pot_after_call * 1.0)  # Pot-sized 3-bet
            action = "BetPlus"
        elif probability > 0.6:  # Confident - standard 3-bet
            raise_size = to_call + (total_pot_after_call * 0.6)  # 60% pot 3-bet
            action = "BetPlus"
        elif probability > 0.4:  # Moderate - small 3-bet
            raise_size = to_call + (total_pot_after_call * 0.4)  # 40% pot 3-bet
            action = "Bet"
        else:  # Low confidence - min raise
            raise_size = to_call + min_bet
            action = "Bet"
        
        # Ensure it's at least a legal raise
        min_raise = to_call + min_bet
        raise_size = max(raise_size, min_raise)
        
        return {"action": action, "size": raise_size}
    
    def _generate_cache_key(self, game_context: Dict) -> str:
        """Generate cache key for strategy lookup."""
        key_components = [
            str(game_context.get("street", 0)),
            str(sorted(game_context.get("hero_cards", []))),
            str(sorted(game_context.get("board_cards", []))),
            str(game_context.get("num_players", 2)),
            str(game_context.get("pot_size", 0)),
            str(game_context.get("to_call", 0))
        ]
        return "_".join(key_components)
    
    def _build_response(
        self, 
        decision_result: Dict, 
        strategy_name: str, 
        state: TableState
    ) -> GTOResponse:
        """Build final GTO response."""
        decision_data = decision_result["decision"]
        metrics_data = decision_result["metrics"]
        
        decision = GTODecision(
            action=decision_data["action"],
            size=decision_data["size"]
        )
        
        metrics = GTOMetrics(
            equity=metrics_data["equity"],
            min_call=metrics_data["min_call"],
            min_bet=metrics_data["min_bet"],
            pot=metrics_data["pot"],
            players=metrics_data["players"],
            ev=metrics_data.get("ev"),
            exploitability=metrics_data.get("exploitability")
        )
        
        return GTOResponse(
            ok=True,
            decision=decision,
            metrics=metrics,
            strategy=strategy_name
        )
    
    def _fallback_decision(self, state: TableState, strategy_name: str) -> GTOResponse:
        """Provide fallback heuristic decision when CFR fails."""
        logger.warning("Using fallback heuristic decision")
        
        # Simple heuristic based on basic poker principles
        to_call = state.to_call or 0
        pot_odds = to_call / (state.pot + to_call) if (state.pot + to_call) > 0 else 0
        
        # Basic decision logic
        if not state.hero_hole:
            action = "Fold"
            size = 0
        elif to_call == 0:  # Can check
            action = "Check" 
            size = 0
        elif pot_odds > 0.3:  # Poor pot odds
            action = "Fold"
            size = 0
        else:  # Acceptable pot odds
            action = "Call"
            size = to_call
            
        decision = GTODecision(action=action, size=size)
        metrics = GTOMetrics(
            equity=0.5,  # Unknown
            min_call=to_call,
            min_bet=state.bet_min or state.stakes.bb,
            pot=state.pot,
            players=len([s for s in state.seats if s.in_hand])
        )
        
        return GTOResponse(
            ok=True,
            decision=decision,
            metrics=metrics,
            strategy=strategy_name
        )
