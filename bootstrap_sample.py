#!/usr/bin/env python3
"""
Bootstrap Database Sample: Direct Access
Pull 5 random situations from the bootstrap database using direct access
"""

import sys
import os
import random
import sqlite3
sys.path.append('/home/runner/workspace')

def sample_bootstrap_database():
    """Sample bootstrap situations directly from SQLite database."""
    
    print("BOOTSTRAP DATABASE SAMPLE")
    print("5 Random Situations from Current Database")
    print("=" * 42)
    
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect('gto_database.db')
        cursor = conn.cursor()
        
        # Get total count
        cursor.execute("SELECT COUNT(*) FROM gto_situations")
        total = cursor.fetchone()[0]
        print(f"Total situations in database: {total}")
        
        if total == 0:
            print("Database is empty")
            return
        
        # Get 5 random samples
        cursor.execute("""
            SELECT situation_hash, situation_data, solution_data 
            FROM gto_situations 
            ORDER BY RANDOM() 
            LIMIT 5
        """)
        
        samples = cursor.fetchall()
        
        print(f"\nSAMPLE: 5 Random Bootstrap Situations")
        print("-" * 37)
        
        for i, (hash_val, situation_data, solution_data) in enumerate(samples, 1):
            print(f"\nSITUATION {i}:")
            print("-" * 12)
            print(f"Hash: {hash_val[:16]}...")
            print(f"Situation Data Length: {len(situation_data)} bytes")
            print(f"Solution Data Length: {len(solution_data)} bytes")
            
            # Try to parse the data (might be pickled or JSON)
            try:
                import json
                import pickle
                
                # Try JSON first
                try:
                    situation = json.loads(situation_data)
                    solution = json.loads(solution_data)
                    print("Format: JSON")
                except:
                    # Try pickle
                    try:
                        situation = pickle.loads(situation_data)
                        solution = pickle.loads(solution_data)
                        print("Format: Pickle")
                    except:
                        print("Format: Unknown binary format")
                        situation = None
                        solution = None
                
                if situation and solution:
                    print(f"\nSITUATION DETAILS:")
                    if hasattr(situation, '__dict__'):
                        for key, value in situation.__dict__.items():
                            print(f"  {key}: {value}")
                    elif isinstance(situation, dict):
                        for key, value in situation.items():
                            print(f"  {key}: {value}")
                    else:
                        print(f"  Raw: {str(situation)[:100]}...")
                    
                    print(f"\nSOLUTION DETAILS:")
                    if isinstance(solution, dict):
                        for key, value in solution.items():
                            if key == 'reasoning' and len(str(value)) > 50:
                                print(f"  {key}: {str(value)[:50]}...")
                            else:
                                print(f"  {key}: {value}")
                    else:
                        print(f"  Raw: {str(solution)[:100]}...")
                        
                    # Assess quality
                    decision = solution.get('decision', '') if isinstance(solution, dict) else 'unknown'
                    equity = solution.get('equity', 0) if isinstance(solution, dict) else 0
                    
                    print(f"\nQUALITY ASSESSMENT:")
                    if decision.lower() in ['fold', 'call', 'raise']:
                        print(f"  ✓ Valid decision format")
                        if isinstance(equity, (int, float)) and 0 <= equity <= 1:
                            print(f"  ✓ Valid equity range")
                        else:
                            print(f"  ✗ Invalid equity: {equity}")
                    else:
                        print(f"  ✗ Invalid decision: {decision}")
                        
            except Exception as e:
                print(f"Data parsing error: {str(e)}")
        
        conn.close()
        
    except Exception as e:
        print(f"Database access error: {str(e)}")
        
        # Fallback: try to access through the GTO database class
        try:
            from app.database.gto_database import gto_db
            if not gto_db.initialized:
                gto_db.initialize()
            print(f"\nFallback: GTO Database initialized with {len(getattr(gto_db, 'situations', {}))} situations")
        except Exception as e2:
            print(f"Fallback failed: {str(e2)}")

def analyze_bootstrap_value():
    """Analyze whether to keep bootstrap data."""
    print(f"\n\n" + "=" * 50)
    print("SHOULD WE KEEP THE 7K BOOTSTRAP SITUATIONS?")
    print("=" * 50)
    
    print("\nPROS OF KEEPING BOOTSTRAP DATA:")
    print("✓ System cold-start capability")
    print("✓ Fallback for extremely rare scenarios") 
    print("✓ Development testing infrastructure")
    print("✓ Minimal storage cost (~15MB)")
    print("✓ Proven HNSW indexing structure")
    print("✓ Database initialization without external dependencies")
    print()
    
    print("CONS OF KEEPING BOOTSTRAP DATA:")
    print("✗ 0% hit rate on realistic scenarios (as we just saw)")
    print("✗ May give poor recommendations if matched")
    print("✗ Could confuse users with low-quality advice")
    print("✗ Takes up vector space in similarity searches")
    print("✗ Maintenance overhead for obsolete data")
    print()
    
    print("RECOMMENDED APPROACH:")
    print("KEEP BOOTSTRAP AS 'TIER-3' FALLBACK")
    print()
    print("Tiered Database Strategy:")
    print("• Tier 1: TexasSolver CFR scenarios (search first)")
    print("• Tier 2: User-learned scenarios (search second)")  
    print("• Tier 3: Bootstrap scenarios (search last)")
    print("• CFR Computation: If no matches found")
    print()
    print("This gives us:")
    print("- Professional quality for common scenarios")
    print("- Personalized learning from user queries")
    print("- Ultimate fallback for edge cases")
    print("- System robustness and development support")
    print()
    
    print("IMPLEMENTATION:")
    print("1. Label bootstrap data with 'bootstrap' source tag")
    print("2. Search authentic data first (higher similarity threshold)")
    print("3. Search bootstrap data only if no good matches")
    print("4. Clearly indicate recommendation source to users")
    print("5. Priority: Build TexasSolver tier to replace bootstrap coverage")

if __name__ == "__main__":
    random.seed(42)  # Reproducible results
    sample_bootstrap_database()
    analyze_bootstrap_value()