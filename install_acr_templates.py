#!/usr/bin/env python3
"""
Install real ACR card templates and set up advanced training for angled cards.
"""

import os
import shutil
import json
from datetime import datetime
from pathlib import Path
from PIL import Image
import cv2
import numpy as np

def install_acr_templates():
    """Install real ACR templates from attached assets."""
    
    print("Installing Real ACR Card Templates")
    print("=" * 50)
    
    # Find extracted ACR templates
    assets_dir = Path("attached_assets")
    template_dir = Path("training_data/templates")
    backup_dir = Path("training_data/generated_backup")
    
    # Create backup of current templates
    backup_dir.mkdir(parents=True, exist_ok=True)
    current_templates = list(template_dir.glob("*.png"))
    
    if current_templates:
        print(f"Backing up {len(current_templates)} current templates...")
        for template in current_templates:
            backup_path = backup_dir / template.name
            shutil.move(str(template), str(backup_path))
    
    # Look for ACR template files
    acr_files = []
    for file in assets_dir.rglob("*"):
        if file.is_file() and file.suffix.lower() in ['.png', '.jpg', '.jpeg']:
            # Skip calibration files
            if 'calibration' not in file.name.lower() and 'screenshot' not in file.name.lower():
                acr_files.append(file)
    
    print(f"Found {len(acr_files)} potential ACR template files")
    
    # Process ACR template files
    installed_count = 0
    card_mapping = {}
    
    for file_path in acr_files:
        try:
            # Try to extract card name from filename
            filename = file_path.stem
            card_name = extract_card_name_from_filename(filename)
            
            if card_name:
                # Load and process image
                image = Image.open(file_path)
                
                # Convert to RGB if needed
                if image.mode != 'RGB':
                    image = image.convert('RGB')
                
                # Resize to standard template size
                image = image.resize((57, 82), Image.Resampling.LANCZOS)
                
                # Save ACR template
                template_path = template_dir / f"{card_name}.png"
                image.save(template_path)
                
                # Create metadata
                metadata = {
                    "card": card_name,
                    "created": datetime.now().isoformat(),
                    "source": "real_acr_templates",
                    "original_file": str(file_path),
                    "format": "authentic_acr_card"
                }
                
                json_path = template_dir / f"{card_name}.json"
                with open(json_path, 'w') as f:
                    json.dump(metadata, f, indent=2)
                
                installed_count += 1
                card_mapping[filename] = card_name
                print(f"Installed {card_name} from {filename}")
            
        except Exception as e:
            print(f"Could not process {file_path}: {e}")
    
    print(f"\nInstalled {installed_count} real ACR templates")
    
    # If we have fewer than expected, list remaining files for manual mapping
    if installed_count < 52:
        print(f"\nRemaining files that need manual mapping:")
        unmapped_files = [f for f in acr_files if f.stem not in card_mapping.values()]
        for file_path in unmapped_files[:10]:  # Show first 10
            print(f"  - {file_path.name}")
    
    return installed_count

def extract_card_name_from_filename(filename):
    """Extract standard card name from ACR filename."""
    
    filename = filename.upper().replace(' ', '').replace('_', '').replace('-', '')
    
    # Common ACR naming patterns
    patterns = [
        # Standard format: ACE_SPADES, KING_HEARTS, etc.
        ('ACE', 'A'), ('KING', 'K'), ('QUEEN', 'Q'), ('JACK', 'J'), ('TEN', 'T'),
        ('NINE', '9'), ('EIGHT', '8'), ('SEVEN', '7'), ('SIX', '6'), ('FIVE', '5'),
        ('FOUR', '4'), ('THREE', '3'), ('TWO', '2'),
        # Short format: AS, KH, QD, JC, etc.
        ('A', 'A'), ('K', 'K'), ('Q', 'Q'), ('J', 'J'), ('T', 'T'),
        ('9', '9'), ('8', '8'), ('7', '7'), ('6', '6'), ('5', '5'),
        ('4', '4'), ('3', '3'), ('2', '2')
    ]
    
    suit_patterns = [
        ('SPADES', 's'), ('SPADE', 's'), ('S', 's'),
        ('HEARTS', 'h'), ('HEART', 'h'), ('H', 'h'),
        ('DIAMONDS', 'd'), ('DIAMOND', 'd'), ('D', 'd'),
        ('CLUBS', 'c'), ('CLUB', 'c'), ('C', 'c')
    ]
    
    rank = None
    suit = None
    
    # Find rank
    for pattern, standard_rank in patterns:
        if pattern in filename:
            rank = standard_rank
            break
    
    # Find suit
    for pattern, standard_suit in suit_patterns:
        if pattern in filename:
            suit = standard_suit
            break
    
    if rank and suit:
        return rank + suit
    
    return None

def create_advanced_angle_trainer():
    """Create advanced training system for angled cards."""
    
    print("\nCreating Advanced Angle Training System")
    print("=" * 50)
    
    trainer_code = '''
import cv2
import numpy as np
from PIL import Image
import random
import math

class AdvancedAngleTrainer:
    """Advanced training system for angled card recognition like professional poker bots."""
    
    def __init__(self):
        self.angle_range = (-30, 30)  # Degrees of rotation
        self.scale_range = (0.8, 1.2)  # Scale variation
        self.perspective_range = 0.1   # Perspective distortion
        
    def create_angled_variants(self, template_image, num_variants=100):
        """Create training variants with realistic poker table angles."""
        
        variants = []
        
        for i in range(num_variants):
            variant = self.apply_poker_table_transforms(template_image)
            variants.append(variant)
            
        return variants
    
    def apply_poker_table_transforms(self, image):
        """Apply realistic poker table transformations."""
        
        # Convert PIL to OpenCV
        cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        h, w = cv_image.shape[:2]
        
        # 1. Random rotation (cards are often slightly angled)
        angle = random.uniform(*self.angle_range)
        rotation_matrix = cv2.getRotationMatrix2D((w/2, h/2), angle, 1.0)
        rotated = cv2.warpAffine(cv_image, rotation_matrix, (w, h), 
                                borderMode=cv2.BORDER_CONSTANT, 
                                borderValue=(0, 0, 0))
        
        # 2. Perspective distortion (viewing angle)
        perspective_strength = random.uniform(-self.perspective_range, self.perspective_range)
        src_points = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
        dst_points = np.float32([
            [w*perspective_strength, h*perspective_strength],
            [w-w*perspective_strength, h*perspective_strength],
            [w-w*perspective_strength, h-h*perspective_strength],
            [w*perspective_strength, h-h*perspective_strength]
        ])
        
        perspective_matrix = cv2.getPerspectiveTransform(src_points, dst_points)
        perspective_image = cv2.warpPerspective(rotated, perspective_matrix, (w, h))
        
        # 3. Scale variation (distance from camera)
        scale = random.uniform(*self.scale_range)
        scaled_w, scaled_h = int(w * scale), int(h * scale)
        scaled = cv2.resize(perspective_image, (scaled_w, scaled_h))
        
        # Pad or crop to original size
        if scale > 1.0:
            # Crop to original size
            start_x = (scaled_w - w) // 2
            start_y = (scaled_h - h) // 2
            scaled = scaled[start_y:start_y+h, start_x:start_x+w]
        else:
            # Pad to original size
            pad_x = (w - scaled_w) // 2
            pad_y = (h - scaled_h) // 2
            scaled = cv2.copyMakeBorder(scaled, pad_y, h-scaled_h-pad_y, 
                                       pad_x, w-scaled_w-pad_x, 
                                       cv2.BORDER_CONSTANT, value=(0, 0, 0))
        
        # 4. Lighting variations
        brightness = random.uniform(0.7, 1.3)
        contrast = random.uniform(0.8, 1.2)
        scaled = cv2.convertScaleAbs(scaled, alpha=contrast, beta=brightness*30)
        
        # 5. Noise (table texture, lighting)
        noise = np.random.normal(0, 10, scaled.shape).astype(np.uint8)
        noisy = cv2.add(scaled, noise)
        
        # Convert back to PIL
        result = Image.fromarray(cv2.cvtColor(noisy, cv2.COLOR_BGR2RGB))
        
        return result
    
    def generate_poker_training_set(self, templates_dir, output_dir, variants_per_card=200):
        """Generate comprehensive training set for poker table conditions."""
        
        from pathlib import Path
        
        templates_path = Path(templates_dir)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        total_generated = 0
        
        for template_file in templates_path.glob("*.png"):
            card_name = template_file.stem
            template_image = Image.open(template_file)
            
            # Create card-specific output directory
            card_output_dir = output_path / card_name
            card_output_dir.mkdir(exist_ok=True)
            
            # Generate variants
            variants = self.create_angled_variants(template_image, variants_per_card)
            
            # Save variants
            for i, variant in enumerate(variants):
                variant_path = card_output_dir / f"{card_name}_{i:03d}.png"
                variant.save(variant_path)
            
            total_generated += len(variants)
            print(f"Generated {len(variants)} variants for {card_name}")
        
        print(f"\\nGenerated {total_generated} total training images")
        print("Training set ready for angled card recognition!")
        
        return total_generated
'''
    
    # Save the advanced trainer
    trainer_path = Path("app/training/advanced_angle_trainer.py")
    trainer_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(trainer_path, 'w') as f:
        f.write(trainer_code)
    
    print(f"Created advanced angle trainer: {trainer_path}")
    
    return trainer_path

if __name__ == "__main__":
    # Install ACR templates
    installed = install_acr_templates()
    
    # Create advanced training system
    trainer_path = create_advanced_angle_trainer()
    
    print(f"\nACR Template Installation Complete!")
    print(f"- Installed {installed} real ACR templates")
    print(f"- Created advanced angle trainer: {trainer_path}")
    print("\nNext steps:")
    print("1. Visit http://localhost:5000/training-interface")
    print("2. Generate angled training variants")
    print("3. Train neural network on realistic poker conditions")