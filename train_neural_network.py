#!/usr/bin/env python3
"""
Train neural network on ACR card templates with advanced angle training data.
"""

import os
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
import cv2
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import json

class ACRCardNetworkTrainer:
    def __init__(self):
        self.img_height = 82
        self.img_width = 57
        self.num_classes = 52
        self.model = None
        self.label_encoder = LabelEncoder()
        
    def load_training_data(self, dataset_dir):
        """Load training data from advanced dataset."""
        print(f"Loading training data from {dataset_dir}")
        
        dataset_path = Path(dataset_dir)
        if not dataset_path.exists():
            raise ValueError(f"Dataset directory not found: {dataset_dir}")
        
        images = []
        labels = []
        
        # Get all card directories
        card_dirs = [d for d in dataset_path.iterdir() if d.is_dir()]
        print(f"Found {len(card_dirs)} card types")
        
        for card_dir in card_dirs:
            card_name = card_dir.name
            card_images = list(card_dir.glob("*.png"))
            
            print(f"Loading {len(card_images)} images for {card_name}")
            
            for img_path in card_images:
                try:
                    # Load and preprocess image
                    img = cv2.imread(str(img_path))
                    if img is None:
                        continue
                        
                    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                    img = cv2.resize(img, (self.img_width, self.img_height))
                    img = img.astype(np.float32) / 255.0
                    
                    images.append(img)
                    labels.append(card_name)
                    
                except Exception as e:
                    print(f"Error loading {img_path}: {e}")
                    continue
        
        print(f"Loaded {len(images)} total training images")
        
        # Convert to numpy arrays
        X = np.array(images)
        y = np.array(labels)
        
        # Encode labels
        y_encoded = self.label_encoder.fit_transform(y)
        y_categorical = keras.utils.to_categorical(y_encoded, num_classes=self.num_classes)
        
        return X, y_categorical
    
    def create_model(self):
        """Create CNN model for card recognition."""
        model = keras.Sequential([
            # Input layer
            keras.Input(shape=(self.img_height, self.img_width, 3)),
            
            # First convolutional block
            layers.Conv2D(32, (3, 3), activation='relu'),
            layers.MaxPooling2D((2, 2)),
            layers.BatchNormalization(),
            
            # Second convolutional block
            layers.Conv2D(64, (3, 3), activation='relu'),
            layers.MaxPooling2D((2, 2)),
            layers.BatchNormalization(),
            
            # Third convolutional block
            layers.Conv2D(128, (3, 3), activation='relu'),
            layers.MaxPooling2D((2, 2)),
            layers.BatchNormalization(),
            
            # Fourth convolutional block
            layers.Conv2D(256, (3, 3), activation='relu'),
            layers.GlobalAveragePooling2D(),
            
            # Dense layers
            layers.Dense(512, activation='relu'),
            layers.Dropout(0.5),
            layers.Dense(256, activation='relu'),
            layers.Dropout(0.3),
            layers.Dense(self.num_classes, activation='softmax')
        ])
        
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=0.001),
            loss='categorical_crossentropy',
            metrics=['accuracy']
        )
        
        return model
    
    def train_model(self, X, y, epochs=50, batch_size=32):
        """Train the neural network."""
        print(f"Training model on {len(X)} samples...")
        
        # Split data
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=np.argmax(y, axis=1)
        )
        
        print(f"Training set: {len(X_train)} samples")
        print(f"Validation set: {len(X_val)} samples")
        
        # Create model
        self.model = self.create_model()
        
        # Print model summary
        print("\nModel Architecture:")
        self.model.summary()
        
        # Callbacks
        callbacks = [
            keras.callbacks.EarlyStopping(
                monitor='val_accuracy',
                patience=10,
                restore_best_weights=True
            ),
            keras.callbacks.ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.5,
                patience=5,
                min_lr=1e-7
            )
        ]
        
        # Data augmentation for additional robustness
        datagen = keras.preprocessing.image.ImageDataGenerator(
            rotation_range=10,
            width_shift_range=0.1,
            height_shift_range=0.1,
            horizontal_flip=False,  # Cards shouldn't be flipped
            zoom_range=0.1,
            brightness_range=[0.8, 1.2]
        )
        
        # Train model
        print("\nStarting training...")
        history = self.model.fit(
            datagen.flow(X_train, y_train, batch_size=batch_size),
            steps_per_epoch=len(X_train) // batch_size,
            epochs=epochs,
            validation_data=(X_val, y_val),
            callbacks=callbacks,
            verbose=1
        )
        
        return history
    
    def save_model(self, model_path="training_data/acr_card_model"):
        """Save trained model and label encoder."""
        if self.model is None:
            raise ValueError("No model to save. Train the model first.")
        
        model_dir = Path(model_path)
        model_dir.mkdir(parents=True, exist_ok=True)
        
        # Save model
        self.model.save(model_dir / "model.h5")
        print(f"Model saved to {model_dir / 'model.h5'}")
        
        # Save label encoder
        import joblib
        joblib.dump(self.label_encoder, model_dir / "label_encoder.pkl")
        print(f"Label encoder saved to {model_dir / 'label_encoder.pkl'}")
        
        # Save training metadata
        metadata = {
            "num_classes": self.num_classes,
            "img_height": self.img_height,
            "img_width": self.img_width,
            "classes": list(self.label_encoder.classes_),
            "training_type": "advanced_angle_training",
            "model_type": "CNN_ACR_Card_Recognition"
        }
        
        with open(model_dir / "metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"Metadata saved to {model_dir / 'metadata.json'}")
    
    def evaluate_model(self, X_test, y_test):
        """Evaluate model performance."""
        if self.model is None:
            raise ValueError("No model to evaluate. Train the model first.")
        
        print("Evaluating model...")
        test_loss, test_accuracy = self.model.evaluate(X_test, y_test, verbose=0)
        
        print(f"Test Accuracy: {test_accuracy:.4f}")
        print(f"Test Loss: {test_loss:.4f}")
        
        return test_accuracy, test_loss

def main():
    """Main training function."""
    print("ACR Card Recognition Neural Network Training")
    print("=" * 60)
    
    # Initialize trainer
    trainer = ACRCardNetworkTrainer()
    
    # Check if advanced dataset exists
    dataset_dir = "training_data/advanced_dataset"
    if not Path(dataset_dir).exists():
        print(f"Advanced dataset not found at {dataset_dir}")
        print("Generating advanced dataset first...")
        
        from app.training.advanced_angle_trainer import AdvancedAngleTrainer
        angle_trainer = AdvancedAngleTrainer()
        total_generated = angle_trainer.generate_poker_training_set(
            templates_dir="training_data/templates",
            output_dir=dataset_dir,
            variants_per_card=200
        )
        print(f"Generated {total_generated} training examples")
    
    try:
        # Load training data
        X, y = trainer.load_training_data(dataset_dir)
        
        # Train model
        history = trainer.train_model(X, y, epochs=30, batch_size=32)
        
        # Save model
        trainer.save_model()
        
        print("\n" + "=" * 60)
        print("Training completed successfully!")
        print("Model saved and ready for ACR card recognition")
        
        # Final evaluation
        final_accuracy = max(history.history['val_accuracy'])
        print(f"Best validation accuracy: {final_accuracy:.4f}")
        
    except Exception as e:
        print(f"Training failed: {e}")
        raise

if __name__ == "__main__":
    main()