"""
Interactive card recognition trainer for improving accuracy through user corrections.
"""

import os
import json
import uuid
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from PIL import Image
import numpy as np
import cv2
import logging

logger = logging.getLogger(__name__)

@dataclass
class TrainingExample:
    """A single training example with image data and correct labels."""
    id: str
    image_path: str
    region_name: str  # e.g., "hero_cards", "board_cards"
    bbox: Tuple[int, int, int, int]  # x1, y1, x2, y2
    correct_cards: List[str]  # e.g., ["As", "Kh"]
    predicted_cards: List[str]  # What the system predicted
    confidence_scores: List[float]
    timestamp: str
    source: str  # "interactive_correction" or "manual_labeling"
    
    def to_dict(self):
        return asdict(self)

class CardTrainer:
    """Manages training data collection and model improvement."""
    
    def __init__(self, training_data_dir: str = "training_data"):
        self.training_data_dir = training_data_dir
        self.examples_file = os.path.join(training_data_dir, "training_examples.json")
        self.images_dir = os.path.join(training_data_dir, "images")
        
        # Create directories if they don't exist
        os.makedirs(self.training_data_dir, exist_ok=True)
        os.makedirs(self.images_dir, exist_ok=True)
        
        # Load existing training data
        self.training_examples = self._load_training_examples()
        
    def _load_training_examples(self) -> List[TrainingExample]:
        """Load existing training examples from file."""
        if not os.path.exists(self.examples_file):
            return []
            
        try:
            with open(self.examples_file, 'r') as f:
                data = json.load(f)
                return [TrainingExample(**example) for example in data]
        except Exception as e:
            logger.error(f"Failed to load training examples: {e}")
            return []
    
    def _save_training_examples(self):
        """Save training examples to file."""
        try:
            with open(self.examples_file, 'w') as f:
                json.dump([example.to_dict() for example in self.training_examples], f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save training examples: {e}")
    
    def add_correction_example(self, 
                             image: Image.Image,
                             region_name: str,
                             bbox: Tuple[int, int, int, int],
                             predicted_cards: List[str],
                             correct_cards: List[str],
                             confidence_scores: List[float]) -> str:
        """Add a training example from user correction."""
        
        # Generate unique ID and save image
        example_id = str(uuid.uuid4())
        image_filename = f"correction_{example_id}.png"
        image_path = os.path.join(self.images_dir, image_filename)
        
        # Save the image region
        image.save(image_path)
        
        # Create training example
        example = TrainingExample(
            id=example_id,
            image_path=image_path,
            region_name=region_name,
            bbox=bbox,
            correct_cards=correct_cards,
            predicted_cards=predicted_cards,
            confidence_scores=confidence_scores,
            timestamp=datetime.now().isoformat(),
            source="interactive_correction"
        )
        
        self.training_examples.append(example)
        self._save_training_examples()
        
        logger.info(f"Added correction example: {predicted_cards} -> {correct_cards}")
        return example_id
    
    def add_manual_label(self,
                        image: Image.Image,
                        cards: List[str],
                        region_name: str = "manual_card") -> str:
        """Add a manually labeled card for training."""
        
        # Generate unique ID and save image
        example_id = str(uuid.uuid4())
        image_filename = f"manual_{example_id}.png"
        image_path = os.path.join(self.images_dir, image_filename)
        
        # Save the image
        image.save(image_path)
        
        # Create training example
        example = TrainingExample(
            id=example_id,
            image_path=image_path,
            region_name=region_name,
            bbox=(0, 0, image.width, image.height),
            correct_cards=cards,
            predicted_cards=[],  # No prediction for manual labels
            confidence_scores=[],
            timestamp=datetime.now().isoformat(),
            source="manual_labeling"
        )
        
        self.training_examples.append(example)
        self._save_training_examples()
        
        logger.info(f"Added manual label: {cards}")
        return example_id
    
    def get_training_stats(self) -> Dict[str, Any]:
        """Get statistics about the training data."""
        total_examples = len(self.training_examples)
        corrections = len([e for e in self.training_examples if e.source == "interactive_correction"])
        manual_labels = len([e for e in self.training_examples if e.source == "manual_labeling"])
        
        # Count by region
        region_counts = {}
        for example in self.training_examples:
            region_counts[example.region_name] = region_counts.get(example.region_name, 0) + 1
        
        # Count card frequencies
        card_counts = {}
        for example in self.training_examples:
            for card in example.correct_cards:
                card_counts[card] = card_counts.get(card, 0) + 1
        
        return {
            "total_examples": total_examples,
            "corrections": corrections,
            "manual_labels": manual_labels,
            "region_distribution": region_counts,
            "card_distribution": card_counts,
            "latest_examples": [e.to_dict() for e in self.training_examples[-5:]]
        }
    
    def export_training_data(self, format: str = "json") -> str:
        """Export training data in specified format."""
        if format == "json":
            export_file = os.path.join(self.training_data_dir, f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            with open(export_file, 'w') as f:
                json.dump([example.to_dict() for example in self.training_examples], f, indent=2)
            return export_file
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def clear_training_data(self):
        """Clear all training data (use with caution)."""
        self.training_examples = []
        self._save_training_examples()
        logger.warning("All training data cleared")

class InteractiveTrainer:
    """Handles interactive training sessions where user corrects predictions."""
    
    def __init__(self, card_trainer: CardTrainer):
        self.trainer = card_trainer
        self.current_session: Optional[Dict[str, Any]] = None
    
    def start_training_session(self, image: Image.Image, regions: Dict[str, Tuple[int, int, int, int]]) -> Dict[str, Any]:
        """Start an interactive training session with a screenshot."""
        from app.scraper.card_recognition import CardRecognition
        
        card_recognizer = CardRecognition()
        session_data: Dict[str, Any] = {
            "session_id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "regions": {}
        }
        
        # Process each region
        for region_name, bbox in regions.items():
            x1, y1, x2, y2 = bbox
            region_image = image.crop((x1, y1, x2, y2))
            
            # Get current predictions
            detected_cards = card_recognizer.detect_cards_in_region(region_image)
            predicted_cards = [str(card) for card in detected_cards]
            confidence_scores = [card.confidence for card in detected_cards]
            
            session_data["regions"][region_name] = {
                "bbox": bbox,
                "predicted_cards": predicted_cards,
                "confidence_scores": confidence_scores,
                "needs_correction": True  # User will review each region
            }
        
        self.current_session = session_data
        return session_data
    
    def submit_correction(self, 
                         image: Image.Image,
                         region_name: str, 
                         correct_cards: List[str]) -> bool:
        """Submit a correction for a specific region."""
        if not self.current_session or region_name not in self.current_session["regions"]:
            return False
        
        region_data = self.current_session["regions"][region_name]
        bbox = region_data["bbox"]
        predicted_cards = region_data["predicted_cards"]
        confidence_scores = region_data["confidence_scores"]
        
        # Extract the region image
        x1, y1, x2, y2 = bbox
        region_image = image.crop((x1, y1, x2, y2))
        
        # Add to training data
        self.trainer.add_correction_example(
            image=region_image,
            region_name=region_name,
            bbox=bbox,
            predicted_cards=predicted_cards,
            correct_cards=correct_cards,
            confidence_scores=confidence_scores
        )
        
        # Mark as corrected
        region_data["correct_cards"] = correct_cards
        region_data["needs_correction"] = False
        
        return True
    
    def finish_session(self) -> Dict[str, Any]:
        """Finish the current training session."""
        if not self.current_session:
            return {"error": "No active session"}
        
        session_summary = {
            "session_id": self.current_session["session_id"],
            "corrections_made": len([r for r in self.current_session["regions"].values() 
                                   if not r["needs_correction"]]),
            "total_regions": len(self.current_session["regions"])
        }
        
        self.current_session = None
        return session_summary

class ManualLabeler:
    """Handles manual card labeling for creating training datasets."""
    
    def __init__(self, card_trainer: CardTrainer):
        self.trainer = card_trainer
        self.valid_ranks = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
        self.valid_suits = ['s', 'h', 'd', 'c']
    
    def validate_card(self, card_str: str) -> bool:
        """Validate card string format (e.g., 'As', 'Kh')."""
        if len(card_str) != 2:
            return False
        rank, suit = card_str[0], card_str[1]
        return rank in self.valid_ranks and suit in self.valid_suits
    
    def add_labeled_card(self, image: Image.Image, cards: List[str]) -> Dict[str, Any]:
        """Add a manually labeled card image."""
        # Validate all cards
        invalid_cards = [card for card in cards if not self.validate_card(card)]
        if invalid_cards:
            return {"error": f"Invalid card format: {invalid_cards}"}
        
        # Add to training data
        example_id = self.trainer.add_manual_label(image, cards)
        
        return {
            "success": True,
            "example_id": example_id,
            "cards": cards,
            "message": f"Added {len(cards)} card(s) to training data"
        }
    
    def bulk_upload_cards(self, card_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Upload multiple card images with labels."""
        results = []
        errors = []
        
        for item in card_data:
            try:
                image = item["image"]  # PIL Image object
                cards = item["cards"]  # List of card strings
                
                result = self.add_labeled_card(image, cards)
                if "error" in result:
                    errors.append(result["error"])
                else:
                    results.append(result)
            except Exception as e:
                errors.append(f"Failed to process item: {e}")
        
        return {
            "successful_uploads": len(results),
            "errors": errors,
            "total_processed": len(card_data)
        }