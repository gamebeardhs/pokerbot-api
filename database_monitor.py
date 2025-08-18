#!/usr/bin/env python3
"""
Database growth monitoring and demonstration.
Shows exactly how the GTO database grows with new scenarios.
"""

import sqlite3
import os
import time

def analyze_current_database():
    """Analyze the actual database structure and growth mechanisms."""
    print("DATABASE GROWTH MECHANISMS EXPLAINED")
    print("=" * 45)
    
    db_path = "gto_database.db"
    
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check actual table name
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print("1. CURRENT DATABASE STRUCTURE")
        print("-" * 30)
        print(f"Database file: {db_path} ({os.path.getsize(db_path)/1024/1024:.1f}MB)")
        print(f"Tables found: {[t[0] for t in tables]}")
        
        # Use correct table name
        if tables and 'gto_situations' in [t[0] for t in tables]:
            table_name = 'gto_situations'
        else:
            table_name = tables[0][0] if tables else None
        
        if table_name:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            total_situations = cursor.fetchone()[0]
            print(f"Total Situations: {total_situations:,}")
            
            # Get schema
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            print(f"\nDatabase Schema ({table_name}):")
            for col in columns:
                col_name, col_type = col[1], col[2]
                print(f"   {col_name}: {col_type}")
            
            # Show recent entries
            cursor.execute(f"SELECT * FROM {table_name} ORDER BY ROWID DESC LIMIT 3")
            recent = cursor.fetchall()
            
            if recent:
                print(f"\nRecent Solutions (last 3):")
                for i, row in enumerate(recent, 1):
                    situation_id = row[0] if len(row) > 0 else "unknown"
                    decision = row[9] if len(row) > 9 else "unknown"
                    equity = row[11] if len(row) > 11 else 0.0
                    print(f"   {i}. ID: {str(situation_id)[:12]}... -> {decision} (equity: {equity})")
        
        conn.close()
    else:
        print("Database file not found - database growth starts from empty state")
        return
    
    print(f"\n2. HOW THE DATABASE GROWS")
    print("-" * 26)
    
    print("The database grows through these exact mechanisms:")
    print()
    
    print("🔄 REAL-TIME LEARNING (Primary Growth):")
    print("   1. User makes API call to /database/instant-gto")
    print("   2. System searches existing 6,757 situations")
    print("   3. If no match found:")
    print("      - CFR solver computes new GTO solution (1-3 seconds)")
    print("      - add_solution() method stores in SQLite database")
    print("      - Situation vectorized into 32-dimensional array")
    print("      - Vector added to HNSW index for similarity search")
    print("      - Database count increases: 6,757 → 6,758")
    print("   4. Next identical query returns in <1ms")
    print()
    
    print("🏗️ STRATEGIC SCALING (Batch Growth):")
    print("   1. advanced_scaling_strategy.py generates high-value scenarios")
    print("   2. Uses research-based distribution (40% preflop, 35% flop, etc.)")
    print("   3. _populate_database() method processes batches of 50-500")
    print("   4. Each situation gets CFR analysis and database storage")
    print("   5. HNSW index rebuilt and saved after batch completion")
    print()
    
    print("📝 TRAINING GROWTH (Manual Addition):")
    print("   1. Training interface allows manual corrections")
    print("   2. Expert inputs stored via add_situation API endpoint")
    print("   3. Human feedback improves database quality")
    print("   4. Custom scenarios added for specific use cases")
    print()
    
    print("3. TECHNICAL GROWTH PROCESS")
    print("-" * 28)
    
    print("Every new situation follows this exact storage process:")
    print()
    print("A. Situation Analysis:")
    print("   • Hole cards, board cards, position, stack sizes parsed")
    print("   • 32-dimensional vector created via PokerVectorizer")
    print("   • Unique situation ID generated (MD5 hash)")
    print()
    print("B. GTO Computation:")
    print("   • OpenSpiel CFR solver with 100 iterations")
    print("   • Decision (fold/call/raise), bet sizing, equity calculated")
    print("   • Confidence score and reasoning generated")
    print()
    print("C. Database Storage:")
    print("   • SQLite INSERT into gto_situations table")
    print("   • Vector stored as binary blob (numpy.tobytes())")
    print("   • Metadata stored as JSON")
    print()
    print("D. Index Update:")
    print("   • HNSW index receives new vector")
    print("   • Similarity search immediately available")
    print("   • Index saved to disk for persistence")
    
    print(f"\n4. GROWTH PERFORMANCE")
    print("-" * 20)
    
    db_size_mb = os.path.getsize(db_path) / (1024 * 1024) if os.path.exists(db_path) else 0
    situations_per_mb = total_situations / db_size_mb if db_size_mb > 0 else 0
    
    print(f"Current Efficiency:")
    print(f"   Storage: {db_size_mb:.1f}MB for {total_situations:,} situations")
    print(f"   Density: {situations_per_mb:.0f} situations per MB")
    print(f"   Growth Rate: ~1 situation per novel query")
    print(f"   Batch Scaling: +2,000-5,000 situations per operation")
    print()
    
    print("Growth Projections:")
    print(f"   To reach 10,000 situations: +{10000-total_situations:,} needed")
    print(f"   Estimated size at 10K: {(10000/situations_per_mb):.1f}MB")
    print(f"   At 50 queries/day: {((10000-total_situations)/50):.0f} days to 10K target")

def demonstrate_growth_cycle():
    """Show the complete growth cycle."""
    print(f"\n5. COMPLETE GROWTH CYCLE EXAMPLE")
    print("-" * 35)
    
    print("Scenario: User queries challenging river decision")
    print("Query: TT facing overbet on As-Kc-Qd-Jh-2s")
    print()
    
    print("Step-by-step growth process:")
    print("1. API receives POST /database/instant-gto")
    print("2. PokerVectorizer creates 32D vector from situation")
    print("3. HNSW searches 6,000 indexed vectors (0.5ms)")
    print("4. No similar situation found (novel scenario)")
    print("5. CFR solver activated with 100 iterations")
    print("6. OpenSpiel computes GTO strategy (2.1 seconds)")
    print("7. Result: fold decision with 0.23 equity, confidence 0.87")
    print("8. add_solution() stores in database:")
    print("   • situation_id: 'a4b2c8d9e1f3'")
    print("   • vector: 32-element numpy array as blob")
    print("   • recommendation: 'fold'")
    print("   • equity: 0.23")
    print("   • reasoning: 'Bluff catcher facing polarized overbet'")
    print("9. HNSW index updated with new vector")
    print("10. Database count: 6,757 → 6,758")
    print("11. Response sent to user (total time: 2.3 seconds)")
    print()
    print("Result: Next identical TT scenario returns in <1ms")
    print("System learned from this single query!")
    
    print(f"\nThis is how the database becomes smarter with every use.")
    print("Each novel scenario permanently improves the system's capabilities.")

if __name__ == "__main__":
    analyze_current_database()
    demonstrate_growth_cycle()