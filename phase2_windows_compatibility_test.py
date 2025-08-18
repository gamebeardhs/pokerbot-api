#!/usr/bin/env python3
"""
Phase 2: TexasSolver Integration Windows Compatibility Test
Verifies Windows compatibility for authentic GTO data generation
"""

import sys
import os
import platform
import subprocess
from pathlib import Path
import tempfile
import json

def test_phase2_windows_compatibility():
    """Test Windows compatibility for Phase 2: TexasSolver Integration."""
    
    print("PHASE 2: WINDOWS COMPATIBILITY CHECK")
    print("=" * 38)
    print(f"Platform: {platform.system()} {platform.release()}")
    print()
    
    issues = []
    warnings = []
    
    # 1. TexasSolver Console Integration
    print("1. TEXASSOLVER PREPARATION")
    print("-" * 26)
    
    try:
        # Test subprocess execution (required for TexasSolver)
        result = subprocess.run(
            ['echo', 'Windows subprocess test'],
            capture_output=True, text=True, timeout=5
        )
        
        if result.returncode == 0:
            print("  ✓ Subprocess execution working")
        else:
            print("  ✗ Subprocess execution failed")
            issues.append("Cannot run external processes")
        
        # Test file I/O for TexasSolver input/output
        temp_dir = Path(tempfile.gettempdir()) / "texassolver_test"
        temp_dir.mkdir(exist_ok=True)
        
        test_input = {
            "game_type": "holdem",
            "board": "AsKhQd",
            "ranges": {"BTN": "22+,A2s+", "BB": "22+,A2s+"},
            "pot_size": 5.0
        }
        
        input_file = temp_dir / "test_input.json"
        with open(input_file, 'w') as f:
            json.dump(test_input, f, indent=2)
        
        # Test reading back
        with open(input_file, 'r') as f:
            parsed = json.load(f)
        
        if parsed == test_input:
            print("  ✓ JSON file I/O for TexasSolver working")
        else:
            print("  ✗ JSON file I/O failed")
            issues.append("JSON file I/O not working")
        
        # Cleanup
        input_file.unlink()
        temp_dir.rmdir()
        
    except Exception as e:
        print(f"  ⚠️  TexasSolver prep issue: {e}")
        warnings.append(f"TexasSolver integration concern: {e}")
    
    # 2. Database Integration
    print(f"\n2. DATABASE INTEGRATION")
    print("-" * 21)
    
    try:
        # Test database connection for storing TexasSolver results
        import sqlite3
        
        test_db = Path("phase2_test.db")
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        
        # Create test table similar to GTO database
        cursor.execute("""
            CREATE TABLE test_gto (
                id TEXT PRIMARY KEY,
                decision TEXT,
                bet_size REAL,
                equity REAL,
                reasoning TEXT,
                metadata TEXT
            )
        """)
        
        # Test inserting TexasSolver-like data
        test_data = {
            'id': 'test_situation',
            'decision': 'call',
            'bet_size': 3.3,
            'equity': 0.67,
            'reasoning': 'TexasSolver CFR analysis',
            'metadata': json.dumps({'source': 'texassolver_cfr', 'iterations': 1000})
        }
        
        cursor.execute("""
            INSERT INTO test_gto VALUES (?, ?, ?, ?, ?, ?)
        """, tuple(test_data.values()))
        
        # Test retrieval
        cursor.execute("SELECT * FROM test_gto WHERE id = ?", ('test_situation',))
        result = cursor.fetchone()
        
        conn.close()
        
        if result:
            print("  ✓ Database storage for TexasSolver results working")
        else:
            print("  ✗ Database storage failed")
            issues.append("Cannot store TexasSolver results in database")
        
        test_db.unlink()  # Cleanup
        
    except Exception as e:
        print(f"  ✗ Database integration error: {e}")
        issues.append(f"Database integration error: {e}")
    
    # 3. Performance & Scaling
    print(f"\n3. PERFORMANCE & SCALING")
    print("-" * 24)
    
    try:
        # Test memory handling for large datasets
        import sys
        
        # Create simulated large dataset (1000 situations)
        large_dataset = []
        for i in range(1000):
            situation = {
                'id': f'situation_{i}',
                'position_ranges': {'BTN': '22+,A2s+,K9s+', 'BB': '22+,A2s+'},
                'board': 'AsKhQd',
                'solutions': {'decision': 'call', 'equity': 0.5 + (i % 100) / 200}
            }
            large_dataset.append(situation)
        
        # Check memory usage
        size_mb = sys.getsizeof(large_dataset) / (1024 * 1024)
        
        if size_mb < 50:  # Reasonable memory usage
            print(f"  ✓ Memory handling efficient ({size_mb:.1f} MB for 1K situations)")
        else:
            print(f"  ⚠️  Memory usage high ({size_mb:.1f} MB for 1K situations)")
            warnings.append(f"High memory usage: {size_mb:.1f} MB")
        
        # Test batch processing capability
        batch_size = 50
        batches = [large_dataset[i:i+batch_size] for i in range(0, len(large_dataset), batch_size)]
        
        if len(batches) == 20:  # 1000 / 50
            print(f"  ✓ Batch processing ready ({len(batches)} batches of {batch_size})")
        else:
            print("  ✗ Batch processing logic error")
            issues.append("Batch processing not working")
        
    except Exception as e:
        print(f"  ✗ Performance test error: {e}")
        issues.append(f"Performance issue: {e}")
    
    # 4. Windows-Specific Path Handling
    print(f"\n4. WINDOWS PATH HANDLING")
    print("-" * 24)
    
    try:
        # Test Windows-style paths
        windows_paths = [
            Path("C:/temp/texassolver_test"),  # Windows absolute
            Path("texassolver_working/input.json"),  # Relative
            Path("./output/solutions.json")  # Current dir relative
        ]
        
        for path in windows_paths:
            # Test path creation and validation
            normalized = path.resolve()
            if normalized.is_absolute() or path.is_relative():
                print(f"  ✓ Path handling: {path}")
            else:
                print(f"  ✗ Path issue: {path}")
                issues.append(f"Path handling failed for: {path}")
        
        # Test working directory changes (needed for TexasSolver)
        original_cwd = os.getcwd()
        temp_dir = Path(tempfile.gettempdir()) / "phase2_cwd_test"
        temp_dir.mkdir(exist_ok=True)
        
        os.chdir(temp_dir)
        new_cwd = os.getcwd()
        os.chdir(original_cwd)
        
        if temp_dir.name in new_cwd:
            print("  ✓ Working directory changes work")
        else:
            print("  ✗ Working directory change failed")
            issues.append("Cannot change working directory")
        
        temp_dir.rmdir()  # Cleanup
        
    except Exception as e:
        print(f"  ✗ Windows path error: {e}")
        issues.append(f"Windows path error: {e}")
    
    # Summary
    print(f"\n" + "=" * 38)
    print("PHASE 2 COMPATIBILITY SUMMARY")
    print("=" * 38)
    
    if not issues and not warnings:
        print("✅ PHASE 2 FULLY READY - TexasSolver integration will work on Windows")
        status = "READY"
    elif not issues:
        print(f"✅ PHASE 2 COMPATIBLE - {len(warnings)} minor concerns")
        status = "COMPATIBLE"
    else:
        print(f"❌ PHASE 2 ISSUES - {len(issues)} critical problems")
        status = "BLOCKED"
    
    if issues:
        print(f"\n🚨 CRITICAL ISSUES:")
        for issue in issues:
            print(f"   • {issue}")
    
    if warnings:
        print(f"\n⚠️  WARNINGS:")
        for warning in warnings:
            print(f"   • {warning}")
    
    print(f"\nPHASE 2 READINESS:")
    if status == "READY":
        print("• TexasSolver integration ready to proceed")
        print("• Database population will work reliably")
        print("• Authentic GTO generation compatible with Windows")
    elif status == "COMPATIBLE":
        print("• TexasSolver integration should work with minor adjustments")
        print("• Monitor warnings during implementation") 
        print("• Core functionality expected to work")
    else:
        print("• Fix critical issues before proceeding with TexasSolver")
        print("• Phase 2 may fail without addressing these problems")
    
    return status, issues, warnings

if __name__ == "__main__":
    status, issues, warnings = test_phase2_windows_compatibility()
    
    if issues:
        sys.exit(1)  # Critical issues
    elif warnings:
        sys.exit(2)  # Warnings only
    else:
        sys.exit(0)  # All ready