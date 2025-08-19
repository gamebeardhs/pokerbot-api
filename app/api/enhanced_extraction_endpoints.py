"""
API endpoints for enhanced table state extraction and OCR functionality.
Provides detailed poker table analysis with high-accuracy text recognition.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from typing import Dict, Optional, Any
import asyncio
import time
import logging

from ..scraper.complete_table_state_extractor import CompleteTableStateExtractor
from ..scraper.enhanced_ocr_engine import EnhancedOCREngine, test_enhanced_ocr

logger = logging.getLogger(__name__)

router = APIRouter()

# Global extractor instance
table_extractor: Optional[CompleteTableStateExtractor] = None

@router.post("/initialize-extractor")
async def initialize_table_extractor():
    """Initialize the complete table state extractor."""
    global table_extractor
    
    try:
        table_extractor = CompleteTableStateExtractor()
        
        if not await table_extractor.initialize():
            raise HTTPException(status_code=500, detail="Failed to initialize table extractor")
        
        performance = table_extractor.get_extraction_performance()
        
        return {
            "status": "initialized",
            "message": "Table state extractor initialized successfully",
            "regions_configured": performance['regions_configured'],
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Failed to initialize table extractor: {e}")
        raise HTTPException(status_code=500, detail=f"Initialization failed: {str(e)}")

@router.get("/extract-complete-state")
async def extract_complete_table_state():
    """Extract complete poker table state with OCR and card recognition."""
    global table_extractor
    
    try:
        if not table_extractor:
            raise HTTPException(status_code=400, detail="Table extractor not initialized")
        
        # Perform complete extraction
        extracted_state = await table_extractor.extract_complete_table_state()
        
        if not extracted_state:
            raise HTTPException(status_code=500, detail="Failed to extract table state")
        
        return {
            "status": "success",
            "extracted_state": {
                "timestamp": extracted_state.timestamp,
                "pot_size": extracted_state.pot_size,
                "hero_stack": extracted_state.hero_stack,
                "hero_cards": extracted_state.hero_cards,
                "board_cards": extracted_state.board_cards,
                "current_street": extracted_state.current_street,
                "active_players": extracted_state.active_players,
                "button_position": extracted_state.button_position,
                "blinds": extracted_state.blinds,
                "is_hero_turn": extracted_state.is_hero_turn,
                "action_buttons": [
                    {
                        "button_type": btn.button_type.value,
                        "confidence": btn.confidence,
                        "is_active": btn.is_active,
                        "position": btn.position
                    } for btn in extracted_state.action_buttons
                ],
                "extraction_confidence": extracted_state.extraction_confidence,
                "errors": extracted_state.errors
            },
            "performance": table_extractor.get_extraction_performance(),
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Table state extraction failed: {e}")
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")

@router.get("/extraction-performance")
async def get_extraction_performance():
    """Get performance metrics for the extraction system."""
    global table_extractor
    
    try:
        if not table_extractor:
            raise HTTPException(status_code=400, detail="Table extractor not initialized")
        
        performance = table_extractor.get_extraction_performance()
        
        return {
            "status": "success",
            "performance": performance,
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Failed to get performance metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Performance query failed: {str(e)}")

@router.post("/save-extraction-debug")
async def save_extraction_debug():
    """Save debug information for the last extraction."""
    global table_extractor
    
    try:
        if not table_extractor:
            raise HTTPException(status_code=400, detail="Table extractor not initialized")
        
        # Get latest extraction
        extracted_state = await table_extractor.extract_complete_table_state()
        
        if not extracted_state:
            raise HTTPException(status_code=500, detail="No extraction data available")
        
        # Save debug information
        debug_filename = table_extractor.save_debug_extraction(extracted_state)
        
        return {
            "status": "success",
            "message": debug_filename,
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Failed to save extraction debug: {e}")
        raise HTTPException(status_code=500, detail=f"Debug save failed: {str(e)}")

@router.get("/test-ocr-engine")
async def test_ocr_engine():
    """Test the enhanced OCR engine with EasyOCR and multi-engine capabilities."""
    try:
        # Run comprehensive OCR tests
        from ..scraper.enhanced_ocr_engine import test_enhanced_ocr, test_multi_engine_performance
        
        # Run synchronous test
        test_enhanced_ocr()
        
        # Run async performance test
        await test_multi_engine_performance()
        
        return {
            "status": "success",
            "message": "Enhanced OCR engine test completed with EasyOCR integration - check server logs for detailed results",
            "features_tested": [
                "EasyOCR initialization",
                "Multi-engine consensus",
                "Performance comparison",
                "Accuracy validation"
            ],
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"OCR engine test failed: {e}")
        raise HTTPException(status_code=500, detail=f"OCR test failed: {str(e)}")

@router.get("/ocr-engine-info")
async def get_ocr_engine_info():
    """Get information about the OCR engine capabilities including EasyOCR status."""
    try:
        # Test both single and multi-engine modes
        ocr_engine = EnhancedOCREngine(use_easyocr=True, use_multi_engine=True)
        engine_info = ocr_engine.get_engine_info()
        
        return {
            "status": "success",
            "ocr_info": {
                "confidence_threshold": ocr_engine.confidence_threshold,
                "engines": engine_info,
                "available_configs": list(ocr_engine.configs.keys()),
                "preprocessing_methods": [
                    "scaled_gray",
                    "adaptive_thresh", 
                    "otsu_thresh",
                    "morphological",
                    "contrast_enhanced",
                    "gaussian_blur"
                ],
                "supported_text_types": [
                    "money", "cards", "names", "general", "single_word", "single_char"
                ],
                "features": {
                    "multi_engine_consensus": engine_info['multi_engine_enabled'],
                    "easyocr_integration": engine_info['easyocr_available'],
                    "parallel_processing": True,
                    "confidence_based_selection": True
                }
            },
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Failed to get OCR info: {e}")
        raise HTTPException(status_code=500, detail=f"OCR info failed: {str(e)}")

@router.post("/continuous-extraction")
async def start_continuous_extraction(duration_seconds: int = 30):
    """Start continuous table state extraction for monitoring."""
    global table_extractor
    
    try:
        if not table_extractor:
            raise HTTPException(status_code=400, detail="Table extractor not initialized")
        
        results = []
        start_time = time.time()
        
        while time.time() - start_time < duration_seconds:
            extracted_state = await table_extractor.extract_complete_table_state()
            
            if extracted_state:
                results.append({
                    "timestamp": extracted_state.timestamp,
                    "confidence": extracted_state.extraction_confidence,
                    "pot_size": extracted_state.pot_size,
                    "hero_cards": len(extracted_state.hero_cards),
                    "board_cards": len(extracted_state.board_cards),
                    "is_hero_turn": extracted_state.is_hero_turn,
                    "errors": len(extracted_state.errors)
                })
            
            # Wait before next extraction
            await asyncio.sleep(1.0)
        
        # Calculate summary statistics
        if results:
            avg_confidence = sum(r['confidence'] for r in results) / len(results)
            success_rate = len([r for r in results if r['confidence'] > 0.6]) / len(results)
        else:
            avg_confidence = 0.0
            success_rate = 0.0
        
        return {
            "status": "completed",
            "duration": duration_seconds,
            "extractions": len(results),
            "average_confidence": avg_confidence,
            "success_rate": success_rate,
            "results": results,
            "performance": table_extractor.get_extraction_performance(),
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Continuous extraction failed: {e}")
        raise HTTPException(status_code=500, detail=f"Continuous extraction failed: {str(e)}")

# Health check for extraction system
@router.get("/extraction-health")
async def extraction_system_health():
    """Health check for the complete extraction system."""
    try:
        health_status = {
            "extractor_initialized": table_extractor is not None,
            "components": {}
        }
        
        # Test core components
        try:
            ocr_engine = EnhancedOCREngine()
            health_status["components"]["ocr_engine"] = "available"
        except Exception as e:
            health_status["components"]["ocr_engine"] = f"error: {e}"
        
        if table_extractor:
            performance = table_extractor.get_extraction_performance()
            health_status["components"]["table_extractor"] = "initialized"
            health_status["extraction_performance"] = performance
        else:
            health_status["components"]["table_extractor"] = "not_initialized"
        
        # Overall health status
        health_status["status"] = "healthy" if all(
            "error" not in str(status) for status in health_status["components"].values()
        ) else "degraded"
        
        health_status["timestamp"] = time.time()
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.time()
        }