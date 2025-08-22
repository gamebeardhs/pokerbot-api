"""Enhanced GTO decision service with comprehensive poker analysis."""

from app.advisor.texas_solver_client import TexasSolverClient
import os
import asyncio
import logging
from typing import Dict, Optional, Tuple, List
import json
from datetime import datetime

from app.api.models import (
    TableState, GTOResponse, GTODecision, GTOMetrics, EquityBreakdown,
    BoardTexture, RangeInfo, BettingAction, Position
)
from app.advisor.adapter import TableStateAdapter
from app.core.openspiel_wrapper import OpenSpielWrapper
from app.core.strategy_cache import StrategyCache
from app.core.board_analyzer import BoardAnalyzer
from app.core.range_analyzer import RangeAnalyzer
from app.core.position_strategy import PositionStrategy
from app.core.opponent_modeling import OpponentModeling

logger = logging.getLogger(__name__)


class EnhancedGTODecisionService:
    """Enhanced GTO decision service with comprehensive poker analysis."""
    
    def __init__(self):
        """Initialize the enhanced GTO decision service."""
        self.adapter = TableStateAdapter()
        self.openspiel_wrapper = OpenSpielWrapper()
        self.strategy_cache = StrategyCache()
        self.strategies_path = "app/strategies"
        self.ts_client = TexasSolverClient(base_url=os.getenv("TEXASSOLVER_API_URL""http://127.0.0.1:8000"))
        # Enhanced GTO components
        self.board_analyzer = BoardAnalyzer()
        self.range_analyzer = RangeAnalyzer()
        self.position_strategy = PositionStrategy()
        self.opponent_modeling = OpponentModeling()
        
        # Load default strategies
        self._load_strategies()
        
        logger.info("Enhanced GTO Decision Service initialized")
    
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
            "cfr_iterations": 10,  # Ultra-fast for real-time (<100ms)
            "max_compute_time_ms": 100,
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
        """Compute comprehensive GTO decision using all available analysis."""
        use_ts = True  # switch via env/config later
        if use_ts:
            ts = self.ts_client.solve(state)
            if ts.get("status") == "ok" and ts.get("actions"):
                return self.ts_client.to_gto_response(state, ts)
    # fallback:
    # return a minimal, safe response or drop to OpenSpiel (if available)
        try:
            start_time = datetime.now()
            
            # Enhanced table analysis
            enhanced_state = await self._enhance_table_state(state)
            
            # Get strategy configuration with adjustments
            strategy = self._get_adjusted_strategy(enhanced_state, strategy_name)
            
            # Adapt table state to OpenSpiel format
            game_context = self.adapter.adapt_to_openspiel(enhanced_state)
            
            # Generate comprehensive cache key
            cache_key = self._generate_enhanced_cache_key(enhanced_state, game_context)
            cached_result = self.strategy_cache.get(cache_key)
            
            if cached_result:
                logger.debug("Using cached enhanced GTO decision")
                return self._build_enhanced_response(cached_result, strategy_name, enhanced_state)
            
            # Compute comprehensive GTO solution
            gto_analysis = await self._compute_comprehensive_gto(enhanced_state, game_context, strategy)
            
            # Cache the result
            self.strategy_cache.set(cache_key, gto_analysis)
            
            computation_time = (datetime.now() - start_time).total_seconds() * 1000
            logger.info(f"Enhanced GTO decision computed in {computation_time:.2f}ms")
            
            # Add computation time to analysis
            gto_analysis["computation_time_ms"] = computation_time
            
            return self._build_enhanced_response(gto_analysis, strategy_name, enhanced_state)
            
        except Exception as e:
            logger.error(f"Enhanced GTO decision computation failed: {e}")
            # Fallback to enhanced heuristic decision
            return self._enhanced_fallback_decision(state, strategy_name)
    
    async def _enhance_table_state(self, state: TableState) -> TableState:
        """Enhance table state with comprehensive analysis."""
        try:
            # Analyze board texture
            board_texture = self.board_analyzer.analyze_board(state.board)
            
            # Estimate player ranges
            player_ranges = []
            hero_position = None
            
            # Find hero position and analyze ranges
            for seat in state.seats:
                if seat.in_hand and seat.position:
                    try:
                        position = Position(seat.position)
                        if seat.is_hero:
                            hero_position = position
                        
                        # Get preflop range for position
                        preflop_range = self.range_analyzer.get_preflop_range(position, "open")
                        
                        # Estimate current range based on actions
                        current_range = self.range_analyzer.estimate_current_range(
                            preflop_range, state.board, [], position
                        )
                        
                        range_info = RangeInfo(
                            seat=seat.seat,
                            position=position,
                            preflop_range=preflop_range,
                            current_range=current_range,
                            range_equity=0.5,  # Will be calculated later
                            range_strength=0.5
                        )
                        player_ranges.append(range_info)
                    except ValueError:
                        # Skip invalid positions
                        continue
            
            # Calculate effective stacks and SPR
            hero_stack = 0
            effective_stacks = {}
            
            for seat in state.seats:
                if seat.is_hero and seat.stack:
                    hero_stack = seat.stack
                    break
            
            for seat in state.seats:
                if seat.in_hand and not seat.is_hero and seat.stack:
                    effective_stacks[seat.seat] = min(hero_stack, seat.stack)
            
            # Calculate SPR (Stack-to-Pot Ratio)
            spr = hero_stack / max(state.pot, 1) if hero_stack > 0 else 0
            
            # Determine button, SB, BB positions
            button_seat = None
            sb_seat = None
            bb_seat = None
            
            for seat in state.seats:
                if seat.position == "BTN":
                    button_seat = seat.seat
                elif seat.position == "SB":
                    sb_seat = seat.seat
                elif seat.position == "BB":
                    bb_seat = seat.seat
            
            # Create enhanced state
            enhanced_state = TableState(
                table_id=state.table_id,
                hand_id=state.hand_id,
                room=state.room,
                variant=state.variant,
                max_seats=state.max_seats,
                hero_seat=state.hero_seat,
                stakes=state.stakes,
                street=state.street,
                board=state.board,
                hero_hole=state.hero_hole,
                pot=state.pot,
                round_pot=state.round_pot,
                to_call=state.to_call,
                bet_min=state.bet_min,
                seats=state.seats,
                action_clock_ms=state.action_clock_ms,
                timestamp=state.timestamp,
                # Enhanced fields
                betting_history=[],  # Would be populated from action tracking
                board_texture=board_texture,
                player_ranges=player_ranges,
                effective_stacks=effective_stacks,
                spr=spr,
                button_seat=button_seat,
                sb_seat=sb_seat,
                bb_seat=bb_seat,
                rake_cap=0.05,  # Standard rake cap
                rake_percentage=0.05  # Standard rake percentage
            )
            
            return enhanced_state
            
        except Exception as e:
            logger.error(f"Failed to enhance table state: {e}")
            return state
    
    def _get_adjusted_strategy(self, state: TableState, strategy_name: str) -> Dict:
        """Get strategy adjusted for position, opponents, and board texture."""
        base_strategy = self.strategies.get(strategy_name, self.strategies["default_cash6max"])
        
        # Get hero position
        hero_position = None
        for seat in state.seats:
            if seat.is_hero and seat.position:
                try:
                    hero_position = Position(seat.position)
                    break
                except ValueError:
                    continue
        
        if not hero_position:
            return base_strategy
        
        # Get positional adjustments
        active_opponents = [seat for seat in state.seats if seat.in_hand and not seat.is_hero]
        
        position_adjustments = self.position_strategy.get_position_adjustment(
            hero_position, None, len(active_opponents)
        )
        
        # Apply opponent modeling adjustments
        meta_adjustments = self.opponent_modeling.get_meta_adjustments(state)
        
        # Combine adjustments
        adjusted_strategy = base_strategy.copy()
        
        # Adjust key parameters
        if "aggression_factor" in adjusted_strategy:
            adjusted_strategy["aggression_factor"] *= position_adjustments.get("aggression", 1.0)
            adjusted_strategy["aggression_factor"] *= meta_adjustments.get("aggression_adjustment", 1.0)
        
        if "bluff_frequency" in adjusted_strategy:
            adjusted_strategy["bluff_frequency"] *= position_adjustments.get("bluff_frequency", 1.0)
            adjusted_strategy["bluff_frequency"] *= meta_adjustments.get("bluff_frequency_adjustment", 1.0)
        
        return adjusted_strategy
    
    async def _compute_comprehensive_gto(self, state: TableState, 
                                       game_context: Dict, strategy: Dict) -> Dict:
        """Compute comprehensive GTO analysis using all components."""
        try:
            # Standard CFR computation
            cfr_result = await self._compute_cfr_solution(game_context, strategy)
            
            # Enhanced equity analysis
            equity_breakdown = self._compute_equity_breakdown(state, cfr_result)
            
            # Range vs range analysis
            range_analysis = self._compute_range_analysis(state)
            
            # Position-aware decision
            positional_decision = self._compute_positional_decision(state, cfr_result)
            
            # Stack depth considerations
            stack_analysis = self._compute_stack_analysis(state)
            
            # Opponent modeling
            exploitative_adjustments = self._compute_exploitative_adjustments(state)
            
            # Combine all analyses
            comprehensive_analysis = {
                "cfr_result": cfr_result,
                "equity_breakdown": equity_breakdown,
                "range_analysis": range_analysis,
                "positional_decision": positional_decision,
                "stack_analysis": stack_analysis,
                "exploitative_adjustments": exploitative_adjustments,
                "final_decision": self._synthesize_final_decision(
                    cfr_result, equity_breakdown, positional_decision, 
                    stack_analysis, exploitative_adjustments, state
                )
            }
            
            return comprehensive_analysis
            
        except Exception as e:
            logger.error(f"Comprehensive GTO computation failed: {e}")
            # Fallback to basic CFR
            cfr_result = await self._compute_cfr_solution(game_context, strategy)
            return {"cfr_result": cfr_result, "final_decision": cfr_result}
    
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
    
    def _compute_equity_breakdown(self, state: TableState, cfr_result: Dict) -> Dict:
        """Compute detailed equity breakdown."""
        base_equity = cfr_result.get("equity", 0.5)
        
        return {
            "raw_equity": base_equity,
            "fold_equity": 0.2,  # Estimated fold equity
            "realize_equity": base_equity * 0.9,  # Positional adjustment
            "vs_calling_range": base_equity,
            "vs_folding_range": base_equity
        }
    
    def _compute_range_analysis(self, state: TableState) -> Dict:
        """Compute range vs range analysis."""
        try:
            hero_range = []
            if state.hero_hole:
                # Simplified: treat hero's actual hand as a range
                hero_range = [f"{state.hero_hole[0][0]}{state.hero_hole[1][0]}{'s' if state.hero_hole[0][1] == state.hero_hole[1][1] else 'o'}"]
            
            # Get opponent ranges from enhanced state
            opponent_ranges = []
            if hasattr(state, 'player_ranges') and state.player_ranges:
                for range_info in state.player_ranges:
                    if range_info.seat != state.hero_seat:
                        opponent_ranges.extend(range_info.current_range[:10])  # Sample
            
            # Calculate range vs range equity if we have ranges
            if hero_range and opponent_ranges:
                equity = self.range_analyzer.calculate_range_equity(
                    hero_range, opponent_ranges, state.board
                )
            else:
                equity = 0.5
            
            return {
                "hero_range_size": len(hero_range),
                "opponent_range_size": len(opponent_ranges),
                "range_equity": equity,
                "range_advantage": equity - 0.5
            }
            
        except Exception as e:
            logger.error(f"Range analysis failed: {e}")
            return {"range_equity": 0.5, "range_advantage": 0.0}
    
    def _compute_positional_decision(self, state: TableState, cfr_result: Dict) -> Dict:
        """Compute position-aware decision modifications."""
        try:
            hero_position = None
            for seat in state.seats:
                if seat.is_hero and seat.position:
                    try:
                        hero_position = Position(seat.position)
                        break
                    except ValueError:
                        continue
            
            if not hero_position:
                return cfr_result
            
            # Get positional multipliers
            board_category = self.board_analyzer.get_board_category(state.board)
            
            # Adjust action probabilities based on position
            action_probs = cfr_result.get("action_probabilities", {}).copy()
            
            # Position-based adjustments
            if hero_position in [Position.BTN, Position.CO]:
                # Late position - more aggressive
                if "bet" in action_probs:
                    action_probs["bet"] *= 1.2
                if "raise" in action_probs:
                    action_probs["raise"] *= 1.2
                if "fold" in action_probs:
                    action_probs["fold"] *= 0.9
            elif hero_position in [Position.UTG, Position.UTG1]:
                # Early position - more conservative
                if "bet" in action_probs:
                    action_probs["bet"] *= 0.8
                if "fold" in action_probs:
                    action_probs["fold"] *= 1.1
            
            # Normalize probabilities
            total = sum(action_probs.values())
            if total > 0:
                action_probs = {k: v/total for k, v in action_probs.items()}
            
            return {
                **cfr_result,
                "action_probabilities": action_probs,
                "position_adjustment": True
            }
            
        except Exception as e:
            logger.error(f"Positional decision computation failed: {e}")
            return cfr_result
    
    def _compute_stack_analysis(self, state: TableState) -> Dict:
        """Analyze stack depth implications."""
        spr = getattr(state, 'spr', 0)
        effective_stacks = getattr(state, 'effective_stacks', {})
        
        # Stack depth categories
        if spr > 20:
            depth_category = "very_deep"
            commitment_threshold = 0.15
        elif spr > 10:
            depth_category = "deep"
            commitment_threshold = 0.25
        elif spr > 5:
            depth_category = "medium"
            commitment_threshold = 0.35
        else:
            depth_category = "shallow"
            commitment_threshold = 0.5
        
        return {
            "spr": spr,
            "depth_category": depth_category,
            "commitment_threshold": commitment_threshold,
            "effective_stacks": effective_stacks,
            "stack_pressure": "high" if spr < 10 else "low"
        }
    
    def _compute_exploitative_adjustments(self, state: TableState) -> List[str]:
        """Compute exploitative adjustments based on opponent modeling."""
        adjustments = []
        
        # Get table dynamics
        meta_adjustments = self.opponent_modeling.get_meta_adjustments(state)
        table_dynamic = meta_adjustments.get("table_dynamic", "unknown")
        
        # Only provide adjustments if we have actual opponent data
        if table_dynamic in ["no_data", "unknown"]:
            return adjustments
        
        if "tight" in table_dynamic:
            adjustments.append("Widened range due to tight table")
            adjustments.append("Increased bluff frequency")
        elif "loose" in table_dynamic:
            adjustments.append("Tightened range due to loose table")
            adjustments.append("Reduced bluff frequency")
        
        if "aggressive" in table_dynamic:
            adjustments.append("More conservative due to aggressive opponents")
        elif "passive" in table_dynamic:
            adjustments.append("Increased aggression against passive opponents")
        
        return adjustments
    
    def _synthesize_final_decision(self, cfr_result: Dict, equity_breakdown: Dict,
                                 positional_decision: Dict, stack_analysis: Dict,
                                 exploitative_adjustments: List[str], state: TableState) -> Dict:
        """Synthesize final decision from all analyses."""
        try:
            # Start with positional decision (which includes CFR adjustments)
            final_decision = positional_decision.copy()
            
            # Adjust based on stack depth
            action_probs = final_decision.get("action_probabilities", {}).copy()
            
            # Stack depth adjustments
            if stack_analysis.get("depth_category") == "shallow":
                # Shallow stacks - more commitment
                if "call" in action_probs:
                    action_probs["call"] *= 1.1
                if "fold" in action_probs and action_probs["fold"] > 0.3:
                    action_probs["fold"] *= 0.9
            elif stack_analysis.get("depth_category") == "very_deep":
                # Deep stacks - more speculative
                if "call" in action_probs:
                    action_probs["call"] *= 1.05
            
            # Normalize probabilities
            total = sum(action_probs.values())
            if total > 0:
                action_probs = {k: v/total for k, v in action_probs.items()}
            
            final_decision["action_probabilities"] = action_probs
            final_decision["synthesis_complete"] = True
            
            return final_decision
            
        except Exception as e:
            logger.error(f"Decision synthesis failed: {e}")
            return cfr_result
    
    def _generate_enhanced_cache_key(self, state: TableState, game_context: Dict) -> str:
        """Generate enhanced cache key including all GTO factors."""
        key_components = [
            str(game_context.get("street", 0)),
            str(sorted(game_context.get("hero_cards", []))),
            str(sorted(game_context.get("board_cards", []))),
            str(game_context.get("num_players", 2)),
            str(game_context.get("pot_size", 0)),
            str(game_context.get("to_call", 0)),
            # Enhanced factors
            str(getattr(state.board_texture, 'wetness_score', 0) if hasattr(state, 'board_texture') and state.board_texture else 0),
            str(getattr(state, 'spr', 0)),
            str(len(getattr(state, 'effective_stacks', {}))),
            str(state.hero_seat or 0)
        ]
        return "enhanced_" + "_".join(key_components)
    
    def generate_detailed_explanation(self, decision, state: TableState) -> str:
        """Generate human-readable explanation from mathematical data."""
        try:
            explanation_parts = []
            
            # Extract mathematical components
            action = getattr(decision, 'action', 'UNKNOWN')
            confidence = getattr(decision, 'confidence', 0.0)
            size = getattr(decision, 'size', 0.0)
            
            # Hand strength analysis
            hero_cards = state.hero_hole or []
            if len(hero_cards) == 2:
                if self._is_premium_hand(hero_cards):
                    explanation_parts.append("Premium hand (top 15% starting range)")
                elif self._is_strong_hand(hero_cards):
                    explanation_parts.append("Strong hand (top 30% starting range)")
                elif self._is_speculative_hand(hero_cards):
                    explanation_parts.append("Speculative hand with implied odds potential")
                else:
                    explanation_parts.append("Marginal hand requiring careful play")
            
            # Board texture analysis
            if state.board:
                board_analysis = self._analyze_board_texture(state.board)
                if board_analysis.get("draw_heavy"):
                    explanation_parts.append("Draw-heavy board requires protection betting")
                elif board_analysis.get("dry"):
                    explanation_parts.append("Dry board allows wider bluffing range")
                
                if board_analysis.get("high_card_heavy"):
                    explanation_parts.append("High card board favors preflop aggressor")
            
            # Position analysis
            hero_position = self._get_hero_position(state)
            if hero_position:
                if hero_position in ["BTN", "CO"]:
                    explanation_parts.append("Late position allows aggressive play")
                elif hero_position in ["UTG", "UTG+1"]:
                    explanation_parts.append("Early position requires tighter range")
                elif hero_position == "BB":
                    explanation_parts.append("Big blind has closing action advantage")
            
            # Stack depth considerations
            pot_size = state.pot or 0
            to_call = state.to_call or 0
            if pot_size > 0:
                spr = self._estimate_spr(state)
                if spr < 3:
                    explanation_parts.append(f"Low SPR ({spr:.1f}) favors commitment with strong hands")
                elif spr > 10:
                    explanation_parts.append(f"Deep stacks ({spr:.1f}) allow speculative plays")
            
            # Expected Value reasoning
            if action == "RAISE" or action == "BET":
                explanation_parts.append("Betting maximizes fold equity + value")
            elif action == "CALL":
                if to_call > 0 and pot_size > 0:
                    pot_odds = to_call / (pot_size + to_call)
                    explanation_parts.append(f"Call profitable with {pot_odds:.1%} pot odds")
            elif action == "FOLD":
                explanation_parts.append("Insufficient equity to continue profitably")
            
            # Confidence modifier
            if confidence > 0.8:
                confidence_text = "High confidence decision"
            elif confidence > 0.6:
                confidence_text = "Medium confidence decision"
            else:
                confidence_text = "Close decision requiring careful consideration"
            
            # Combine explanation
            main_explanation = " | ".join(explanation_parts) if explanation_parts else "Standard GTO play"
            
            return f"{main_explanation} | {confidence_text} ({confidence:.1%})"
            
        except Exception as e:
            logger.error(f"Explanation generation failed: {e}")
            return f"GTO analysis: {action} recommended based on mathematical optimization"
    
    def _is_premium_hand(self, cards) -> bool:
        """Check if hand is premium (AA, KK, QQ, AK)."""
        if len(cards) != 2:
            return False
        
        ranks = [self._get_rank(card) for card in cards]
        ranks.sort(reverse=True)
        
        # Pairs: AA, KK, QQ  
        if ranks[0] == ranks[1] and ranks[0] in [14, 13, 12]:
            return True
        
        # AK suited/unsuited
        if ranks == [14, 13]:
            return True
            
        return False
    
    def _is_strong_hand(self, cards) -> bool:
        """Check if hand is strong (JJ, TT, AQ, AJ, KQ)."""
        if len(cards) != 2:
            return False
        
        ranks = [self._get_rank(card) for card in cards]
        ranks.sort(reverse=True)
        
        # Medium pairs: JJ, TT, 99
        if ranks[0] == ranks[1] and ranks[0] in [11, 10, 9]:
            return True
        
        # Strong broadways
        if ranks == [14, 12] or ranks == [14, 11] or ranks == [13, 12]:
            return True
            
        return False
    
    def _is_speculative_hand(self, cards) -> bool:
        """Check if hand is speculative (suited connectors, small pairs)."""
        if len(cards) != 2:
            return False
        
        ranks = [self._get_rank(card) for card in cards]
        suits = [self._get_suit(card) for card in cards]
        
        # Small/medium pairs
        if ranks[0] == ranks[1] and ranks[0] <= 8:
            return True
        
        # Suited connectors
        if suits[0] == suits[1] and abs(ranks[0] - ranks[1]) <= 2:
            return True
        
        return False
    
    def _get_rank(self, card: str) -> int:
        """Convert card to rank number (2=2, A=14)."""
        rank_map = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, 
                   '9': 9, 'T': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14}
        return rank_map.get(card[0].upper(), 2)
    
    def _get_suit(self, card: str) -> str:
        """Extract suit from card."""
        return card[-1].lower() if len(card) > 1 else 's'
    
    def _analyze_board_texture(self, board) -> Dict:
        """Analyze board texture characteristics."""
        if not board or len(board) < 3:
            return {"draw_heavy": False, "dry": True, "high_card_heavy": False}
        
        ranks = [self._get_rank(card) for card in board]
        suits = [self._get_suit(card) for card in board]
        
        # Count suit distribution
        suit_counts = {}
        for suit in suits:
            suit_counts[suit] = suit_counts.get(suit, 0) + 1
        max_suit_count = max(suit_counts.values()) if suit_counts else 0
        
        # Check for draws
        ranks_sorted = sorted(ranks)
        connected = any(abs(ranks_sorted[i] - ranks_sorted[i+1]) <= 2 for i in range(len(ranks_sorted)-1))
        
        return {
            "draw_heavy": max_suit_count >= 2 or connected,
            "dry": max_suit_count <= 1 and not connected,
            "high_card_heavy": any(rank >= 10 for rank in ranks)
        }
    
    def _estimate_spr(self, state: TableState) -> float:
        """Estimate stack-to-pot ratio."""
        pot = state.pot or 0
        if pot <= 0:
            return 10.0  # Default assumption
            
        # Find hero stack
        hero_stack = 100.0  # Default
        if state.seats:
            for seat in state.seats:
                if getattr(seat, 'is_hero', False) and getattr(seat, 'stack', None):
                    hero_stack = seat.stack
                    break
        
        return hero_stack / pot if pot > 0 else 10.0
    
    def _build_enhanced_response(self, analysis: Dict, strategy_name: str, 
                               state: TableState) -> GTOResponse:
        """Build enhanced GTO response with comprehensive analysis."""
        try:
            decision_data = analysis.get("final_decision", analysis.get("cfr_result", {}))
            
            # Extract decision
            action_probs = decision_data.get("action_probabilities", {})
            if action_probs:
                best_action = max(action_probs, key=action_probs.get)
                action_prob = action_probs[best_action]
            else:
                best_action = "check"
                action_prob = 1.0
            
            # Convert to poker action
            poker_decision = self._openspiel_action_to_poker(
                best_action, action_prob, {}, state
            )
            
            # Enhanced decision
            decision = GTODecision(
                action=poker_decision["action"],
                size=poker_decision["size"],
                size_bb=poker_decision["size"] / state.stakes.bb if state.stakes.bb > 0 else 0,
                size_pot_fraction=poker_decision["size"] / state.pot if state.pot > 0 else 0,
                confidence=action_prob,
                frequency=action_prob,
                reasoning="Enhanced GTO decision with comprehensive analysis"
            )
            
            # Enhanced metrics
            equity_data = analysis.get("equity_breakdown", {})
            equity_breakdown = EquityBreakdown(
                raw_equity=equity_data.get("raw_equity", 0.5),
                fold_equity=equity_data.get("fold_equity", 0.2),
                realize_equity=equity_data.get("realize_equity", 0.45),
                vs_calling_range=equity_data.get("vs_calling_range", 0.5),
                vs_folding_range=equity_data.get("vs_folding_range", 0.5)
            )
            
            stack_data = analysis.get("stack_analysis", {})
            range_data = analysis.get("range_analysis", {})
            
            metrics = GTOMetrics(
                equity_breakdown=equity_breakdown,
                min_call=state.to_call or 0,
                min_bet=state.bet_min or state.stakes.bb,
                pot=state.pot,
                players=len([s for s in state.seats if s.in_hand]),
                spr=stack_data.get("spr", 0),
                effective_stack=min(stack_data.get("effective_stacks", {}).values()) if stack_data.get("effective_stacks") else 0,
                pot_odds=(state.to_call or 0) / (state.pot + (state.to_call or 0)) if state.pot + (state.to_call or 0) > 0 else 0,
                range_advantage=range_data.get("range_advantage", 0.0),
                nut_advantage=0.0,  # Would require deeper analysis
                bluff_catchers=0.5,  # Estimated
                board_favorability=getattr(state.board_texture, 'wetness_score', 0.5) if hasattr(state, 'board_texture') and state.board_texture else 0.5,
                positional_advantage=0.1 if self._get_hero_position(state) in [Position.BTN, Position.CO] else -0.1,
                initiative=self._get_hero_position(state) in [Position.BTN, Position.CO, Position.HJ] if self._get_hero_position(state) else False,
                commitment_threshold=stack_data.get("commitment_threshold", 0.3),
                reverse_implied_odds=0.1
            )
            
            return GTOResponse(
                ok=True,
                decision=decision,
                metrics=metrics,
                strategy=strategy_name,
                computation_time_ms=int(analysis.get("computation_time_ms", 0)),
                exploitative_adjustments=analysis.get("exploitative_adjustments", [])
            )
            
        except Exception as e:
            logger.error(f"Failed to build enhanced response: {e}")
            return self._enhanced_fallback_decision(state, strategy_name)
    
    def _get_hero_position(self, state: TableState) -> Optional[Position]:
        """Get hero's position."""
        for seat in state.seats:
            if seat.is_hero and seat.position:
                try:
                    return Position(seat.position)
                except ValueError:
                    continue
        return None
    
    def _openspiel_action_to_poker(self, openspiel_action: str, probability: float,
                                 game_context: Dict, state: TableState) -> Dict:
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
    
    def _enhanced_fallback_decision(self, state: TableState, strategy_name: str) -> GTOResponse:
        """Enhanced fallback decision using available analysis."""
        logger.warning("Using enhanced fallback decision")
        
        try:
            # Basic analysis even in fallback
            board_texture = self.board_analyzer.analyze_board(state.board)
            hero_position = self._get_hero_position(state)
            
            # Enhanced decision logic
            to_call = state.to_call or 0
            pot_odds = to_call / (state.pot + to_call) if (state.pot + to_call) > 0 else 0
            
            # Position-aware fallback
            if hero_position and hero_position in [Position.BTN, Position.CO, Position.HJ]:
                # Late position - more aggressive
                aggression_factor = 1.2
            else:
                # Early position - more conservative
                aggression_factor = 0.8
            
            # Board texture adjustment
            if board_texture.wetness_score > 0.7:
                # Wet board - more careful
                aggression_factor *= 0.9
            elif board_texture.wetness_score < 0.3:
                # Dry board - more aggressive
                aggression_factor *= 1.1
            
            # Basic decision with enhancements
            if not state.hero_hole:
                action = "Fold"
                size = 0
            elif to_call == 0:  # Can check
                if board_texture.high_card_score > 0.7 and hero_position in [Position.BTN, Position.CO]:
                    action = "Bet"
                    size = state.pot * 0.6 * aggression_factor
                else:
                    action = "Check"
                    size = 0
            elif pot_odds > 0.35:  # Poor pot odds
                action = "Fold"
                size = 0
            else:  # Acceptable pot odds
                if aggression_factor > 1.0:
                    action = "BetPlus"  # Raise
                    size = to_call + (state.pot * 0.7 * aggression_factor)
                else:
                    action = "Call"
                    size = to_call
            
            # Create enhanced decision
            decision = GTODecision(
                action=action, 
                size=size,
                size_bb=size / state.stakes.bb if state.stakes.bb > 0 else 0,
                size_pot_fraction=size / state.pot if state.pot > 0 else 0,
                confidence=0.3,  # Low confidence for fallback
                frequency=0.8,   # Conservative frequency
                reasoning="Enhanced fallback decision based on position and board texture"
            )
            
            # Enhanced metrics
            equity_breakdown = EquityBreakdown(
                raw_equity=0.5,
                fold_equity=0.2,
                realize_equity=0.45,
                vs_calling_range=0.4,
                vs_folding_range=0.6
            )
            
            metrics = GTOMetrics(
                equity_breakdown=equity_breakdown,
                min_call=to_call,
                min_bet=state.bet_min or state.stakes.bb,
                pot=state.pot,
                players=len([s for s in state.seats if s.in_hand]),
                spr=100.0,  # Default SPR
                effective_stack=1000.0,  # Default stack
                pot_odds=pot_odds,
                range_advantage=0.0,
                nut_advantage=0.0,
                bluff_catchers=0.5,
                board_favorability=0.5,
                positional_advantage=0.1 if hero_position in [Position.BTN, Position.CO] else -0.1,
                initiative=hero_position in [Position.BTN, Position.CO, Position.HJ] if hero_position else False,
                commitment_threshold=0.3,
                reverse_implied_odds=0.1
            )
            
            return GTOResponse(
                ok=True,
                decision=decision,
                metrics=metrics,
                strategy=strategy_name,
                computation_time_ms=0,
                exploitative_adjustments=["Enhanced fallback with position and board analysis"]
            )
            
        except Exception as e:
            logger.error(f"Enhanced fallback decision failed: {e}")
            # Ultimate fallback - simple decision
            decision = GTODecision(action="Check" if not state.to_call else "Fold", size=0)
            equity_breakdown = EquityBreakdown(
                raw_equity=0.5, fold_equity=0.0, realize_equity=0.5,
                vs_calling_range=0.5, vs_folding_range=0.5
            )
            metrics = GTOMetrics(
                equity_breakdown=equity_breakdown,
                min_call=state.to_call or 0,
                min_bet=state.bet_min or state.stakes.bb,
                pot=state.pot,
                players=len([s for s in state.seats if s.in_hand]),
                spr=0, effective_stack=0, pot_odds=0,
                range_advantage=0, nut_advantage=0, bluff_catchers=0,
                board_favorability=0, positional_advantage=0,
                initiative=False, commitment_threshold=0, reverse_implied_odds=0
            )
            return GTOResponse(ok=True, decision=decision, metrics=metrics, strategy=strategy_name, computation_time_ms=0)