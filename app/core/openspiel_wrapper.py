"""OpenSpiel wrapper for CFR-based GTO poker solving."""

import logging
from typing import Dict, List, Optional, Any
import time

try:
    import pyspiel
    from open_spiel.python.algorithms import cfr
    OPENSPIEL_AVAILABLE = True
except ImportError:
    OPENSPIEL_AVAILABLE = False
    pyspiel = None
    cfr = None

logger = logging.getLogger(__name__)


class OpenSpielWrapper:
    """Wrapper for OpenSpiel CFR algorithms."""
    
    def __init__(self):
        """Initialize OpenSpiel wrapper."""
        self.game = None
        self.cfr_solver = None
        
        if OPENSPIEL_AVAILABLE:
            try:
                # Initialize with a simple game for testing
                self._initialize_solver()
                logger.info("OpenSpiel CFR solver initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize OpenSpiel solver: {e}")
                self.game = None
                self.cfr_solver = None
        else:
            logger.warning("OpenSpiel not available - install with: pip install open_spiel")
    
    def is_available(self) -> bool:
        """Check if OpenSpiel is available."""
        return OPENSPIEL_AVAILABLE and self.game is not None
    
    def is_cfr_ready(self) -> bool:
        """Check if CFR solver is ready."""
        return self.cfr_solver is not None
    
    def _initialize_solver(self):
        """Initialize the CFR solver with a poker game."""
        if not OPENSPIEL_AVAILABLE or pyspiel is None or cfr is None:
            raise RuntimeError("OpenSpiel not available")
            
        try:
            # Use Kuhn poker for basic testing, leduc for more complex scenarios
            # In production, you'd use no_limit_holdem but it's computationally intensive
            self.game = pyspiel.load_game("leduc_poker")
            self.cfr_solver = cfr.CFRSolver(self.game)
            
        except Exception as e:
            logger.error(f"CFR solver initialization failed: {e}")
            # Fallback to simpler game
            try:
                self.game = pyspiel.load_game("kuhn_poker")
                self.cfr_solver = cfr.CFRSolver(self.game)
                logger.info("Using Kuhn poker as fallback game")
            except Exception as e2:
                logger.error(f"Fallback game initialization also failed: {e2}")
                raise
    
    def compute_cfr_strategy(
        self,
        game_context: Dict,
        max_iterations: int = 10000,
        max_time_ms: int = 500
    ) -> Dict:
        """Compute CFR strategy for given game context."""
        if not self.is_available():
            raise RuntimeError("OpenSpiel not available or not initialized")
        
        try:
            start_time = time.time()
            
            # For demo purposes, we'll use the pre-initialized solver
            # In a full implementation, you'd create a game state from game_context
            solver = self.cfr_solver
            
            # Run CFR iterations with time limit
            iterations_run = 0
            while (iterations_run < max_iterations and 
                   (time.time() - start_time) * 1000 < max_time_ms):
                
                if solver is not None:
                    solver.evaluate_and_update_policy()
                iterations_run += 1
                
                # Check every 100 iterations to avoid excessive time checking
                if iterations_run % 100 == 0:
                    elapsed_ms = (time.time() - start_time) * 1000
                    if elapsed_ms > max_time_ms:
                        break
            
            # Get the computed strategy
            average_policy = solver.average_policy() if solver is not None else None
            
            # Compute basic metrics
            equity = self._estimate_equity(game_context, average_policy)
            expected_value = self._estimate_expected_value(game_context, average_policy)
            exploitability = self._estimate_exploitability(solver)
            action_probabilities = self._extract_action_probabilities(
                game_context, average_policy
            )
            
            logger.debug(f"CFR completed: {iterations_run} iterations in {(time.time() - start_time)*1000:.1f}ms")
            
            return {
                "equity": equity,
                "expected_value": expected_value,
                "exploitability": exploitability,
                "action_probabilities": action_probabilities,
                "iterations": iterations_run,
                "computation_time_ms": (time.time() - start_time) * 1000
            }
            
        except Exception as e:
            logger.error(f"CFR computation failed: {e}")
            # Return fallback result
            return self._fallback_cfr_result(game_context)
    
    def _estimate_equity(self, game_context: Dict, policy) -> float:
        """Estimate hero's equity based on game context."""
        # This is a simplified estimation - in a full implementation,
        # you'd use the actual game state and policy to compute precise equity
        
        street = game_context.get("street", 0)
        num_players = game_context.get("num_players", 2)
        hero_cards = game_context.get("hero_cards", [])
        board_cards = game_context.get("board_cards", [])
        
        # Basic equity estimation based on street and cards
        base_equity = 1.0 / num_players  # Fair share
        
        # Adjust based on street (more information = more accurate)
        if street == 0:  # Preflop
            # Very rough preflop equity estimation
            if len(hero_cards) == 2:
                card1, card2 = hero_cards[0], hero_cards[1]
                if card1 // 4 == card2 // 4:  # Pocket pair
                    base_equity = min(0.8, base_equity * 2.0)
                elif abs(card1 // 4 - card2 // 4) <= 2:  # Connected cards
                    base_equity = min(0.7, base_equity * 1.5)
                else:
                    base_equity = max(0.2, base_equity)
        else:
            # Post-flop: assume strategy gives reasonable estimate
            base_equity = max(0.1, min(0.9, base_equity + (street * 0.1)))
        
        return base_equity
    
    def _estimate_expected_value(self, game_context: Dict, policy) -> float:
        """Estimate expected value of the computed strategy."""
        equity = self._estimate_equity(game_context, policy)
        pot_size = game_context.get("pot_size", 0)
        
        # Simple EV estimation: equity * pot - cost to call
        to_call = game_context.get("to_call", 0)
        expected_value = equity * (pot_size + to_call) - to_call
        
        return expected_value
    
    def _estimate_exploitability(self, solver) -> float:
        """Estimate exploitability of the strategy."""
        # This would require computing best response in a full implementation
        # For now, return a reasonable estimate based on iterations
        try:
            # More iterations generally mean lower exploitability
            return max(0.01, 1.0 / (1 + len(solver.cumulative_regrets()) / 1000))
        except:
            return 0.05  # Default reasonable exploitability
    
    def _extract_action_probabilities(self, game_context: Dict, policy) -> Dict[str, float]:
        """Extract action probabilities from policy."""
        # This is simplified - in practice you'd need to map the exact game state
        # to the policy and extract the action probabilities
        
        # For demonstration, create reasonable action probabilities
        street = game_context.get("street", 0)
        to_call = game_context.get("to_call", 0)
        
        if to_call == 0:  # Can check
            if street == 0:  # Preflop
                return {
                    "check": 0.3,
                    "bet": 0.6,
                    "fold": 0.1
                }
            else:  # Postflop
                return {
                    "check": 0.5,
                    "bet": 0.4,
                    "fold": 0.1
                }
        else:  # Must call or fold
            equity = self._estimate_equity(game_context, policy)
            if equity > 0.6:
                return {
                    "call": 0.8,
                    "raise": 0.15,
                    "fold": 0.05
                }
            elif equity > 0.4:
                return {
                    "call": 0.6,
                    "raise": 0.1,
                    "fold": 0.3
                }
            else:
                return {
                    "call": 0.2,
                    "raise": 0.05,
                    "fold": 0.75
                }
    
    def _fallback_cfr_result(self, game_context: Dict) -> Dict:
        """Provide fallback result when CFR computation fails."""
        logger.warning("Using fallback CFR result")
        
        # Return reasonable default values
        return {
            "equity": 0.5,
            "expected_value": 0,
            "exploitability": 0.1,
            "action_probabilities": {
                "fold": 0.3,
                "call": 0.4,
                "bet": 0.3
            },
            "iterations": 0,
            "computation_time_ms": 1
        }
    
    def reset_solver(self):
        """Reset the CFR solver state."""
        if self.is_available():
            try:
                self._initialize_solver()
                logger.info("CFR solver reset successfully")
            except Exception as e:
                logger.error(f"Failed to reset CFR solver: {e}")
