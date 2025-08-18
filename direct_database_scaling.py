#!/usr/bin/env python3
"""
Direct database scaling using internal methods.
Bypasses API endpoints to directly populate database with strategic coverage.
"""

import sqlite3
import numpy as np
import time
import random
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.database.gto_database import GTODatabase, PokerSituation, Position, BettingRound

def generate_strategic_situations(count: int) -> list:
    """Generate strategic poker situations for comprehensive coverage."""
    situations = []
    
    # Research-based distribution
    street_counts = {
        BettingRound.PREFLOP: int(count * 0.40),
        BettingRound.FLOP: int(count * 0.35), 
        BettingRound.TURN: int(count * 0.15),
        BettingRound.RIVER: int(count * 0.10)
    }
    
    # Premium starting hands for preflop
    premium_hands = [
        ["As", "Ad"], ["Kh", "Kd"], ["Qc", "Qs"], ["Jd", "Jh"], ["Th", "Ts"],
        ["9s", "9d"], ["8h", "8c"], ["7s", "7d"], ["6h", "6c"], ["5s", "5d"],
        ["Ah", "Ks"], ["Ad", "Qh"], ["Ac", "Js"], ["As", "Th"], ["Kd", "Qh"],
        ["Kh", "Js"], ["Qs", "Jd"], ["Jh", "Ts"], ["Td", "9s"], ["9h", "8s"]
    ]
    
    # Board textures for postflop
    board_textures = {
        'dry': [["As", "7h", "2c"], ["Kd", "8s", "3h"], ["Qc", "9h", "4d"]],
        'wet': [["Ah", "Kh", "Qd"], ["9h", "8h", "7c"], ["Jd", "Td", "9s"]],
        'paired': [["As", "Ah", "7c"], ["Kd", "Ks", "9h"], ["8h", "8c", "3d"]]
    }
    
    positions = list(Position)
    
    for street, target_count in street_counts.items():
        print(f"Generating {target_count} {street.name} situations...")
        
        for _ in range(target_count):
            position = random.choice(positions)
            
            if street == BettingRound.PREFLOP:
                # Preflop situations
                if random.random() < 0.7:  # 70% premium hands
                    hole_cards = random.choice(premium_hands)
                else:
                    # Random hands for diversity
                    all_cards = [r + s for r in "AKQJT98765432" for s in "hdcs"]
                    hole_cards = random.sample(all_cards, 2)
                
                board_cards = []
                pot_size = random.choice([3.0, 4.5, 6.0, 9.0, 12.0])
                bet_to_call = random.choice([0, 2.0, 3.0, 6.0, 9.0])
                num_players = random.choice([6, 9])
                
            else:
                # Postflop situations
                texture_type = random.choice(list(board_textures.keys()))
                board_cards = random.choice(board_textures[texture_type]).copy()
                
                # Add turn/river cards if needed
                used_cards = board_cards.copy()
                available_cards = [c for c in [r + s for r in "AKQJT98765432" for s in "hdcs"] 
                                 if c not in used_cards]
                
                if street in [BettingRound.TURN, BettingRound.RIVER]:
                    turn_card = random.choice(available_cards)
                    board_cards.append(turn_card)
                    available_cards.remove(turn_card)
                    
                if street == BettingRound.RIVER:
                    river_card = random.choice(available_cards)
                    board_cards.append(river_card)
                    available_cards.remove(river_card)
                
                hole_cards = random.sample(available_cards, 2)
                
                # Escalating pot sizes
                base_pot = random.uniform(15, 50)
                if street == BettingRound.TURN:
                    base_pot *= 2.0
                elif street == BettingRound.RIVER:
                    base_pot *= 3.0
                    
                pot_size = round(base_pot, 1)
                bet_sizes = [0, 0.25, 0.5, 0.75, 1.0]
                bet_to_call = round(pot_size * random.choice(bet_sizes), 1)
                num_players = random.choice([2, 3, 4])
            
            stack_size = random.uniform(50, 200)
            
            situation = PokerSituation(
                hole_cards=hole_cards,
                board_cards=board_cards,
                position=position,
                pot_size=pot_size,
                bet_to_call=bet_to_call,
                stack_size=stack_size,
                num_players=num_players,
                betting_round=street
            )
            situations.append(situation)
    
    return situations

def scale_database_directly(target_size: int = 10000):
    """Scale database directly using internal methods."""
    print(f"🚀 DIRECT DATABASE SCALING TO {target_size:,}")
    print("Using internal GTO database methods for maximum efficiency")
    print("=" * 65)
    
    # Initialize database
    gto_db = GTODatabase()
    gto_db.initialize()
    
    # Get current count
    current_stats = gto_db.get_performance_stats()
    current_count = current_stats['total_situations']
    
    print(f"Current database size: {current_count:,} situations")
    
    if current_count >= target_size:
        print("✅ Database already at or above target size")
        return current_stats
    
    needed = target_size - current_count
    print(f"Need to add: {needed:,} situations")
    
    # Generate situations in efficient batches
    batch_size = 500
    total_added = 0
    start_time = time.time()
    
    while total_added < needed:
        current_batch_size = min(batch_size, needed - total_added)
        
        print(f"\nGenerating batch of {current_batch_size} strategic situations...")
        situations = generate_strategic_situations(current_batch_size)
        
        # Add to database
        batch_added = 0
        for i, situation in enumerate(situations):
            try:
                # Generate GTO solution
                solution = gto_db._generate_simple_gto_solution(situation)
                if solution:
                    success = gto_db.add_solution(situation, solution)
                    if success:
                        batch_added += 1
                        total_added += 1
                
                # Progress update
                if (i + 1) % 100 == 0:
                    progress = ((total_added) / needed) * 100
                    elapsed = time.time() - start_time
                    rate = total_added / elapsed if elapsed > 0 else 0
                    eta = (needed - total_added) / rate / 60 if rate > 0 else 0
                    print(f"   Progress: {total_added:,}/{needed:,} ({progress:.1f}%) - "
                          f"Rate: {rate:.1f}/sec - ETA: {eta:.1f}min")
                          
            except Exception as e:
                print(f"   Warning: Failed to add situation: {e}")
                continue
        
        print(f"✅ Batch complete: Added {batch_added}/{current_batch_size} situations")
        
        if batch_added < current_batch_size * 0.3:  # Less than 30% success
            print("⚠️ Low success rate detected, checking database...")
            time.sleep(1)
    
    # Final statistics
    total_time = time.time() - start_time
    final_stats = gto_db.get_performance_stats()
    final_count = final_stats['total_situations']
    
    print(f"\n🎯 DIRECT SCALING COMPLETE")
    print(f"   Added: {total_added:,} situations")
    print(f"   Final size: {final_count:,} situations")
    print(f"   Total time: {total_time:.1f} seconds")
    print(f"   Average rate: {total_added/total_time:.1f} situations/second")
    print(f"   Coverage: {(final_count/229671*100):.2f}% of theoretical poker space")
    print(f"   Database size: {final_stats['database_size_mb']:.1f}MB")
    print(f"   HNSW index: {final_stats['hnsw_index_size']:,} elements")
    
    # Test performance
    print(f"\n📊 PERFORMANCE VERIFICATION")
    test_situation = PokerSituation(
        hole_cards=["As", "Kd"],
        board_cards=[],
        position=Position.BTN,
        pot_size=10.0,
        bet_to_call=3.0,
        stack_size=100.0,
        num_players=6,
        betting_round=BettingRound.PREFLOP
    )
    
    test_start = time.time()
    result = gto_db.get_instant_recommendation(test_situation)
    test_time = (time.time() - test_start) * 1000
    
    if result:
        print(f"   ✅ Query test: {test_time:.1f}ms response time")
        print(f"   Decision: {result['decision']} ({result['confidence']:.2f} confidence)")
    else:
        print(f"   ⚠️ Query test failed")
    
    return final_stats

if __name__ == "__main__":
    result = scale_database_directly(10000)
    
    if result['total_situations'] >= 10000:
        print(f"\n🏆 SUCCESS: Database scaled to {result['total_situations']:,} situations")
        print("Ready for production with comprehensive coverage!")
    else:
        print(f"\n⚠️ Partial success: Reached {result['total_situations']:,} situations")
        print("May need additional optimization or troubleshooting")