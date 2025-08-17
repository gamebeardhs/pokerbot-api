#!/usr/bin/env python3
"""
Test the advanced angle training system with real ACR templates.
"""

from app.training.advanced_angle_trainer import AdvancedAngleTrainer
from pathlib import Path

def test_advanced_training():
    """Test advanced training with real ACR templates."""
    
    print("Testing Advanced Angle Training with Real ACR Templates")
    print("=" * 60)
    
    # Initialize advanced trainer
    trainer = AdvancedAngleTrainer()
    
    # Count ACR templates
    templates_dir = Path("training_data/templates")
    templates = list(templates_dir.glob("*.png"))
    print(f"Found {len(templates)} ACR templates")
    
    # Show a few template names
    for template in templates[:5]:
        print(f"  - {template.stem}")
    
    if len(templates) >= 52:
        print(f"\n✅ Complete ACR template set available!")
        
        # Test generating a small batch
        print("\nGenerating test batch with advanced transformations...")
        
        total_generated = trainer.generate_poker_training_set(
            templates_dir="training_data/templates",
            output_dir="training_data/test_advanced",
            variants_per_card=10  # Small test batch
        )
        
        print(f"\n🎉 Successfully generated {total_generated} advanced training examples!")
        print("\nFeatures included:")
        print("- ✅ Card rotation (-30° to +30°)")
        print("- ✅ Perspective distortion (viewing angles)")
        print("- ✅ Scale variation (distance effects)")
        print("- ✅ Lighting changes")
        print("- ✅ Realistic noise")
        
        # Check output
        output_dir = Path("training_data/test_advanced")
        if output_dir.exists():
            card_dirs = list(output_dir.glob("*"))
            print(f"\nGenerated training data for {len(card_dirs)} cards")
            
            # Show sample
            if card_dirs:
                sample_card = card_dirs[0]
                variants = list(sample_card.glob("*.png"))
                print(f"Example: {sample_card.name} has {len(variants)} variants")
        
    else:
        print(f"❌ Only found {len(templates)} templates, need 52")
        print("Run install_acr_templates.py first")

if __name__ == "__main__":
    test_advanced_training()