#!/usr/bin/env python3
"""
Quick training script for ACR card recognition with optimized parameters.
"""

import os
import numpy as np
import tensorflow as tf
from pathlib import Path
import cv2
import json
import joblib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

# Suppress TensorFlow warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
tf.get_logger().setLevel('ERROR')

def load_sample_data(dataset_dir, samples_per_card=20):
    """Load a smaller sample for faster training."""
    print(f"Loading sample data: {samples_per_card} images per card")
    
    dataset_path = Path(dataset_dir)
    images, labels = [], []
    
    for card_dir in dataset_path.iterdir():
        if not card_dir.is_dir():
            continue
            
        card_name = card_dir.name
        card_images = list(card_dir.glob("*.png"))[:samples_per_card]
        
        for img_path in card_images:
            try:
                img = cv2.imread(str(img_path))
                if img is None:
                    continue
                    
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                img = cv2.resize(img, (57, 82))
                img = img.astype(np.float32) / 255.0
                
                images.append(img)
                labels.append(card_name)
                
            except:
                continue
    
    print(f"Loaded {len(images)} training samples")
    return np.array(images), np.array(labels)

def create_compact_model():
    """Create a smaller, faster model for quick training."""
    model = tf.keras.Sequential([
        tf.keras.layers.Input(shape=(82, 57, 3)),
        
        # Compact CNN architecture
        tf.keras.layers.Conv2D(16, (5, 5), activation='relu'),
        tf.keras.layers.MaxPooling2D((2, 2)),
        
        tf.keras.layers.Conv2D(32, (3, 3), activation='relu'),
        tf.keras.layers.MaxPooling2D((2, 2)),
        
        tf.keras.layers.Conv2D(64, (3, 3), activation='relu'),
        tf.keras.layers.GlobalAveragePooling2D(),
        
        tf.keras.layers.Dense(128, activation='relu'),
        tf.keras.layers.Dropout(0.5),
        tf.keras.layers.Dense(52, activation='softmax')
    ])
    
    model.compile(
        optimizer='adam',
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )
    
    return model

def quick_train():
    """Quick training function."""
    print("Quick ACR Card Recognition Training")
    print("=" * 50)
    
    # Load sample data
    X, y = load_sample_data("training_data/advanced_dataset", samples_per_card=30)
    
    # Encode labels
    le = LabelEncoder()
    y_encoded = le.fit_transform(y)
    y_categorical = tf.keras.utils.to_categorical(y_encoded, num_classes=52)
    
    # Split data
    X_train, X_val, y_train, y_val = train_test_split(
        X, y_categorical, test_size=0.2, random_state=42
    )
    
    print(f"Training: {len(X_train)}, Validation: {len(X_val)}")
    
    # Create and train model
    model = create_compact_model()
    print("Training model...")
    
    history = model.fit(
        X_train, y_train,
        epochs=15,
        batch_size=32,
        validation_data=(X_val, y_val),
        verbose=1
    )
    
    # Save model
    model_dir = Path("training_data/acr_card_model")
    model_dir.mkdir(parents=True, exist_ok=True)
    
    model.save(model_dir / "model.h5")
    joblib.dump(le, model_dir / "label_encoder.pkl")
    
    # Save metadata
    metadata = {
        "num_classes": 52,
        "img_height": 82,
        "img_width": 57,
        "classes": list(le.classes_),
        "training_type": "quick_advanced_training",
        "model_type": "Compact_CNN_ACR"
    }
    
    with open(model_dir / "metadata.json", 'w') as f:
        json.dump(metadata, f, indent=2)
    
    # Final accuracy
    final_acc = max(history.history['val_accuracy'])
    print(f"\nTraining Complete!")
    print(f"Best validation accuracy: {final_acc:.3f}")
    print(f"Model saved to: {model_dir}")
    
    return model, le

if __name__ == "__main__":
    model, le = quick_train()