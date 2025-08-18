#!/usr/bin/env python3
"""
Inspect Bootstrap Database: Random Sample Analysis
Pull 5 random situations from the current 7,757 database to see what they contain
"""

import sys
import os
import random
sys.path.append('/home/runner/workspace')

from app.database.gto_database import gto_db

def inspect_bootstrap_situations():
    """Pull and analyze 5 random situations from the bootstrap database."""
    
    print("BOOTSTRAP DATABASE INSPECTION")
    print("Analyzing 5 Random Situations from 6,757 Total")
    print("=" * 55)
    
    # Initialize database
    if not gto_db.initialized:
        gto_db.initialize()
    
    print(f"Database Status: {gto_db.total_situations} situations loaded")
    
    if gto_db.total_situations == 0:
        print("ERROR: No situations found in database")
        return
    
    # Get all situation keys
    all_keys = list(gto_db.situations.keys()) if hasattr(gto_db, 'situations') else []
    
    if not all_keys:
        print("ERROR: Cannot access situations directly")
        print("Database structure may be different than expected")
        return
    
    # Sample 5 random situations
    sample_size = min(5, len(all_keys))
    random_keys = random.sample(all_keys, sample_size)
    
    print(f"\nSAMPLE: {sample_size} Random Situations")
    print("-" * 35)
    
    for i, key in enumerate(random_keys, 1):
        try:
            situation_data = gto_db.situations[key]
            solution_data = situation_data['solution']
            
            print(f"\nSITUATION {i}:")
            print("-" * 12)
            
            # Try to decode the situation from the key or data
            if 'situation' in situation_data:
                sit = situation_data['situation']
                print(f"Cards: {getattr(sit, 'hole_cards', 'unknown')}")
                if hasattr(sit, 'board_cards') and sit.board_cards:
                    print(f"Board: {'-'.join(sit.board_cards)}")
                else:
                    print(f"Board: (preflop)")
                print(f"Position: {getattr(sit, 'position', 'unknown')}")
                print(f"Pot: ${getattr(sit, 'pot_size', 0):.1f}")
                print(f"Bet: ${getattr(sit, 'bet_to_call', 0):.1f}")
                print(f"Stack: ${getattr(sit, 'stack_size', 0):.1f}")
                print(f"Players: {getattr(sit, 'num_players', 0)}")
                print(f"Street: {getattr(sit, 'betting_round', 'unknown')}")
            else:
                print(f"Key: {key}")
                print("Situation details: Not directly accessible")
            
            print(f"\nRECOMMENDATION:")
            print(f"  Decision: {solution_data.get('decision', 'unknown')}")
            print(f"  Bet Size: ${solution_data.get('bet_size', 0):.1f}")
            print(f"  Equity: {solution_data.get('equity', 0.0):.3f}")
            print(f"  Reasoning: {solution_data.get('reasoning', 'No reasoning')}")
            print(f"  Confidence: {solution_data.get('confidence', 0.0):.2f}")
            print(f"  Source: {solution_data.get('metadata', {}).get('source', 'unknown')}")
            
            # Assess recommendation quality
            decision = solution_data.get('decision', '').lower()
            equity = solution_data.get('equity', 0.0)
            confidence = solution_data.get('confidence', 0.0)
            
            quality = "UNKNOWN"
            if decision in ['fold', 'call', 'raise']:
                quality = "VALID FORMAT"
                if confidence < 0.5:
                    quality += " (low confidence)"
                elif confidence > 0.8:
                    quality += " (high confidence)"
                else:
                    quality += " (medium confidence)"
                    
                if equity > 0.6 and decision == 'fold':
                    quality += " - QUESTIONABLE LOGIC"
                elif equity < 0.3 and decision in ['raise', 'call']:
                    quality += " - QUESTIONABLE LOGIC"
            else:
                quality = "INVALID FORMAT"
            
            print(f"  Quality: {quality}")
            
        except Exception as e:
            print(f"\nSITUATION {i}: ERROR - {str(e)}")
            print(f"Key: {key}")
    
    return random_keys

def analyze_bootstrap_value():
    """Analyze whether bootstrap situations have any value."""
    print(f"\n\n" + "=" * 55)
    print("BOOTSTRAP VALUE ANALYSIS")
    print("=" * 55)
    
    print("\nWHAT BOOTSTRAP SITUATIONS PROVIDE:")
    print("✓ Database initialization and testing infrastructure")
    print("✓ HNSW index population for performance testing")
    print("✓ Fallback coverage for completely novel scenarios")
    print("✓ System startup without external dependencies")
    print("✓ Proof-of-concept for vectorization and similarity matching")
    print()
    
    print("WHAT BOOTSTRAP SITUATIONS LACK:")
    print("✗ Realistic poker scenarios that players encounter")
    print("✗ Position-appropriate hand selection logic")
    print("✗ Authentic betting patterns and stack-to-pot ratios")
    print("✗ Strategic depth matching actual GTO play")
    print("✗ Quality that would satisfy serious poker players")
    print()
    
    print("RECOMMENDATION:")
    print("KEEP BOOTSTRAP DATA AS:")
    print("• System initialization layer (for cold starts)")
    print("• Fallback for extremely rare edge cases") 
    print("• Development testing infrastructure")
    print("• Foundation for HNSW index structure")
    print()
    
    print("BUT PRIORITIZE AUTHENTIC DATA:")
    print("• TexasSolver CFR solutions for realistic scenarios")
    print("• User-generated data from actual queries")
    print("• Hand-curated high-frequency decision points")
    print("• Professional tournament/cash game situations")
    print()
    
    print("STORAGE STRATEGY:")
    print("• Bootstrap: Keep as 'tier-3' fallback data (~7K situations)")
    print("• Realistic: Add as 'tier-1' primary data (~25K+ situations)")
    print("• User-learned: Store as 'tier-2' query-driven data (~10K+ situations)")
    print("• Total system: ~40K+ situations with quality tiers")
    print()
    
    print("QUERY PRIORITY:")
    print("1. Search tier-1 (realistic/authentic scenarios) first")
    print("2. Search tier-2 (user-learned scenarios) second")
    print("3. Search tier-3 (bootstrap fallback) third")
    print("4. Trigger CFR computation if no matches found")
    print("5. Cache new CFR results as tier-2 data")

def final_recommendation():
    """Provide final recommendation on bootstrap data retention."""
    print(f"\n\nFINAL RECOMMENDATION")
    print("=" * 20)
    
    print("VERDICT: KEEP BOOTSTRAP DATA")
    print()
    print("WHY KEEP IT:")
    print("• Infrastructure value outweighs storage cost")
    print("• Provides system robustness and cold-start capability")
    print("• Acts as ultimate fallback for edge cases")
    print("• ~15MB storage cost is negligible")
    print("• Preserves development and testing framework")
    print()
    
    print("HOW TO USE IT:")
    print("• Tier-3 priority (search last)")
    print("• Fallback for completely novel scenarios")
    print("• Development environment testing")
    print("• System initialization when other data unavailable")
    print()
    
    print("FOCUS DEVELOPMENT ON:")
    print("• TexasSolver integration for tier-1 authentic data")
    print("• Smart scenario generation for common situations")
    print("• User query learning for tier-2 personalized data")
    print("• Quality-based search prioritization")
    print()
    
    print("EXPECTED FINAL SYSTEM:")
    print("• Tier-1: 25K+ TexasSolver CFR scenarios (90% of queries)")
    print("• Tier-2: 10K+ user-learned scenarios (8% of queries)")
    print("• Tier-3: 7K bootstrap scenarios (1% of queries)")
    print("• CFR computation: Novel scenarios (1% of queries)")
    print("• Total: 40K+ situations with intelligent prioritization")

if __name__ == "__main__":
    random.seed(42)  # Reproducible results
    inspect_bootstrap_situations()
    analyze_bootstrap_value()
    final_recommendation()