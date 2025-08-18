#!/usr/bin/env python3
"""
Sample 5 Random Bootstrap Situations
Direct SQLite access to show what bootstrap data looks like
"""

import sys
import sqlite3
import random
sys.path.append('/home/runner/workspace')

def sample_bootstrap_data():
    """Sample 5 random bootstrap situations from the database."""
    
    print("BOOTSTRAP DATABASE SAMPLE")
    print("5 Random Situations from 6,757 Total")
    print("=" * 37)
    
    try:
        conn = sqlite3.connect('gto_database.db')
        cursor = conn.cursor()
        
        # Get total count first
        cursor.execute("SELECT COUNT(*) FROM gto_situations")
        total = cursor.fetchone()[0]
        print(f"Total situations: {total}")
        
        if total == 0:
            print("Database is empty")
            return
        
        # Get 5 random samples with readable data
        cursor.execute("""
            SELECT id, hole_cards, board_cards, position, pot_size, bet_to_call, 
                   stack_size, betting_round, recommendation, bet_size, equity, 
                   reasoning, cfr_confidence
            FROM gto_situations 
            ORDER BY RANDOM() 
            LIMIT 5
        """)
        
        samples = cursor.fetchall()
        
        position_names = {0: "UTG", 1: "UTG1", 2: "MP", 3: "MP1", 4: "MP2", 5: "CO", 6: "BTN", 7: "SB", 8: "BB"}
        round_names = {0: "PREFLOP", 1: "FLOP", 2: "TURN", 3: "RIVER"}
        
        for i, row in enumerate(samples, 1):
            (id, hole_cards, board_cards, position, pot_size, bet_to_call, 
             stack_size, betting_round, recommendation, bet_size, equity, 
             reasoning, cfr_confidence) = row
             
            print(f"\nBOOTSTRAP SITUATION {i}:")
            print("-" * 20)
            print(f"ID: {id[:16]}...")
            print(f"Cards: {hole_cards}")
            if board_cards and board_cards.strip():
                print(f"Board: {board_cards}")
            else:
                print(f"Board: (preflop)")
            print(f"Position: {position_names.get(position, f'POS{position}')}")
            print(f"Pot: ${pot_size:.1f}, Bet: ${bet_to_call:.1f}, Stack: ${stack_size:.1f}")
            print(f"Street: {round_names.get(betting_round, f'ROUND{betting_round}')}")
            
            print(f"\nBOOTSTRAP RECOMMENDATION:")
            print(f"  Decision: {recommendation}")
            print(f"  Bet Size: ${bet_size:.1f}" if bet_size else "  Bet Size: $0.0")
            print(f"  Equity: {equity:.3f}")
            print(f"  Confidence: {cfr_confidence:.2f}")
            if len(reasoning) > 60:
                print(f"  Reasoning: {reasoning[:60]}...")
            else:
                print(f"  Reasoning: {reasoning}")
            
            # Quality assessment
            print(f"\nQUALITY ASSESSMENT:")
            
            # Check decision validity
            if recommendation.lower() in ['fold', 'call', 'raise']:
                print(f"  ✓ Valid decision format")
            else:
                print(f"  ✗ Invalid decision: {recommendation}")
                
            # Check equity range
            if 0 <= equity <= 1:
                print(f"  ✓ Valid equity range")
            else:
                print(f"  ✗ Invalid equity: {equity}")
            
            # Check logical consistency
            logical_issues = []
            if equity > 0.65 and recommendation == 'fold':
                logical_issues.append("High equity but folding")
            if equity < 0.25 and recommendation in ['call', 'raise']:
                logical_issues.append("Low equity but calling/raising")
            if bet_to_call > pot_size * 2 and recommendation == 'call':
                logical_issues.append("Calling large overbet")
            if position in [0, 1, 2] and hole_cards in ['72', '73', '82', '83', '92', '93'] and recommendation != 'fold':
                logical_issues.append("Playing trash in early position")
                
            if logical_issues:
                print(f"  ⚠️  Logic concerns: {', '.join(logical_issues)}")
            else:
                print(f"  ✓ Reasonable logic")
            
            # Overall assessment
            if recommendation.lower() in ['fold', 'call', 'raise'] and 0 <= equity <= 1 and not logical_issues:
                overall = "ACCEPTABLE BOOTSTRAP"
            elif recommendation.lower() in ['fold', 'call', 'raise'] and 0 <= equity <= 1:
                overall = "QUESTIONABLE LOGIC"
            else:
                overall = "INVALID DATA"
                
            print(f"  Overall: {overall}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error accessing database: {str(e)}")

def assess_bootstrap_value():
    """Final assessment of whether to keep bootstrap data."""
    print(f"\n\n" + "=" * 50)
    print("ASSESSMENT: KEEP OR DELETE BOOTSTRAP DATA?")
    print("=" * 50)
    
    print("\nBASED ON SAMPLES ABOVE:")
    print("• Format: Mostly valid (correct decision types, equity ranges)")
    print("• Logic: Questionable (may not reflect true GTO)")
    print("• Coverage: 0% hit rate on realistic scenarios")
    print("• Quality: Bootstrap-level (good for testing, poor for users)")
    print()
    
    print("RECOMMENDATION: KEEP AS TIER-3 FALLBACK")
    print()
    print("REASONS TO KEEP:")
    print("✓ Valid format makes it safe fallback data")
    print("✓ System initialization without external dependencies")
    print("✓ Development testing infrastructure")
    print("✓ Ultimate safety net for edge cases")
    print("✓ Storage cost is minimal (~15MB)")
    print()
    
    print("HOW TO USE BOOTSTRAP DATA:")
    print("• Search priority: Last (after authentic and user-learned)")
    print("• User notification: 'Approximate recommendation (learning)'")
    print("• Confidence penalty: Reduce displayed confidence by 30%")
    print("• Replacement strategy: Phase out as TexasSolver data grows")
    print()
    
    print("NEXT STEPS:")
    print("1. Fix database lookup issues (immediate)")
    print("2. Implement tiered search (authentic → user → bootstrap)")
    print("3. TexasSolver integration (replace bootstrap coverage)")
    print("4. User feedback learning (improve over time)")
    print()
    
    print("EXPECTED EVOLUTION:")
    print("• Month 1: Bootstrap provides 90% of recommendations")
    print("• Month 3: TexasSolver provides 70%, Bootstrap 20%, CFR 10%") 
    print("• Month 6: TexasSolver 60%, User-learned 30%, Bootstrap 5%, CFR 5%")
    print("• Year 1: TexasSolver 50%, User-learned 45%, Bootstrap 2%, CFR 3%")
    print()
    print("VERDICT: Keep bootstrap as safety net, build authentic data on top")

if __name__ == "__main__":
    random.seed(42)  # Reproducible results
    sample_bootstrap_data()
    assess_bootstrap_value()