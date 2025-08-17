"""
API endpoints for card recognition training system.
"""

import io
import base64
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from PIL import Image
import logging

from app.training.card_trainer import CardTrainer, InteractiveTrainer, ManualLabeler

logger = logging.getLogger(__name__)

# Initialize training components
card_trainer = CardTrainer()
interactive_trainer = InteractiveTrainer(card_trainer)
manual_labeler = ManualLabeler(card_trainer)

router = APIRouter(prefix="/training", tags=["training"])

# Pydantic models for requests/responses
class TrainingSessionRequest(BaseModel):
    image_base64: str
    regions: Dict[str, List[int]]  # region_name -> [x1, y1, x2, y2]

class CorrectionRequest(BaseModel):
    image_base64: str
    region_name: str
    correct_cards: List[str]

class ManualLabelRequest(BaseModel):
    image_base64: str
    cards: List[str]

class TrainingStatsResponse(BaseModel):
    total_examples: int
    corrections: int
    manual_labels: int
    region_distribution: Dict[str, int]
    card_distribution: Dict[str, int]

def base64_to_image(base64_str: str) -> Image.Image:
    """Convert base64 string to PIL Image."""
    try:
        # Remove data URL prefix if present
        if base64_str.startswith('data:image'):
            base64_str = base64_str.split(',')[1]
        
        image_data = base64.b64decode(base64_str)
        return Image.open(io.BytesIO(image_data))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image data: {e}")

@router.post("/start-session")
async def start_training_session(request: TrainingSessionRequest) -> Dict[str, Any]:
    """Start an interactive training session with a screenshot."""
    try:
        # Convert base64 to image
        image = base64_to_image(request.image_base64)
        
        # Convert regions format
        regions = {}
        for region_name, coords in request.regions.items():
            if len(coords) != 4:
                raise HTTPException(status_code=400, detail=f"Region {region_name} must have 4 coordinates")
            regions[region_name] = tuple(coords)
        
        # Start training session
        session_data = interactive_trainer.start_training_session(image, regions)
        
        return {
            "success": True,
            "session_data": session_data
        }
        
    except Exception as e:
        logger.error(f"Failed to start training session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/submit-correction")
async def submit_correction(request: CorrectionRequest) -> Dict[str, Any]:
    """Submit a correction for a specific region during training."""
    try:
        # Convert base64 to image
        image = base64_to_image(request.image_base64)
        
        # Submit correction
        success = interactive_trainer.submit_correction(
            image=image,
            region_name=request.region_name,
            correct_cards=request.correct_cards
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to submit correction")
        
        return {
            "success": True,
            "message": f"Correction submitted for {request.region_name}"
        }
        
    except Exception as e:
        logger.error(f"Failed to submit correction: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/finish-session")
async def finish_training_session() -> Dict[str, Any]:
    """Finish the current training session."""
    try:
        result = interactive_trainer.finish_session()
        return {
            "success": True,
            "session_summary": result
        }
        
    except Exception as e:
        logger.error(f"Failed to finish training session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/add-manual-label")
async def add_manual_label(request: ManualLabelRequest) -> Dict[str, Any]:
    """Add a manually labeled card for training."""
    try:
        # Convert base64 to image
        image = base64_to_image(request.image_base64)
        
        # Add manual label
        result = manual_labeler.add_labeled_card(image, request.cards)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to add manual label: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload-card-image")
async def upload_card_image(
    file: UploadFile = File(...),
    cards: str = Form(...)
) -> Dict[str, Any]:
    """Upload a card image file with labels."""
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read and convert to PIL Image
        image_data = await file.read()
        image = Image.open(io.BytesIO(image_data))
        
        # Parse cards (comma-separated)
        card_list = [card.strip() for card in cards.split(',') if card.strip()]
        
        # Add manual label
        result = manual_labeler.add_labeled_card(image, card_list)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to upload card image: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_training_stats() -> TrainingStatsResponse:
    """Get training data statistics."""
    try:
        stats = card_trainer.get_training_stats()
        return TrainingStatsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Failed to get training stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/export")
async def export_training_data(format: str = "json") -> Dict[str, Any]:
    """Export training data."""
    try:
        export_file = card_trainer.export_training_data(format)
        return {
            "success": True,
            "export_file": export_file,
            "message": f"Training data exported to {export_file}"
        }
        
    except Exception as e:
        logger.error(f"Failed to export training data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/clear")
async def clear_training_data() -> Dict[str, Any]:
    """Clear all training data (use with caution)."""
    try:
        card_trainer.clear_training_data()
        return {
            "success": True,
            "message": "All training data cleared"
        }
        
    except Exception as e:
        logger.error(f"Failed to clear training data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def training_health_check() -> Dict[str, Any]:
    """Health check for training system."""
    return {
        "status": "healthy",
        "trainer_ready": True,
        "interactive_trainer_ready": True,
        "manual_labeler_ready": True
    }