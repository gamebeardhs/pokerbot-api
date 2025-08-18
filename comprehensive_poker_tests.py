#!/usr/bin/env python3
"""
Comprehensive Poker Pipeline Tests: End-to-end validation
Tests the complete flow from ACR screenshot to TexasSolver scenario display
"""

import time
import json
import logging
import requests
from typing import Dict, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PipelineValidator:
    """Validates the complete poker advisory pipeline."""
    
    def __init__(self):
        self.base_url = "http://localhost:5000"
        self.auth_header = {"Authorization": "Bearer test-token-123"}
        
    def test_database_query_pipeline(self) -> bool:
        """Test database query and response formatting."""
        
        print("🔍 TESTING DATABASE QUERY PIPELINE")
        print("=" * 35)
        
        try:
            # Test instant GTO endpoint
            test_data = {
                "hole_cards": ["As", "Ks"],
                "board_cards": [],
                "pot_size": 3.0,
                "bet_to_call": 2.0,
                "stack_size": 100.0,
                "position": "BTN",
                "num_players": 6,
                "betting_round": "preflop"
            }
            
            print("Testing instant GTO query...")
            response = requests.post(
                f"{self.base_url}/database/instant-gto",
                json=test_data,
                headers={"Content-Type": "application/json", **self.auth_header},
                timeout=10
            )
            
            print(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Database query successful")
                print(f"Response structure: {list(result.keys())}")
                
                # Check for proper TexasSolver scenario format
                if 'recommendation' in result:
                    rec = result['recommendation']
                    print(f"Decision: {rec.get('decision', 'N/A')}")
                    print(f"Equity: {rec.get('equity', 0):.3f}")
                    print(f"Reasoning: {rec.get('reasoning', 'N/A')[:80]}...")
                    return True
                else:
                    print("⚠️ Missing recommendation field")
                    return False
            else:
                error_data = response.json() if response.content else {}
                print(f"❌ Query failed: {error_data.get('message', 'Unknown error')}")
                return False
                
        except Exception as e:
            print(f"❌ Database query test failed: {e}")
            return False
    
    def test_scenario_interpretation(self) -> bool:
        """Test TexasSolver scenario interpretation and formatting."""
        
        print("\n🎯 TESTING SCENARIO INTERPRETATION")
        print("=" * 33)
        
        try:
            # Test manual solve endpoint for detailed analysis
            test_situation = {
                "hole_cards": ["Qh", "Qd"],
                "board_cards": ["As", "Kh", "Qc"],
                "pot_size": 15.0,
                "bet_to_call": 10.0,
                "stack_size": 85.0,
                "position": "CO",
                "num_players": 4,
                "betting_round": "flop"
            }
            
            print("Testing scenario interpretation...")
            response = requests.post(
                f"{self.base_url}/manual/solve",
                json=test_situation,
                headers={"Content-Type": "application/json", **self.auth_header},
                timeout=15
            )
            
            print(f"Interpretation status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Scenario interpretation successful")
                
                # Check analysis structure
                if 'analysis' in result:
                    analysis = result['analysis']
                    print(f"Mathematical reasoning: {analysis.get('mathematical_reasoning', 'N/A')[:60]}...")
                    print(f"Strategic context: {analysis.get('strategic_context', 'N/A')[:60]}...")
                    
                    # Check recommendation format
                    if 'recommendation' in result:
                        rec = result['recommendation']
                        print(f"Final decision: {rec.get('decision', 'N/A')}")
                        print(f"Bet size: ${rec.get('bet_size', 0)}")
                        print(f"Confidence: {rec.get('confidence', 0):.3f}")
                        return True
                    else:
                        print("⚠️ Missing recommendation in interpretation")
                        return False
                else:
                    print("⚠️ Missing analysis in interpretation")
                    return False
            else:
                print(f"❌ Interpretation failed: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Scenario interpretation test failed: {e}")
            return False
    
    def test_gui_display_pipeline(self) -> bool:
        """Test GUI display and formatting pipeline."""
        
        print("\n🖥️ TESTING GUI DISPLAY PIPELINE")
        print("=" * 30)
        
        try:
            # Test unified interface endpoint
            print("Testing unified interface...")
            response = requests.get(
                f"{self.base_url}/unified",
                headers=self.auth_header,
                timeout=10
            )
            
            print(f"GUI status: {response.status_code}")
            
            if response.status_code == 200:
                html_content = response.text
                print("✅ GUI endpoint accessible")
                
                # Check for key interface elements
                key_elements = [
                    "GTO Recommendation",
                    "Manual Analysis",
                    "equity",
                    "confidence",
                    "decision"
                ]
                
                missing_elements = []
                for element in key_elements:
                    if element.lower() not in html_content.lower():
                        missing_elements.append(element)
                
                if not missing_elements:
                    print("✅ All key GUI elements present")
                    return True
                else:
                    print(f"⚠️ Missing GUI elements: {missing_elements}")
                    return False
            else:
                print(f"❌ GUI not accessible: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ GUI display test failed: {e}")
            return False
    
    def test_screenshot_processing_compatibility(self) -> bool:
        """Test screenshot processing and ACR table data compatibility."""
        
        print("\n📸 TESTING SCREENSHOT PROCESSING COMPATIBILITY")
        print("=" * 45)
        
        try:
            # Test auto-advisory endpoint for screenshot compatibility
            print("Testing screenshot processing...")
            response = requests.get(
                f"{self.base_url}/auto-advisory/status",
                headers=self.auth_header,
                timeout=10
            )
            
            print(f"Screenshot processor status: {response.status_code}")
            
            if response.status_code == 200:
                status = response.json()
                print("✅ Screenshot processor accessible")
                print(f"Scraper status: {status.get('scraper_active', 'Unknown')}")
                print(f"Calibration: {status.get('calibrated', 'Unknown')}")
                
                # Test table data format compatibility
                test_table_data = {
                    "seats": [
                        {
                            "position": 0,
                            "name": "TestPlayer",
                            "stack": 100.0,
                            "cards": ["As", "Ks"],
                            "active": True
                        }
                    ],
                    "pot": 3.0,
                    "board": [],
                    "betting_round": "preflop",
                    "button_position": 0
                }
                
                print("Testing table data format...")
                process_response = requests.post(
                    f"{self.base_url}/auto-advisory/process-table",
                    json=test_table_data,
                    headers={"Content-Type": "application/json", **self.auth_header},
                    timeout=15
                )
                
                if process_response.status_code == 200:
                    result = process_response.json()
                    print("✅ Table data processing successful")
                    
                    if 'recommendation' in result:
                        print(f"Generated recommendation: {result['recommendation'].get('decision', 'N/A')}")
                        return True
                    else:
                        print("⚠️ No recommendation generated from table data")
                        return False
                else:
                    print(f"⚠️ Table processing issue: {process_response.status_code}")
                    return False
            else:
                print(f"❌ Screenshot processor not accessible: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Screenshot processing test failed: {e}")
            return False
    
    def test_error_handling_pipeline(self) -> bool:
        """Test error handling throughout the pipeline."""
        
        print("\n⚠️ TESTING ERROR HANDLING PIPELINE")
        print("=" * 33)
        
        try:
            # Test malformed request handling
            print("Testing malformed request handling...")
            bad_data = {"invalid": "data"}
            
            response = requests.post(
                f"{self.base_url}/database/instant-gto",
                json=bad_data,
                headers={"Content-Type": "application/json", **self.auth_header},
                timeout=10
            )
            
            if response.status_code in [400, 422]:  # Expected error codes
                print("✅ Proper error handling for malformed requests")
                
                # Test database fallback behavior
                print("Testing database fallback...")
                impossible_data = {
                    "hole_cards": ["Zz", "Yy"],  # Invalid cards
                    "board_cards": [],
                    "pot_size": -1.0,  # Invalid pot
                    "bet_to_call": 2.0,
                    "stack_size": 100.0,
                    "position": "INVALID",
                    "num_players": 6,
                    "betting_round": "preflop"
                }
                
                fallback_response = requests.post(
                    f"{self.base_url}/database/instant-gto",
                    json=impossible_data,
                    headers={"Content-Type": "application/json", **self.auth_header},
                    timeout=10
                )
                
                if fallback_response.status_code in [400, 422]:
                    print("✅ Proper validation and error responses")
                    return True
                else:
                    print("⚠️ Unexpected response to invalid data")
                    return False
            else:
                print(f"⚠️ Unexpected error handling: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error handling test failed: {e}")
            return False
    
    def run_comprehensive_tests(self) -> Dict[str, bool]:
        """Run all pipeline tests and return results."""
        
        print("🧪 COMPREHENSIVE PIPELINE VALIDATION")
        print("=" * 36)
        print("Testing complete flow: Screenshot → Processing → Database → GUI")
        
        results = {
            "database_query": self.test_database_query_pipeline(),
            "scenario_interpretation": self.test_scenario_interpretation(),
            "gui_display": self.test_gui_display_pipeline(),
            "screenshot_processing": self.test_screenshot_processing_compatibility(),
            "error_handling": self.test_error_handling_pipeline()
        }
        
        # Summary
        print(f"\n📊 PIPELINE TEST RESULTS")
        print("=" * 25)
        
        passed = sum(results.values())
        total = len(results)
        
        for test_name, passed_test in results.items():
            status = "✅ PASS" if passed_test else "❌ FAIL"
            print(f"{test_name.replace('_', ' ').title()}: {status}")
        
        print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        if passed == total:
            print("🎉 ALL PIPELINE TESTS PASSED")
            print("System ready for full TexasSolver scenario processing")
        elif passed >= total * 0.8:
            print("✅ PIPELINE MOSTLY FUNCTIONAL")
            print("Minor issues detected but core functionality working")
        else:
            print("⚠️ SIGNIFICANT PIPELINE ISSUES")
            print("Multiple components need attention")
        
        return results

def main():
    """Execute comprehensive pipeline validation."""
    validator = PipelineValidator()
    results = validator.run_comprehensive_tests()
    
    # Additional detailed analysis
    if not all(results.values()):
        print("\n🔧 RECOMMENDED FIXES:")
        print("-" * 18)
        
        if not results["database_query"]:
            print("• Fix database query response formatting")
        if not results["scenario_interpretation"]:
            print("• Improve TexasSolver scenario interpretation")
        if not results["gui_display"]:
            print("• Update GUI display components")
        if not results["screenshot_processing"]:
            print("• Verify screenshot processing compatibility")
        if not results["error_handling"]:
            print("• Enhance error handling and validation")
    
    return all(results.values())

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)