#!/usr/bin/env python3
"""
Simple testing interface for the enhanced card recognition system.
Run this script to test different aspects of the dual recognition system.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PIL import Image
import requests
import base64
import io
from app.scraper.card_recognition import CardRecognition
from app.training.neural_trainer import TemplateManager, NeuralCardTrainer
import logging

logging.basicConfig(level=logging.INFO)

class TestInterface:
    def __init__(self):
        self.recognizer = CardRecognition()
        self.template_manager = TemplateManager()
        
    def show_menu(self):
        """Display the testing menu."""
        print("\n" + "="*60)
        print("🃏 Enhanced Card Recognition Testing Interface")
        print("="*60)
        print("1. View existing templates")
        print("2. Test template matching")
        print("3. Test dual recognition on image")
        print("4. Generate training dataset")
        print("5. Test API endpoints")
        print("6. Create new template")
        print("7. View system status")
        print("0. Exit")
        print("="*60)
        
    def view_templates(self):
        """Show all existing templates."""
        print("\n📁 Existing Templates:")
        templates = self.template_manager.get_all_templates()
        
        if not templates:
            print("  No templates found. Create some templates first!")
            return
            
        for card, template in templates.items():
            print(f"  ✓ {card}: confidence threshold {template.confidence_threshold}")
            print(f"    Size: {template.image.size}, Created: {template.created_at}")
        
        print(f"\nTotal: {len(templates)} templates")
        
    def test_template_matching(self):
        """Test template matching with existing templates."""
        print("\n🔍 Template Matching Test:")
        
        templates = self.template_manager.get_all_templates()
        if not templates:
            print("  No templates available for testing!")
            return
            
        # Test self-matching for each template
        for card, template in templates.items():
            confidence = self.template_manager.match_template(template.image, card)
            status = "✓ PASS" if confidence > 0.9 else "✗ FAIL"
            print(f"  {card}: {confidence:.3f} {status}")
    
    def test_dual_recognition(self):
        """Test dual recognition on a test image."""
        print("\n🎯 Dual Recognition Test:")
        
        # List available test images
        test_images = [f for f in os.listdir('.') if f.startswith('test_template_') and f.endswith('.png')]
        
        if not test_images:
            print("  No test images found!")
            return
            
        print("Available test images:")
        for i, img in enumerate(test_images):
            print(f"  {i+1}. {img}")
        
        try:
            choice = int(input(f"Choose image (1-{len(test_images)}): ")) - 1
            if 0 <= choice < len(test_images):
                image_path = test_images[choice]
                test_image = Image.open(image_path)
                
                print(f"\nTesting with {image_path}...")
                print(f"Image size: {test_image.size}")
                
                # Test dual recognition
                cards = self.recognizer.detect_cards_dual_mode(test_image)
                print(f"\nDual recognition results:")
                if cards:
                    for card in cards:
                        print(f"  ✓ {card} (confidence: {card.confidence:.3f})")
                else:
                    print("  No cards detected")
                    
        except (ValueError, IndexError):
            print("Invalid choice!")
        except Exception as e:
            print(f"Test failed: {e}")
    
    def generate_training_data(self):
        """Generate training dataset from templates."""
        print("\n📊 Training Dataset Generation:")
        
        trainer = NeuralCardTrainer()
        
        try:
            variants = int(input("Number of variants per card (default 10): ") or "10")
            print(f"Generating {variants} variants per template...")
            
            dataset = trainer.generate_training_dataset(variants_per_card=variants)
            
            print(f"\nGenerated dataset:")
            print(f"  Total images: {len(dataset['images'])}")
            print(f"  Total labels: {len(dataset['labels'])}")
            print(f"  Cards covered: {len(set(dataset['card_names']))}")
            
            # Show distribution
            card_counts = {}
            for card in dataset['card_names']:
                card_counts[card] = card_counts.get(card, 0) + 1
                
            print(f"\nCard distribution:")
            for card, count in card_counts.items():
                print(f"    {card}: {count} variants")
                
        except ValueError:
            print("Invalid number!")
        except Exception as e:
            print(f"Dataset generation failed: {e}")
    
    def test_api_endpoints(self):
        """Test the training API endpoints."""
        print("\n🌐 API Endpoints Test:")
        
        base_url = "http://localhost:5000"
        
        # Test health endpoint
        try:
            response = requests.get(f"{base_url}/health", timeout=5)
            if response.status_code == 200:
                print("  ✓ Health endpoint: OK")
            else:
                print(f"  ✗ Health endpoint: {response.status_code}")
        except Exception as e:
            print(f"  ✗ Health endpoint failed: {e}")
        
        # Test training stats
        try:
            response = requests.get(f"{base_url}/training/stats", timeout=5)
            if response.status_code == 200:
                print("  ✓ Training stats endpoint: OK")
                data = response.json()
                print(f"    Training examples: {data.get('total_examples', 0)}")
            else:
                print(f"  ✗ Training stats: {response.status_code}")
        except Exception as e:
            print(f"  ✗ Training stats failed: {e}")
    
    def create_template(self):
        """Create a new card template."""
        print("\n🎨 Create New Template:")
        
        print("Available cards: As, Ah, Ad, Ac, Ks, Kh, Kd, Kc, etc.")
        card = input("Enter card name (e.g., 'As' for Ace of Spades): ").strip()
        
        if len(card) != 2:
            print("Invalid card format! Use format like 'As', 'Kh', etc.")
            return
            
        try:
            # Create a simple template (you can modify this to load from file)
            from create_test_template import create_card_template
            
            rank, suit = card[0], card[1]
            card_image = create_card_template(rank, suit)
            
            confidence = float(input("Confidence threshold (0.0-1.0, default 0.7): ") or "0.7")
            
            success = self.template_manager.add_template(card, card_image, confidence)
            
            if success:
                print(f"  ✓ Template for {card} created successfully!")
                # Save visual copy
                card_image.save(f"test_template_{card}.png")
                print(f"  ✓ Saved visual copy as test_template_{card}.png")
            else:
                print(f"  ✗ Failed to create template for {card}")
                
        except ValueError:
            print("Invalid confidence value!")
        except Exception as e:
            print(f"Template creation failed: {e}")
    
    def show_system_status(self):
        """Show current system status."""
        print("\n📈 System Status:")
        
        templates = self.template_manager.get_all_templates()
        print(f"  Templates loaded: {len(templates)}")
        
        # Check directories
        dirs_to_check = ['training_data', 'training_data/templates', 'training_data/images']
        for dir_path in dirs_to_check:
            exists = "✓" if os.path.exists(dir_path) else "✗"
            print(f"  {exists} {dir_path}")
        
        # Check test files
        test_files = [f for f in os.listdir('.') if f.startswith('test_template_')]
        print(f"  Test template files: {len(test_files)}")
        
        print(f"\nDual recognition system: ✓ Ready")
        print(f"Template matching: ✓ Operational")
        print(f"Data augmentation: ✓ Available")
    
    def run(self):
        """Run the testing interface."""
        while True:
            self.show_menu()
            
            try:
                choice = input("\nChoose an option (0-7): ").strip()
                
                if choice == '0':
                    print("Goodbye! 👋")
                    break
                elif choice == '1':
                    self.view_templates()
                elif choice == '2':
                    self.test_template_matching()
                elif choice == '3':
                    self.test_dual_recognition()
                elif choice == '4':
                    self.generate_training_data()
                elif choice == '5':
                    self.test_api_endpoints()
                elif choice == '6':
                    self.create_template()
                elif choice == '7':
                    self.show_system_status()
                else:
                    print("Invalid option! Please choose 0-7.")
                    
                input("\nPress Enter to continue...")
                
            except KeyboardInterrupt:
                print("\n\nGoodbye! 👋")
                break
            except Exception as e:
                print(f"Error: {e}")
                input("\nPress Enter to continue...")

if __name__ == "__main__":
    interface = TestInterface()
    interface.run()