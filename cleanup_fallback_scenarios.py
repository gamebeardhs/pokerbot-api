#!/usr/bin/env python3
"""
Cleanup Fallback Scenarios: Remove the 38K fallback templates and restore authentic database
"""

import sqlite3
import time

def cleanup_fallback_scenarios():
    """Remove all fallback scenarios from the database."""
    
    print("🧹 CLEANING UP FALLBACK SCENARIOS")
    print("=" * 33)
    
    try:
        conn = sqlite3.connect("gto_database.db")
        cursor = conn.cursor()
        
        # Check current state
        cursor.execute("SELECT COUNT(*) FROM gto_situations")
        before_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM gto_situations WHERE reasoning LIKE '%fallback%'")
        fallback_count = cursor.fetchone()[0]
        
        print(f"Current database: {before_count:,} total scenarios")
        print(f"Fallback scenarios to remove: {fallback_count:,}")
        
        # Remove fallback scenarios
        cursor.execute("DELETE FROM gto_situations WHERE reasoning LIKE '%fallback%'")
        deleted_count = cursor.rowcount
        
        # Check final state
        cursor.execute("SELECT COUNT(*) FROM gto_situations")
        after_count = cursor.fetchone()[0]
        
        conn.commit()
        conn.close()
        
        print(f"✅ Removed {deleted_count:,} fallback scenarios")
        print(f"✅ Database now contains {after_count:,} authentic scenarios")
        print(f"✅ Restored to clean state with original TexasSolver scenarios")
        
        return after_count
        
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")
        return 0

if __name__ == "__main__":
    final_count = cleanup_fallback_scenarios()
    print(f"\n🎯 Database cleanup complete: {final_count:,} authentic scenarios remaining")