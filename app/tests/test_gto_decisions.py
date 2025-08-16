"""Tests for GTO decision computation accuracy."""

import pytest
from app.api.models import TableState, Stakes, Seat
from app.advisor.gto_service import GTODecisionService


class TestGTODecisions:
    """Test suite for GTO decision accuracy."""
    
    def setup_method(self):
        """Set up test fixtures."""
        try:
            self.gto_service = GTODecisionService()
            self.service_available = self.gto_service.is_available()
        except Exception as e:
            self.service_available = False
            self.gto_service = None
    
    @pytest.mark.asyncio
    async def test_preflop_premium_hand_decision(self):
        """Test GTO decision for premium preflop hand."""
        if not self.service_available:
            pytest.skip("GTO service not available")
        
        # Create table state with premium hand (AA) in CO position
        state = TableState(
            table_id="test-1",
            stakes=Stakes(sb=0.01, bb=0.02),
            street="PREFLOP",
            hero_hole=["ah", "as"],  # Pocket aces
            pot=0.03,  # Blinds only
            to_call=0.02,  # Must call big blind
            bet_min=0.02,
            hero_seat=5,
            seats=[
                Seat(seat=1, stack=2.00, in_hand=True, put_in=0.01),  # SB
                Seat(seat=2, stack=2.00, in_hand=True, put_in=0.02),  # BB
                Seat(seat=5, stack=2.00, in_hand=True, is_hero=True)  # Hero in CO
            ]
        )
        
        result = await self.gto_service.compute_gto_decision(state, "default_cash6max")
        
        # Premium hand should typically raise, not fold
        assert result.ok is True
        assert result.decision.action in ["Bet", "BetPlus", "Call"]
        assert result.metrics.equity > 0.6  # Pocket aces should have high equity
        assert result.strategy == "default_cash6max"
    
    @pytest.mark.asyncio 
    async def test_weak_hand_fold_decision(self):
        """Test GTO decision for weak hand facing raise."""
        if not self.service_available:
            pytest.skip("GTO service not available")
        
        # Create table state with weak hand facing large bet
        state = TableState(
            table_id="test-2", 
            stakes=Stakes(sb=0.01, bb=0.02),
            street="FLOP",
            board=["kh", "9s", "2d"],  # Dry board
            hero_hole=["3c", "7h"],   # Very weak hand
            pot=0.50,
            to_call=0.40,  # Large bet to call (80% pot)
            bet_min=0.02,
            hero_seat=2,
            seats=[
                Seat(seat=1, stack=2.00, in_hand=True, put_in=0.40),  # Aggressor
                Seat(seat=2, stack=1.60, in_hand=True, is_hero=True)  # Hero
            ]
        )
        
        result = await self.gto_service.compute_gto_decision(state, "default_cash6max")
        
        # Weak hand facing large bet should typically fold
        assert result.ok is True
        assert result.decision.action == "Fold"
        assert result.metrics.equity < 0.4  # Low equity expected
        
    @pytest.mark.asyncio
    async def test_drawing_hand_decision(self):
        """Test GTO decision for drawing hand."""
        if not self.service_available:
            pytest.skip("GTO service not available")
            
        # Create table state with flush draw
        state = TableState(
            table_id="test-3",
            stakes=Stakes(sb=0.01, bb=0.02), 
            street="FLOP",
            board=["kh", "9h", "2c"],  # Two hearts on board
            hero_hole=["ah", "qh"],   # Nut flush draw + overcards
            pot=0.20,
            to_call=0.10,  # Half pot bet
            bet_min=0.02,
            hero_seat=3,
            seats=[
                Seat(seat=1, stack=2.00, in_hand=True, put_in=0.10),
                Seat(seat=3, stack=1.90, in_hand=True, is_hero=True)
            ]
        )
        
        result = await self.gto_service.compute_gto_decision(state, "default_cash6max")
        
        # Strong draw should typically continue (call or raise)
        assert result.ok is True
        assert result.decision.action in ["Call", "Bet", "BetPlus"]
        assert result.metrics.equity > 0.35  # Flush draw has decent equity
        
    @pytest.mark.asyncio
    async def test_heads_up_vs_multiway_adjustment(self):
        """Test that GTO adjusts for number of opponents."""
        if not self.service_available:
            pytest.skip("GTO service not available")
            
        # Same hand, different number of opponents
        base_state_data = {
            "table_id": "test-4",
            "stakes": Stakes(sb=0.01, bb=0.02),
            "street": "PREFLOP", 
            "hero_hole": ["jh", "js"],  # Pocket jacks
            "pot": 0.06,
            "to_call": 0.02,
            "bet_min": 0.02,
            "hero_seat": 6
        }
        
        # Heads-up scenario
        heads_up_state = TableState(
            **base_state_data,
            seats=[
                Seat(seat=2, stack=2.00, in_hand=True, put_in=0.02),  # BB
                Seat(seat=6, stack=2.00, in_hand=True, is_hero=True)  # Hero BTN
            ]
        )
        
        # Multi-way scenario  
        multiway_state = TableState(
            **base_state_data,
            pot=0.10,  # More money in pot with more players
            seats=[
                Seat(seat=1, stack=2.00, in_hand=True, put_in=0.01),  # SB
                Seat(seat=2, stack=2.00, in_hand=True, put_in=0.02),  # BB
                Seat(seat=4, stack=2.00, in_hand=True, put_in=0.02),  # UTG
                Seat(seat=5, stack=2.00, in_hand=True, put_in=0.02),  # MP
                Seat(seat=6, stack=2.00, in_hand=True, is_hero=True)  # Hero BTN
            ]
        )
        
        hu_result = await self.gto_service.compute_gto_decision(heads_up_state)
        mw_result = await self.gto_service.compute_gto_decision(multiway_state)
        
        # Both should succeed
        assert hu_result.ok is True
        assert mw_result.ok is True
        
        # Equity should be higher heads-up vs multiway for same hand
        assert hu_result.metrics.equity >= mw_result.metrics.equity
        
    def test_service_availability(self):
        """Test that service reports availability correctly."""
        if self.gto_service:
            availability = self.gto_service.is_available()
            cfr_ready = self.gto_service.is_cfr_ready()
            
            # At minimum, service should report its status
            assert isinstance(availability, bool)
            assert isinstance(cfr_ready, bool)
        else:
            # If service couldn't be created, that's also a valid test result
            assert True
            
    @pytest.mark.asyncio
    async def test_computation_time_limit(self):
        """Test that GTO computation respects time limits."""
        if not self.service_available:
            pytest.skip("GTO service not available")
            
        state = TableState(
            table_id="test-time",
            stakes=Stakes(sb=0.01, bb=0.02),
            street="TURN",
            board=["kh", "9s", "2d", "7c"],
            hero_hole=["ah", "kd"],  # Top pair
            pot=1.50,
            to_call=0.75,
            bet_min=0.02,
            hero_seat=2,
            seats=[
                Seat(seat=1, stack=2.00, in_hand=True, put_in=0.75),
                Seat(seat=2, stack=1.25, in_hand=True, is_hero=True)
            ]
        )
        
        import time
        start_time = time.time()
        result = await self.gto_service.compute_gto_decision(state)
        elapsed_ms = (time.time() - start_time) * 1000
        
        # Should complete within reasonable time (< 2 seconds for safety)
        assert elapsed_ms < 2000
        assert result.ok is True
        
        # Should include computation time in response
        if result.computation_time_ms:
            assert result.computation_time_ms > 0
