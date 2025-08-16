"""Tests for table state adapter functionality."""

import pytest
from app.api.models import TableState, Stakes, Seat
from app.advisor.adapter import TableStateAdapter


class TestTableStateAdapter:
    """Test suite for table state adapter."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.adapter = TableStateAdapter()
    
    def test_basic_adaptation(self):
        """Test basic table state adaptation to OpenSpiel format."""
        state = TableState(
            table_id="test-adapt-1",
            stakes=Stakes(sb=0.01, bb=0.02),
            street="FLOP",
            board=["kh", "9s", "2d"],
            hero_hole=["ah", "qs"],
            pot=0.20,
            to_call=0.10,
            bet_min=0.02,
            hero_seat=3,
            seats=[
                Seat(seat=1, stack=2.00, in_hand=True, put_in=0.05),
                Seat(seat=3, stack=1.90, in_hand=True, is_hero=True, put_in=0.05)
            ]
        )
        
        game_context = self.adapter.adapt_to_openspiel(state)
        
        # Verify basic structure
        assert game_context["game_type"] == "no_limit_holdem"
        assert game_context["num_players"] == 2
        assert game_context["street"] == 1  # FLOP = 1
        assert game_context["pot_size"] == 0.20
        assert game_context["to_call"] == 0.10
        assert game_context["big_blind"] == 0.02
        assert game_context["small_blind"] == 0.01
        
    def test_card_conversion(self):
        """Test card string to OpenSpiel integer conversion."""
        # Test various card formats
        test_cases = [
            (["ah"], [12 * 4 + 0]),  # Ace of hearts = rank 12, suit 0
            (["ks"], [11 * 4 + 3]),  # King of spades = rank 11, suit 3  
            (["2c"], [0 * 4 + 2]),   # Two of clubs = rank 0, suit 2
            (["td"], [8 * 4 + 1])    # Ten of diamonds = rank 8, suit 1
        ]
        
        for cards_str, expected in test_cases:
            result = self.adapter._convert_cards_to_openspiel(cards_str)
            assert result == expected, f"Failed for {cards_str}: got {result}, expected {expected}"
    
    def test_street_mapping(self):
        """Test street name to integer mapping."""
        test_states = [
            ("PREFLOP", 0),
            ("FLOP", 1), 
            ("TURN", 2),
            ("RIVER", 3)
        ]
        
        for street_name, expected_int in test_states:
            state = TableState(
                table_id="test",
                stakes=Stakes(sb=0.01, bb=0.02),
                street=street_name,
                pot=0.03,
                seats=[Seat(seat=1, stack=2.00, in_hand=True, is_hero=True)]
            )
            
            game_context = self.adapter.adapt_to_openspiel(state)
            assert game_context["street"] == expected_int
    
    def test_hero_identification(self):
        """Test hero seat identification."""
        # Test hero identified by is_hero flag
        state1 = TableState(
            table_id="test-hero-1",
            stakes=Stakes(sb=0.01, bb=0.02),
            street="PREFLOP",
            pot=0.03,
            seats=[
                Seat(seat=1, stack=2.00, in_hand=True),
                Seat(seat=3, stack=2.00, in_hand=True, is_hero=True),
                Seat(seat=6, stack=2.00, in_hand=True)
            ]
        )
        
        hero_seat = self.adapter._find_hero_seat(state1)
        assert hero_seat == 3
        
        # Test hero identified by hero_seat field
        state2 = TableState(
            table_id="test-hero-2", 
            stakes=Stakes(sb=0.01, bb=0.02),
            street="PREFLOP",
            hero_seat=6,
            pot=0.03,
            seats=[
                Seat(seat=1, stack=2.00, in_hand=True),
                Seat(seat=3, stack=2.00, in_hand=True),
                Seat(seat=6, stack=2.00, in_hand=True)
            ]
        )
        
        hero_seat = self.adapter._find_hero_seat(state2)
        assert hero_seat == 6
    
    def test_active_players_filtering(self):
        """Test filtering of active players."""
        state = TableState(
            table_id="test-active",
            stakes=Stakes(sb=0.01, bb=0.02),
            street="FLOP", 
            pot=0.20,
            seats=[
                Seat(seat=1, stack=2.00, in_hand=True),      # Active
                Seat(seat=2, stack=0.00, in_hand=False),     # Folded
                Seat(seat=3, stack=1.50, in_hand=True),      # Active  
                Seat(seat=4, stack=None, in_hand=True),      # No stack info
                Seat(seat=5, stack=1.80, in_hand=True),      # Active
                Seat(seat=6, stack=2.20, in_hand=False)      # Sitting out
            ]
        )
        
        active_players = self.adapter._get_active_players(state)
        
        # Should only include seats 1, 3, 5 (have stack and in_hand=True)
        assert len(active_players) == 3
        active_seats = [p.seat for p in active_players]
        assert active_seats == [1, 3, 5]  # Should be sorted by seat
    
    def test_pot_calculation(self):
        """Test pot size calculations."""
        state = TableState(
            table_id="test-pot",
            stakes=Stakes(sb=0.01, bb=0.02),
            street="FLOP",
            pot=0.15,      # Previous betting
            round_pot=0.08, # Current round contributions
            seats=[
                Seat(seat=1, stack=1.95, in_hand=True, put_in=0.04),
                Seat(seat=3, stack=1.96, in_hand=True, put_in=0.04, is_hero=True)
            ]
        )
        
        pot_info = self.adapter._calculate_pot_info(state)
        
        assert pot_info["total_pot"] == 0.15
        assert pot_info["round_pot"] == 0.08
        assert pot_info["effective_pot"] == 0.23
        
    def test_pot_calculation_no_round_pot(self):
        """Test pot calculation when round_pot is not provided."""
        state = TableState(
            table_id="test-pot-estimate",
            stakes=Stakes(sb=0.01, bb=0.02),
            street="TURN",
            pot=0.25,
            # round_pot not provided
            seats=[
                Seat(seat=1, stack=1.90, in_hand=True, put_in=0.05),
                Seat(seat=3, stack=1.88, in_hand=True, put_in=0.07, is_hero=True)
            ]
        )
        
        pot_info = self.adapter._calculate_pot_info(state)
        
        assert pot_info["total_pot"] == 0.25
        assert pot_info["round_pot"] == 0.12  # Sum of put_in values
        assert pot_info["effective_pot"] == 0.37
    
    def test_position_assignment_6max(self):
        """Test position assignment for 6-max table."""
        active_players = [
            Seat(seat=1, stack=2.0, in_hand=True),  # Should be UTG
            Seat(seat=2, stack=2.0, in_hand=True),  # Should be MP
            Seat(seat=4, stack=2.0, in_hand=True),  # Should be CO  
            Seat(seat=5, stack=2.0, in_hand=True),  # Should be BTN
            Seat(seat=6, stack=2.0, in_hand=True),  # Should be SB
            Seat(seat=7, stack=2.0, in_hand=True),  # Should be BB
        ]
        
        positions = self.adapter._assign_positions(active_players, max_seats=9)
        
        # Verify positions are assigned
        assert len(positions) == 6
        assert all(pos in ["UTG", "MP", "CO", "BTN", "SB", "BB", "UTG+1", "UTG+2", "LJ", "HJ"] 
                  for pos in positions.values())
    
    def test_position_assignment_heads_up(self):
        """Test position assignment for heads-up play."""
        active_players = [
            Seat(seat=2, stack=2.0, in_hand=True),
            Seat(seat=6, stack=2.0, in_hand=True)
        ]
        
        positions = self.adapter._assign_positions(active_players, max_seats=6)
        
        assert len(positions) == 2
        position_values = list(positions.values())
        assert "SB" in position_values
        assert "BB" in position_values
    
    def test_invalid_card_handling(self):
        """Test handling of invalid card strings."""
        invalid_cards = ["", "x", "ah2", "zz", "10h"]
        result = self.adapter._convert_cards_to_openspiel(invalid_cards)
        
        # Should filter out invalid cards and return empty list
        assert result == []
    
    def test_empty_state_handling(self):
        """Test handling of minimal/empty table state."""
        minimal_state = TableState(
            table_id="minimal",
            stakes=Stakes(sb=0.01, bb=0.02),
            street="PREFLOP",
            pot=0.03,
            seats=[Seat(seat=1, stack=2.00, in_hand=True, is_hero=True)]
        )
        
        # Should not raise exception
        game_context = self.adapter.adapt_to_openspiel(minimal_state)
        
        # Basic validation
        assert game_context["num_players"] == 1
        assert game_context["street"] == 0
        assert game_context["hero_cards"] == []  # No hero cards provided
        assert game_context["board_cards"] == []  # No board
