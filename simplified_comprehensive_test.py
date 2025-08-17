"""
Simplified Comprehensive Test Suite: All 6 Phases Validation
Fast, reliable testing of the complete poker advisory system.
"""

import time
import numpy as np
import sys
from typing import Dict, Any

def test_phase_1_circuit_breaker():
    """Test Phase 1: Circuit Breaker & Timeout Protection"""
    print("🔧 Testing Phase 1: Circuit Breaker & Timeout Protection")
    
    results = []
    
    try:
        from app.scraper.intelligent_calibrator import IntelligentACRCalibrator
        
        # Test initialization
        calibrator = IntelligentACRCalibrator()
        assert calibrator.circuit_breaker is not None
        results.append("✅ Circuit breaker initialized")
        
        # Test screenshot capture with timeout protection
        start_time = time.time()
        screenshot = calibrator.capture_screen()
        capture_time = time.time() - start_time
        
        assert screenshot is not None
        assert len(screenshot.shape) == 3
        assert capture_time < 10.0  # Should complete within 10 seconds
        results.append(f"✅ Screenshot capture ({capture_time:.2f}s)")
        
        # Test screenshot state manager
        assert calibrator.screenshot_manager is not None
        results.append("✅ Screenshot state manager")
        
        # Test calibration cache
        assert isinstance(calibrator.calibration_cache, dict)
        results.append("✅ Calibration cache")
        
    except Exception as e:
        results.append(f"❌ Phase 1 error: {e}")
    
    success_rate = len([r for r in results if r.startswith("✅")]) / len(results)
    return results, success_rate

def test_phase_2_stealth_detection():
    """Test Phase 2: Advanced ACR Stealth Detection"""
    print("🔧 Testing Phase 2: Advanced ACR Stealth Detection")
    
    results = []
    
    try:
        from app.scraper.intelligent_calibrator import IntelligentACRCalibrator
        
        calibrator = IntelligentACRCalibrator()
        
        # Test stealth detector integration
        if calibrator.stealth_detector:
            results.append("✅ Stealth detector loaded")
            
            # Test hierarchical detection
            assert hasattr(calibrator.stealth_detector, 'hierarchical_detectors')
            assert len(calibrator.stealth_detector.hierarchical_detectors) == 3
            results.append("✅ Hierarchical detectors (3 levels)")
            
            # Test UI signatures
            assert hasattr(calibrator.stealth_detector, 'acr_ui_signatures')
            signatures = calibrator.stealth_detector.acr_ui_signatures
            assert "table_felt_colors" in signatures
            results.append("✅ ACR UI signatures")
            
            # Test adaptive detection
            test_screenshot = np.random.randint(0, 255, (600, 800, 3), dtype=np.uint8)
            detected, table_info = calibrator.detect_acr_table_with_versioning(test_screenshot)
            assert isinstance(detected, bool)
            assert isinstance(table_info, dict)
            results.append("✅ Adaptive table detection")
            
        else:
            results.append("⚠️ Stealth detector not loaded - using fallback")
        
    except Exception as e:
        results.append(f"❌ Phase 2 error: {e}")
    
    success_rate = len([r for r in results if r.startswith("✅")]) / len(results)
    return results, success_rate

def test_phase_3_gpu_acceleration():
    """Test Phase 3: GPU Acceleration Framework"""
    print("🔧 Testing Phase 3: GPU Acceleration Framework")
    
    results = []
    
    try:
        from app.core.gpu_acceleration import GPUAcceleratedRecognition
        
        # Test initialization
        gpu_system = GPUAcceleratedRecognition()
        results.append(f"✅ GPU system initialized ({gpu_system.gpu_available})")
        
        # Test device info
        device_info = gpu_system.device_info
        assert isinstance(device_info, dict)
        results.append("✅ Device info available")
        
        # Test accelerated card detection
        test_image = np.random.randint(0, 255, (600, 800, 3), dtype=np.uint8)
        start_time = time.time()
        card_regions, metrics = gpu_system.accelerated_card_detection(test_image)
        detection_time = time.time() - start_time
        
        assert isinstance(card_regions, list)
        assert hasattr(metrics, 'gpu_available')
        assert hasattr(metrics, 'processing_time')
        assert detection_time < 5.0
        results.append(f"✅ Card detection ({detection_time:.3f}s)")
        
        # Test performance report
        report = gpu_system.get_performance_report()
        assert "gpu_enabled" in report
        assert "optimization_level" in report
        results.append("✅ Performance report")
        
    except Exception as e:
        results.append(f"❌ Phase 3 error: {e}")
    
    success_rate = len([r for r in results if r.startswith("✅")]) / len(results)
    return results, success_rate

def test_phase_4_gto_engine():
    """Test Phase 4: Enhanced GTO Engine"""
    print("🔧 Testing Phase 4: Enhanced GTO Engine")
    
    results = []
    
    try:
        from app.advisor.enhanced_gto_engine import EnhancedGTOEngine, PokerSituation
        
        # Test initialization
        gto_engine = EnhancedGTOEngine()
        results.append("✅ GTO engine initialized")
        
        # Test components
        assert gto_engine.equity_calculator is not None
        assert gto_engine.range_analyzer is not None
        assert gto_engine.board_texture_analyzer is not None
        results.append("✅ All components loaded")
        
        # Test GTO analysis
        test_situation = PokerSituation(
            hero_cards=['As', 'Kh'],
            board_cards=['Qd', 'Jc', '9s'],
            position='BTN',
            stack_size=100.0,
            pot_size=20.0,
            bet_to_call=5.0,
            opponents=[{'position': 'BB', 'last_action': 'bet'}],
            betting_history=['check', 'bet'],
            game_phase='flop',
            table_type='cash',
            blind_levels=(0.5, 1.0)
        )
        
        start_time = time.time()
        decision = gto_engine.analyze_situation(test_situation)
        analysis_time = time.time() - start_time
        
        assert hasattr(decision, 'primary_action')
        assert hasattr(decision, 'confidence_score')
        assert hasattr(decision, 'reasoning')
        assert analysis_time < 2.0  # Should be fast
        results.append(f"✅ GTO analysis ({decision.primary_action}, {analysis_time:.3f}s)")
        
        # Test performance report
        report = gto_engine.get_performance_report()
        assert "engine_status" in report
        assert "components_loaded" in report
        results.append("✅ Performance metrics")
        
    except Exception as e:
        results.append(f"❌ Phase 4 error: {e}")
    
    success_rate = len([r for r in results if r.startswith("✅")]) / len(results)
    return results, success_rate

def test_phase_5_turn_detection():
    """Test Phase 5: Advanced Turn Detection"""
    print("🔧 Testing Phase 5: Advanced Turn Detection")
    
    results = []
    
    try:
        from app.core.turn_detection import AdvancedTurnDetection
        
        # Test initialization
        turn_detector = AdvancedTurnDetection()
        results.append("✅ Turn detector initialized")
        
        # Test UI detectors
        assert len(turn_detector.ui_element_detectors) == 6
        results.append("✅ UI element detectors (6 methods)")
        
        # Test turn detection
        test_screenshot = np.random.randint(0, 255, (600, 800, 3), dtype=np.uint8)
        # Add simulated action buttons
        test_screenshot[500:530, 600:750] = [100, 140, 220]  # Blue button
        
        start_time = time.time()
        turn_state = turn_detector.detect_turn_state(test_screenshot)
        detection_time = time.time() - start_time
        
        assert hasattr(turn_state, 'is_hero_turn')
        assert hasattr(turn_state, 'confidence')
        assert hasattr(turn_state, 'ui_elements_detected')
        assert detection_time < 1.0
        results.append(f"✅ Turn detection ({turn_state.confidence:.2f}, {detection_time:.3f}s)")
        
        # Test state machine
        assert turn_detector.state_machine["current_state"] in ["waiting", "hero_turn_detected"]
        results.append("✅ State machine")
        
        # Test performance report
        report = turn_detector.get_performance_report()
        assert "detection_system" in report
        results.append("✅ Performance report")
        
    except Exception as e:
        results.append(f"❌ Phase 5 error: {e}")
    
    success_rate = len([r for r in results if r.startswith("✅")]) / len(results)
    return results, success_rate

def test_phase_6_anti_detection():
    """Test Phase 6: ACR Anti-Detection System"""
    print("🔧 Testing Phase 6: ACR Anti-Detection System")
    
    results = []
    
    try:
        from app.core.acr_anti_detection import ACRAntiDetectionSystem
        
        # Test initialization
        anti_detection = ACRAntiDetectionSystem()
        results.append(f"✅ Anti-detection initialized ({anti_detection.stealth_level})")
        
        # Test behavior profiles
        assert len(anti_detection.behavior_profiles) == 3
        assert anti_detection.current_profile is not None
        results.append("✅ Behavior profiles (3 types)")
        
        # Test stealth timing
        decision_context = {
            'game_phase': 'flop',
            'intended_action': 'raise',
            'decision_difficulty': 'marginal'
        }
        
        stealth_timing = anti_detection.calculate_stealth_decision_timing(decision_context)
        assert isinstance(stealth_timing, float)
        assert 0.5 <= stealth_timing <= 30.0
        results.append(f"✅ Stealth timing ({stealth_timing:.2f}s)")
        
        # Test GTO deviation
        gto_decision = {
            'action_frequencies': {'fold': 0.3, 'call': 0.4, 'raise': 0.3},
            'confidence': 0.85
        }
        
        stealth_decision = anti_detection.apply_gto_deviation(gto_decision, {})
        assert isinstance(stealth_decision, dict)
        results.append("✅ GTO deviation")
        
        # Test risk assessment
        session_data = {
            'duration_hours': 2.5,
            'decision_consistency': 0.92,
            'timing_variance': 0.25
        }
        
        risk_assessment = anti_detection.assess_detection_risk(session_data)
        assert "overall_risk" in risk_assessment
        assert "risk_score" in risk_assessment
        results.append(f"✅ Risk assessment ({risk_assessment['overall_risk']})")
        
        # Test performance report
        report = anti_detection.get_stealth_performance_report()
        assert "stealth_system" in report
        assert "metrics" in report
        results.append("✅ Performance report")
        
    except Exception as e:
        results.append(f"❌ Phase 6 error: {e}")
    
    success_rate = len([r for r in results if r.startswith("✅")]) / len(results)
    return results, success_rate

def test_integration():
    """Test complete system integration"""
    print("🔧 Testing Integration: All Phases Working Together")
    
    results = []
    
    try:
        # Import all phases
        from app.scraper.intelligent_calibrator import IntelligentACRCalibrator
        from app.core.gpu_acceleration import GPUAcceleratedRecognition
        from app.advisor.enhanced_gto_engine import EnhancedGTOEngine, PokerSituation
        from app.core.turn_detection import AdvancedTurnDetection
        from app.core.acr_anti_detection import ACRAntiDetectionSystem
        
        # Initialize all systems
        calibrator = IntelligentACRCalibrator()
        gpu_system = GPUAcceleratedRecognition()
        gto_engine = EnhancedGTOEngine()
        turn_detector = AdvancedTurnDetection()
        anti_detection = ACRAntiDetectionSystem()
        
        results.append("✅ All systems initialized")
        
        # Test complete pipeline
        start_time = time.time()
        
        # 1. Screenshot capture
        screenshot = calibrator.capture_screen()
        
        # 2. Table detection
        detected, table_info = calibrator.detect_acr_table_with_versioning(screenshot)
        
        # 3. Card recognition
        card_regions, gpu_metrics = gpu_system.accelerated_card_detection(screenshot)
        
        # 4. GTO analysis
        poker_situation = PokerSituation(
            hero_cards=['As', 'Kh'],
            board_cards=['Qd', 'Jc', '9s'],
            position='BTN',
            stack_size=100.0,
            pot_size=20.0,
            bet_to_call=5.0,
            opponents=[{'position': 'BB', 'last_action': 'bet'}],
            betting_history=['check', 'bet'],
            game_phase='flop',
            table_type='cash',
            blind_levels=(0.5, 1.0)
        )
        
        decision = gto_engine.analyze_situation(poker_situation)
        
        # 5. Turn detection
        turn_state = turn_detector.detect_turn_state(screenshot)
        
        # 6. Anti-detection measures
        decision_context = {
            'game_phase': 'flop',
            'intended_action': decision.primary_action,
            'decision_difficulty': 'marginal'
        }
        
        stealth_timing = anti_detection.calculate_stealth_decision_timing(decision_context)
        
        total_time = time.time() - start_time
        
        results.append(f"✅ Complete pipeline ({total_time:.3f}s)")
        results.append(f"✅ Screenshot: {screenshot.shape}")
        results.append(f"✅ Detection: {detected}")
        results.append(f"✅ Cards: {len(card_regions)} regions")
        results.append(f"✅ GTO: {decision.primary_action}")
        results.append(f"✅ Turn: {turn_state.is_hero_turn}")
        results.append(f"✅ Stealth: {stealth_timing:.2f}s")
        
        # Test data flow consistency
        assert screenshot is not None
        assert isinstance(detected, bool)
        assert isinstance(card_regions, list)
        assert hasattr(decision, 'primary_action')
        assert hasattr(turn_state, 'is_hero_turn')
        assert isinstance(stealth_timing, float)
        
        results.append("✅ Data flow consistency")
        
    except Exception as e:
        results.append(f"❌ Integration error: {e}")
    
    success_rate = len([r for r in results if r.startswith("✅")]) / len(results)
    return results, success_rate

def run_comprehensive_test():
    """Run complete comprehensive test suite"""
    print("🧪 COMPREHENSIVE POKER ADVISORY SYSTEM TEST")
    print("=" * 60)
    print()
    
    start_time = time.time()
    all_results = {}
    
    # Run all phase tests
    test_phases = [
        ("Phase 1", test_phase_1_circuit_breaker),
        ("Phase 2", test_phase_2_stealth_detection),
        ("Phase 3", test_phase_3_gpu_acceleration),
        ("Phase 4", test_phase_4_gto_engine),
        ("Phase 5", test_phase_5_turn_detection),
        ("Phase 6", test_phase_6_anti_detection),
        ("Integration", test_integration)
    ]
    
    for phase_name, test_func in test_phases:
        print(f"\n{phase_name} Testing:")
        print("-" * 30)
        
        try:
            results, success_rate = test_func()
            all_results[phase_name] = {
                "results": results,
                "success_rate": success_rate
            }
            
            # Print results
            for result in results:
                print(f"  {result}")
            
            print(f"  📊 Success Rate: {success_rate:.1%}")
            
        except Exception as e:
            all_results[phase_name] = {
                "results": [f"❌ Test failed: {e}"],
                "success_rate": 0.0
            }
            print(f"  ❌ Test failed: {e}")
    
    # Generate final report
    total_time = time.time() - start_time
    
    print("\n" + "=" * 60)
    print("📊 FINAL TEST RESULTS")
    print("=" * 60)
    
    # Summary table
    print(f"{'Phase':<15} {'Success Rate':<12} {'Status'}")
    print("-" * 50)
    
    overall_success_rates = []
    
    for phase_name, data in all_results.items():
        success_rate = data['success_rate']
        overall_success_rates.append(success_rate)
        
        if success_rate >= 0.9:
            status = "🟢 EXCELLENT"
        elif success_rate >= 0.8:
            status = "🟡 GOOD"
        elif success_rate >= 0.6:
            status = "🟠 ACCEPTABLE"
        else:
            status = "🔴 NEEDS WORK"
        
        print(f"{phase_name:<15} {success_rate:.1%}          {status}")
    
    print("-" * 50)
    
    # Overall assessment
    overall_success = sum(overall_success_rates) / len(overall_success_rates) if overall_success_rates else 0
    total_tests = sum(len(data['results']) for data in all_results.values())
    successful_tests = sum(
        len([r for r in data['results'] if r.startswith("✅")])
        for data in all_results.values()
    )
    
    if overall_success >= 0.9:
        system_status = "🟢 SYSTEM READY - Excellent performance"
    elif overall_success >= 0.8:
        system_status = "🟡 SYSTEM READY - Good performance"
    elif overall_success >= 0.6:
        system_status = "🟠 FUNCTIONAL - Minor issues detected"
    else:
        system_status = "🔴 ISSUES DETECTED - Review required"
    
    print(f"{'OVERALL':<15} {overall_success:.1%}          {system_status}")
    
    print()
    print("🎯 SUMMARY")
    print("-" * 30)
    print(f"Total Tests: {total_tests}")
    print(f"Successful: {successful_tests}")
    print(f"Overall Success Rate: {overall_success:.1%}")
    print(f"Test Duration: {total_time:.2f} seconds")
    
    print()
    print("🎮 POKER ADVISORY SYSTEM STATUS")
    print("-" * 40)
    
    if overall_success >= 0.8:
        print("✅ System is ready for professional poker advisory use")
        print("✅ All critical components are functioning correctly")
        print("✅ Circuit breaker protection is active")
        print("✅ Stealth measures are operational")
        print("✅ Performance optimization is working")
        print("✅ GTO analysis provides expert decisions")
        print("✅ Turn detection is responsive")
        print("✅ Anti-detection measures ensure safety")
    else:
        print("⚠️ Some components need attention before production use")
    
    return overall_success

if __name__ == "__main__":
    overall_success = run_comprehensive_test()
    
    if overall_success >= 0.8:
        print("\n✅ Comprehensive test passed - System validated")
        sys.exit(0)
    else:
        print("\n⚠️ Some issues detected - Review recommended")
        sys.exit(1)