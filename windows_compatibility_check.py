#!/usr/bin/env python3
"""
Windows Compatibility Sanity Check
Tests all major system components for Windows compatibility
"""

import sys
import os
import platform
import json
from pathlib import Path

def check_windows_compatibility():
    """Comprehensive Windows compatibility check."""
    
    print("WINDOWS COMPATIBILITY SANITY CHECK")
    print("=" * 38)
    print(f"Platform: {platform.system()} {platform.release()}")
    print(f"Python: {sys.version}")
    print(f"Working Directory: {os.getcwd()}")
    print()
    
    issues_found = []
    warnings = []
    
    # 1. Path Compatibility
    print("1. PATH COMPATIBILITY")
    print("-" * 20)
    try:
        # Test Windows path handling
        test_paths = [
            Path("app/database/gto_database.py"),
            Path("gto_database.db"),
            Path("gto_index.bin")
        ]
        
        for path in test_paths:
            if path.exists():
                print(f"  ✓ Path accessible: {path}")
            else:
                print(f"  ⚠️  Path not found: {path}")
                warnings.append(f"Missing file: {path}")
        
        # Test path creation
        test_dir = Path("temp_windows_test")
        test_dir.mkdir(exist_ok=True)
        test_file = test_dir / "test.txt"
        test_file.write_text("Windows compatibility test")
        
        if test_file.read_text() == "Windows compatibility test":
            print("  ✓ File I/O working")
        else:
            print("  ✗ File I/O failed")
            issues_found.append("File I/O not working")
        
        # Cleanup
        test_file.unlink()
        test_dir.rmdir()
        
    except Exception as e:
        print(f"  ✗ Path compatibility error: {e}")
        issues_found.append(f"Path error: {e}")
    
    # 2. Database Compatibility
    print(f"\n2. DATABASE COMPATIBILITY")
    print("-" * 25)
    try:
        import sqlite3
        
        # Test SQLite on Windows
        test_db = Path("windows_test.db")
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        
        cursor.execute("CREATE TABLE test (id INTEGER, data TEXT)")
        cursor.execute("INSERT INTO test VALUES (1, 'Windows test')")
        cursor.execute("SELECT * FROM test")
        result = cursor.fetchone()
        
        conn.close()
        
        if result == (1, 'Windows test'):
            print("  ✓ SQLite working on Windows")
        else:
            print("  ✗ SQLite query failed")
            issues_found.append("SQLite not working")
        
        test_db.unlink()  # Cleanup
        
    except Exception as e:
        print(f"  ✗ Database error: {e}")
        issues_found.append(f"Database error: {e}")
    
    # 3. Dependencies Check
    print(f"\n3. DEPENDENCIES CHECK")
    print("-" * 21)
    
    required_modules = [
        'fastapi', 'uvicorn', 'pydantic', 'numpy', 
        'sqlite3', 'threading', 'asyncio'
    ]
    
    optional_modules = [
        'hnswlib', 'nest_asyncio', 'pyautogui'
    ]
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"  ✓ Required: {module}")
        except ImportError:
            print(f"  ✗ Missing: {module}")
            issues_found.append(f"Missing required module: {module}")
    
    for module in optional_modules:
        try:
            __import__(module)
            print(f"  ✓ Optional: {module}")
        except ImportError:
            print(f"  ⚠️  Optional: {module} not available")
            warnings.append(f"Optional module missing: {module}")
    
    # 4. TexasSolver Integration Check
    print(f"\n4. TEXASSOLVER PREPARATION")
    print("-" * 26)
    try:
        # Check if we can run console commands
        import subprocess
        
        # Test basic subprocess capability
        result = subprocess.run(['python', '--version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("  ✓ Console command execution working")
        else:
            print("  ✗ Console command execution failed")
            issues_found.append("Cannot execute console commands")
        
        # Check JSON handling for TexasSolver output
        test_json = {"test": "data", "array": [1, 2, 3]}
        json_str = json.dumps(test_json)
        parsed = json.loads(json_str)
        
        if parsed == test_json:
            print("  ✓ JSON processing working")
        else:
            print("  ✗ JSON processing failed")
            issues_found.append("JSON processing not working")
        
    except Exception as e:
        print(f"  ⚠️  TexasSolver prep warning: {e}")
        warnings.append(f"TexasSolver prep issue: {e}")
    
    # 5. Async Compatibility
    print(f"\n5. ASYNC COMPATIBILITY")
    print("-" * 20)
    try:
        import asyncio
        
        # Test basic async functionality
        async def test_async():
            return "async working"
        
        # Try to run async test
        if hasattr(asyncio, 'get_event_loop'):
            try:
                loop = asyncio.get_event_loop()
                result = loop.run_until_complete(test_async())
                if result == "async working":
                    print("  ✓ Basic async functionality working")
                else:
                    print("  ✗ Async test failed")
                    issues_found.append("Async not working")
            except Exception as loop_error:
                print(f"  ⚠️  Event loop issue: {loop_error}")
                warnings.append(f"Event loop issue: {loop_error}")
        else:
            print("  ⚠️  Legacy async handling needed")
            warnings.append("Legacy async handling needed")
        
        # Test nest_asyncio specifically
        try:
            import nest_asyncio
            print("  ✓ nest_asyncio available")
            # Don't actually apply here to avoid conflicts
        except ImportError:
            print("  ⚠️  nest_asyncio not available")
            warnings.append("nest_asyncio not available")
        
    except Exception as e:
        print(f"  ✗ Async compatibility error: {e}")
        issues_found.append(f"Async error: {e}")
    
    # Summary
    print(f"\n" + "=" * 38)
    print("WINDOWS COMPATIBILITY SUMMARY")
    print("=" * 38)
    
    if not issues_found and not warnings:
        print("✅ FULLY COMPATIBLE - No issues found")
        compatibility_status = "FULL"
    elif not issues_found:
        print(f"✅ COMPATIBLE - {len(warnings)} warnings")
        compatibility_status = "COMPATIBLE"
    else:
        print(f"❌ COMPATIBILITY ISSUES - {len(issues_found)} critical")
        compatibility_status = "ISSUES"
    
    if issues_found:
        print(f"\n🚨 CRITICAL ISSUES:")
        for issue in issues_found:
            print(f"   • {issue}")
    
    if warnings:
        print(f"\n⚠️  WARNINGS:")
        for warning in warnings:
            print(f"   • {warning}")
    
    print(f"\nNEXT STEPS:")
    if compatibility_status == "FULL":
        print("• Proceed with TexasSolver integration")
        print("• All core functionality should work on Windows")
    elif compatibility_status == "COMPATIBLE":
        print("• Address warnings before production deployment")
        print("• Core functionality should work with minor limitations")
    else:
        print("• Fix critical issues before proceeding")
        print("• System may not work reliably on Windows")
    
    return compatibility_status, issues_found, warnings

if __name__ == "__main__":
    status, issues, warnings = check_windows_compatibility()
    
    # Return appropriate exit code
    if issues:
        sys.exit(1)
    elif warnings:
        sys.exit(2)  # Warnings but no critical issues
    else:
        sys.exit(0)  # All good