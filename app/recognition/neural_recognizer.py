
import numpy as np
import cv2
from pathlib import Path
import json
import joblib
from PIL import Image

class TrainedACRRecognizer:
    """Neural network-based card recognizer using trained ACR model."""
    
    def __init__(self, model_path="training_data/acr_card_model"):
        self.model_path = Path(model_path)
        self.model = None
        self.label_encoder = None
        self.metadata = None
        self.load_model()
    
    def load_model(self):
        """Load trained model and metadata."""
        try:
            # Load TensorFlow/Keras model
            import tensorflow as tf
            self.model = tf.keras.models.load_model(self.model_path / "model.h5")
            
            # Load label encoder
            self.label_encoder = joblib.load(self.model_path / "label_encoder.pkl")
            
            # Load metadata
            with open(self.model_path / "metadata.json", 'r') as f:
                self.metadata = json.load(f)
            
            print(f"Loaded ACR card recognition model with {self.metadata['num_classes']} classes")
            
        except Exception as e:
            print(f"Failed to load neural network model: {e}")
            self.model = None
    
    def preprocess_image(self, image):
        """Preprocess image for neural network prediction."""
        if isinstance(image, Image.Image):
            image = np.array(image)
        
        # Resize to model input size
        height, width = self.metadata['img_height'], self.metadata['img_width']
        image = cv2.resize(image, (width, height))
        
        # Normalize
        image = image.astype(np.float32) / 255.0
        
        # Add batch dimension
        image = np.expand_dims(image, axis=0)
        
        return image
    
    def predict_card(self, image):
        """Predict card from image using neural network."""
        if self.model is None:
            return None, 0.0
        
        try:
            # Preprocess image
            processed_image = self.preprocess_image(image)
            
            # Make prediction
            predictions = self.model.predict(processed_image, verbose=0)
            
            # Get best prediction
            predicted_class_idx = np.argmax(predictions[0])
            confidence = predictions[0][predicted_class_idx]
            
            # Convert to card name
            card_name = self.label_encoder.inverse_transform([predicted_class_idx])[0]
            
            return card_name, float(confidence)
            
        except Exception as e:
            print(f"Neural network prediction failed: {e}")
            return None, 0.0
    
    def is_available(self):
        """Check if neural network model is available."""
        return self.model is not None
