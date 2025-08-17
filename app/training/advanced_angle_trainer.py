
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
        
        print(f"\nGenerated {total_generated} total training images")
        print("Training set ready for angled card recognition!")
        
        return total_generated
