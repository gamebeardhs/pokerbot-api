"""
Neural network training system inspired by DeeperMind poker bot.
Combines template-based bootstrapping with augmented data generation.
"""

import os
import json
import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
from typing import List, Dict, Optional, Tuple, Any
import logging
from dataclasses import dataclass
from datetime import datetime
import random

logger = logging.getLogger(__name__)

@dataclass
class CardTemplate:
    """A template for a specific card."""
    card: str  # e.g., "As", "Kh"
    image: Image.Image
    confidence_threshold: float = 0.8
    created_at: str = ""

class ColorNormalizer:
    """Normalizes card colors similar to DeeperMind approach."""
    
    @staticmethod
    def adjust_colors(image: np.ndarray, tolerance: int = 120) -> np.ndarray:
        """
        Adjust colors to standard poker card colors.
        Makes red cards more red, black cards more black, etc.
        """
        # Handle different image formats
        if len(image.shape) == 4:
            # RGBA format - convert to RGB
            if image.shape[3] == 4:
                image = image[:, :, :, :3]  # Drop alpha channel
        
        # Ensure RGB format (H, W, 3)
        if len(image.shape) != 3 or image.shape[2] != 3:
            raise ValueError(f"Expected RGB image with shape (H, W, 3), got {image.shape}")
        
        # Define standard poker colors (red, black, white, background)
        colors = np.array([
            [255, 0, 0],    # Red (hearts/diamonds)
            [0, 0, 0],      # Black (spades/clubs)
            [255, 255, 255], # White (card background)
            [0, 128, 0]     # Green (table background)
        ])
        
        # Find closest color for each pixel
        # Reshape for broadcasting: image (H,W,3) vs colors (4,1,1,3)
        image_expanded = image[None, :, :, :]  # (1, H, W, 3)
        colors_expanded = colors[:, None, None, :]  # (4, 1, 1, 3)
        
        # Calculate distance and find closest color
        distances = np.abs(image_expanded - colors_expanded).sum(axis=-1)  # (4, H, W)
        closest_color_idx = np.argmin(distances, axis=0)  # (H, W)
        
        # Only apply normalization where colors are close enough
        min_distances = np.min(distances, axis=0)  # (H, W)
        close_enough = min_distances < tolerance
        
        # Initialize with original image
        normalized = image.copy()
        
        # Apply color normalization where appropriate
        for i, color in enumerate(colors):
            mask = (closest_color_idx == i) & close_enough
            normalized[mask] = color
        
        # Convert green to darker green (table color)
        green_mask = np.all(normalized == colors[3], axis=-1)
        normalized[green_mask] = [0, 100, 0]
        
        return normalized.astype(np.uint8)
    
    @staticmethod
    def normalize_card_region(image: Image.Image) -> Image.Image:
        """Normalize a card region for better recognition."""
        # Convert to RGB if needed (handles RGBA, L, P modes)
        if image.mode != 'RGB':
            # For RGBA images, composite over white background
            if image.mode == 'RGBA':
                background = Image.new('RGB', image.size, (255, 255, 255))
                image = Image.alpha_composite(background.convert('RGBA'), image).convert('RGB')
            else:
                image = image.convert('RGB')
        
        # Convert to numpy
        img_array = np.array(image)
        
        try:
            # Apply color normalization
            normalized = ColorNormalizer.adjust_colors(img_array)
            
            # Enhance contrast
            img = Image.fromarray(normalized)
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.5)
            
            # Slight sharpening
            img = img.filter(ImageFilter.UnsharpMask(radius=1, percent=120, threshold=3))
            
            return img
        except Exception as e:
            logger.warning(f"Color normalization failed: {e}, using original image")
            return image

class DataAugmentor:
    """Generate augmented training data from base templates."""
    
    def __init__(self):
        self.transformations = [
            self._rotate,
            self._shift,
            self._scale,
            self._brightness,
            self._contrast,
            self._noise,
            self._blur,
            self._perspective
        ]
    
    def generate_variants(self, image: Image.Image, count: int = 50) -> List[Image.Image]:
        """Generate multiple variants of a card image."""
        variants = []
        base_image = image.copy()
        
        for i in range(count):
            # Start with original
            variant = base_image.copy()
            
            # Apply 1-3 random transformations
            num_transforms = random.randint(1, 3)
            transforms = random.sample(self.transformations, num_transforms)
            
            for transform in transforms:
                try:
                    variant = transform(variant)
                except Exception as e:
                    logger.debug(f"Transform failed: {e}")
                    continue
            
            variants.append(variant)
        
        return variants
    
    def _rotate(self, image: Image.Image) -> Image.Image:
        """Slight rotation."""
        angle = random.uniform(-5, 5)
        return image.rotate(angle, fillcolor='white')
    
    def _shift(self, image: Image.Image) -> Image.Image:
        """Small position shift."""
        dx = random.randint(-2, 2)
        dy = random.randint(-2, 2)
        return image.transform(image.size, Image.Transform.AFFINE, (1, 0, dx, 0, 1, dy))
    
    def _scale(self, image: Image.Image) -> Image.Image:
        """Slight scaling."""
        factor = random.uniform(0.95, 1.05)
        new_size = (int(image.width * factor), int(image.height * factor))
        scaled = image.resize(new_size, Image.Resampling.LANCZOS)
        
        # Crop or pad back to original size
        if factor > 1:
            # Crop
            left = (scaled.width - image.width) // 2
            top = (scaled.height - image.height) // 2
            return scaled.crop((left, top, left + image.width, top + image.height))
        else:
            # Pad
            padded = Image.new('RGB', image.size, 'white')
            offset = ((image.width - scaled.width) // 2, (image.height - scaled.height) // 2)
            padded.paste(scaled, offset)
            return padded
    
    def _brightness(self, image: Image.Image) -> Image.Image:
        """Adjust brightness."""
        factor = random.uniform(0.8, 1.2)
        enhancer = ImageEnhance.Brightness(image)
        return enhancer.enhance(factor)
    
    def _contrast(self, image: Image.Image) -> Image.Image:
        """Adjust contrast."""
        factor = random.uniform(0.8, 1.3)
        enhancer = ImageEnhance.Contrast(image)
        return enhancer.enhance(factor)
    
    def _noise(self, image: Image.Image) -> Image.Image:
        """Add slight noise."""
        img_array = np.array(image)
        noise = np.random.normal(0, 5, img_array.shape).astype(np.uint8)
        noisy = np.clip(img_array.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        return Image.fromarray(noisy)
    
    def _blur(self, image: Image.Image) -> Image.Image:
        """Slight blur."""
        radius = random.uniform(0.2, 0.8)
        return image.filter(ImageFilter.GaussianBlur(radius))
    
    def _perspective(self, image: Image.Image) -> Image.Image:
        """Slight perspective distortion."""
        # Small perspective changes
        w, h = image.size
        delta = random.randint(-2, 2)
        
        # Define perspective transform
        src_points = np.array([[0, 0], [w, 0], [w, h], [0, h]], dtype=np.float32)
        dst_points = np.array([
            [delta, delta], 
            [w - delta, delta], 
            [w + delta, h - delta], 
            [-delta, h - delta]
        ], dtype=np.float32)
        
        # Apply transform
        img_array = np.array(image)
        matrix = cv2.getPerspectiveTransform(src_points, dst_points)
        warped = cv2.warpPerspective(img_array, matrix, (w, h), borderValue=(255, 255, 255))
        
        return Image.fromarray(warped)

class TemplateManager:
    """Manages card templates similar to DeeperMind's approach."""
    
    def __init__(self, templates_dir: str = "training_data/templates"):
        self.templates_dir = templates_dir
        self.templates: Dict[str, CardTemplate] = {}
        os.makedirs(templates_dir, exist_ok=True)
        self.load_templates()
    
    def add_template(self, card: str, image: Image.Image, confidence: float = 0.8) -> bool:
        """Add a new card template."""
        try:
            # Normalize the image
            normalized = ColorNormalizer.normalize_card_region(image)
            
            # Create template
            template = CardTemplate(
                card=card,
                image=normalized,
                confidence_threshold=confidence,
                created_at=datetime.now().isoformat()
            )
            
            # Save to disk
            template_path = os.path.join(self.templates_dir, f"{card}.png")
            normalized.save(template_path)
            
            # Save metadata
            metadata_path = os.path.join(self.templates_dir, f"{card}.json")
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'card': card,
                    'confidence_threshold': confidence,
                    'created_at': template.created_at
                }, f)
            
            self.templates[card] = template
            logger.info(f"Added template for {card}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add template for {card}: {e}")
            return False
    
    def load_templates(self):
        """Load existing templates from disk."""
        try:
            for file in os.listdir(self.templates_dir):
                if file.endswith('.png'):
                    card = file[:-4]  # Remove .png
                    
                    # Load image
                    image_path = os.path.join(self.templates_dir, file)
                    image = Image.open(image_path)
                    
                    # Load metadata if exists
                    metadata_path = os.path.join(self.templates_dir, f"{card}.json")
                    confidence = 0.8
                    created_at = ""
                    
                    if os.path.exists(metadata_path):
                        with open(metadata_path, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                            confidence = metadata.get('confidence_threshold', 0.8)
                            created_at = metadata.get('created_at', '')
                    
                    # Create template
                    template = CardTemplate(
                        card=card,
                        image=image,
                        confidence_threshold=confidence,
                        created_at=created_at
                    )
                    
                    self.templates[card] = template
            
            logger.info(f"Loaded {len(self.templates)} templates")
            
        except Exception as e:
            logger.error(f"Failed to load templates: {e}")
    
    def get_template(self, card: str) -> Optional[CardTemplate]:
        """Get template for a specific card."""
        return self.templates.get(card)
    
    def get_all_templates(self) -> Dict[str, CardTemplate]:
        """Get all templates."""
        return self.templates.copy()
    
    def match_template(self, image: Image.Image, card: str) -> float:
        """Match an image against a template, return confidence score."""
        template = self.get_template(card)
        if not template:
            return 0.0
        
        try:
            # Normalize input image
            normalized_input = ColorNormalizer.normalize_card_region(image)
            
            # Resize to same size
            if normalized_input.size != template.image.size:
                normalized_input = normalized_input.resize(template.image.size, Image.Resampling.LANCZOS)
            
            # Convert to numpy arrays
            img1 = np.array(normalized_input)
            img2 = np.array(template.image)
            
            # Calculate similarity using normalized cross-correlation
            correlation = cv2.matchTemplate(img1, img2, cv2.TM_CCOEFF_NORMED)
            max_val = correlation.max()
            
            return float(max_val)
            
        except Exception as e:
            logger.debug(f"Template matching failed for {card}: {e}")
            return 0.0

class NeuralCardTrainer:
    """Enhanced neural network trainer inspired by DeeperMind."""
    
    def __init__(self, training_data_dir: str = "training_data"):
        self.training_data_dir = training_data_dir
        self.augmentor = DataAugmentor()
        self.template_manager = TemplateManager(os.path.join(training_data_dir, "templates"))
        
        # Standard deck
        self.ranks = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
        self.suits = ['s', 'h', 'd', 'c']
        self.all_cards = [rank + suit for rank in self.ranks for suit in self.suits]
        
        os.makedirs(training_data_dir, exist_ok=True)
    
    def add_card_template(self, card: str, image: Image.Image) -> bool:
        """Add a new card template for generating training data."""
        if card not in self.all_cards:
            logger.error(f"Invalid card: {card}")
            return False
        
        return self.template_manager.add_template(card, image)
    
    def generate_training_dataset(self, variants_per_card: int = 100) -> Dict[str, Any]:
        """Generate augmented training dataset from templates."""
        dataset = {
            'images': [],
            'labels': [],
            'card_names': []
        }
        
        templates = self.template_manager.get_all_templates()
        if not templates:
            logger.error("No templates available for training data generation")
            return dataset
        
        logger.info(f"Generating training data from {len(templates)} templates")
        
        for card, template in templates.items():
            logger.info(f"Generating {variants_per_card} variants for {card}")
            
            # Generate augmented versions
            variants = self.augmentor.generate_variants(template.image, variants_per_card)
            
            for variant in variants:
                # Convert to numpy array and normalize
                img_array = np.array(variant)
                normalized = ColorNormalizer.adjust_colors(img_array)
                
                dataset['images'].append(normalized)
                dataset['labels'].append(self.all_cards.index(card))
                dataset['card_names'].append(card)
        
        logger.info(f"Generated {len(dataset['images'])} training examples")
        return dataset
    
    def save_training_dataset(self, dataset: Dict[str, Any], output_dir: str):
        """Save training dataset to disk."""
        os.makedirs(output_dir, exist_ok=True)
        
        # Save images and metadata
        for i, (image, label, card_name) in enumerate(zip(
            dataset['images'], dataset['labels'], dataset['card_names']
        )):
            # Create directory for this card
            card_dir = os.path.join(output_dir, card_name)
            os.makedirs(card_dir, exist_ok=True)
            
            # Save image
            img = Image.fromarray(image)
            img.save(os.path.join(card_dir, f"{card_name}_{i:04d}.png"))
        
        # Save metadata
        metadata = {
            'total_images': len(dataset['images']),
            'cards': list(set(dataset['card_names'])),
            'class_mapping': {card: idx for idx, card in enumerate(self.all_cards)},
            'generated_at': datetime.now().isoformat()
        }
        
        with open(os.path.join(output_dir, 'metadata.json'), 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Saved training dataset to {output_dir}")
    
    def get_training_stats(self) -> Dict[str, Any]:
        """Get statistics about available training resources."""
        templates = self.template_manager.get_all_templates()
        
        stats = {
            'total_templates': len(templates),
            'cards_with_templates': list(templates.keys()),
            'missing_cards': [card for card in self.all_cards if card not in templates],
            'coverage_percentage': (len(templates) / len(self.all_cards)) * 100,
            'template_stats': {}
        }
        
        for card, template in templates.items():
            stats['template_stats'][card] = {
                'created_at': template.created_at,
                'confidence_threshold': template.confidence_threshold,
                'image_size': template.image.size
            }
        
        return stats