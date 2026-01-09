import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
import numpy as np
import json
import os
from collections import defaultdict
import requests
import tempfile
from django.conf import settings

class DiseasePredictionService:
    def __init__(self):
        # Get the path to the CDDM directory
        self.base_path = os.path.join(settings.BASE_DIR, '..', 'CDDM')
        
        # Load model and class names
        model_path = os.path.join(self.base_path, 'crop_disease_model_mobilenetv2.h5')
        class_names_path = os.path.join(self.base_path, 'class_names_mobilenetv2.txt')
        pesticides_path = os.path.join(self.base_path, 'pesticides.json')
        
        self.model = load_model(model_path)
        
        with open(class_names_path, "r") as f:
            self.class_names = [line.strip() for line in f.readlines()]
        
        # Load pesticide recommendations
        with open(pesticides_path, "r") as f:
            self.pesticide_data = json.load(f)
        
        # Build a crop-to-class index map
        self.crop_to_indices = defaultdict(list)
        for idx, name in enumerate(self.class_names):
            crop = name.split("_")[0].lower()
            self.crop_to_indices[crop].append(idx)
    
    def download_image(self, image_url):
        """
        Download image from URL and save to temporary file.
        Returns the path to the temporary file.
        """
        try:
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            
            # Create a temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
            temp_file.write(response.content)
            temp_file.close()
            
            return temp_file.name
        except Exception as e:
            raise Exception(f"Failed to download image: {str(e)}")
    
    def predict_disease(self, img_path, selected_crop):
        """
        Predict disease from image path and crop type.
        Returns a dictionary with prediction results.
        """
        selected_crop = selected_crop.lower()
        
        if selected_crop not in self.crop_to_indices:
            return {
                'error': f"Crop '{selected_crop}' not found in our database. Supported crops: {', '.join(self.crop_to_indices.keys())}"
            }
        
        try:
            # Load and preprocess image
            img = image.load_img(img_path, target_size=(180, 180))
            img_array = image.img_to_array(img) / 255.0  # Normalize
            img_array = tf.expand_dims(img_array, 0)
            
            # Predict
            predictions = self.model.predict(img_array)[0]
            
            # Filter predictions to selected crop
            valid_indices = self.crop_to_indices[selected_crop]
            filtered_probs = [predictions[i] for i in valid_indices]
            best_index_in_filtered = np.argmax(filtered_probs)
            actual_index = valid_indices[best_index_in_filtered]
            predicted_class = self.class_names[actual_index]
            confidence = filtered_probs[best_index_in_filtered] * 100
            
            # Get pesticide recommendation
            recommendation = self.pesticide_data.get(predicted_class)
            
            return {
                'predicted_class': predicted_class,
                'confidence': confidence,
                'recommendation': recommendation,
                'success': True
            }
            
        except Exception as e:
            return {
                'error': f"Prediction failed: {str(e)}",
                'success': False
            }
    
    def predict_from_url(self, image_url, selected_crop):
        """
        Download image from URL and predict disease.
        Returns prediction results and cleans up temporary file.
        """
        temp_file_path = None
        try:
            # Download image
            temp_file_path = self.download_image(image_url)
            
            # Predict disease
            result = self.predict_disease(temp_file_path, selected_crop)
            
            return result
            
        finally:
            # Clean up temporary file
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                except:
                    pass  # Ignore cleanup errors
    
    def format_response(self, prediction_result):
        """
        Format prediction result into natural language response.
        """
        if not prediction_result.get('success', False):
            return prediction_result.get('error', 'Prediction failed')
        
        predicted_class = prediction_result['predicted_class']
        confidence = prediction_result['confidence']
        recommendation = prediction_result['recommendation']
        
        # Extract crop and disease from predicted class
        crop = predicted_class.split('_')[0].title()
        disease = predicted_class.split('_', 1)[1].replace('_', ' ').title()
        
        # Build response
        response_parts = []
        
        if confidence >= 70:
            response_parts.append(f"Your {crop} crop shows {disease} (confidence: {confidence:.1f}%).")
        else:
            response_parts.append(f"Your {crop} crop might have {disease} (confidence: {confidence:.1f}%).")
        
        if recommendation:
            pesticide = recommendation.get('recommended_pesticide', 'No specific recommendation available')
            frequency = recommendation.get('application_frequency', '')
            control_time = recommendation.get('expected_control_time', '')
            
            response_parts.append(f"Recommended treatment: {pesticide}")
            
            if frequency:
                response_parts.append(f"Application: {frequency}")
            
            if control_time:
                response_parts.append(f"Expected control time: {control_time}")
        else:
            response_parts.append("No specific treatment recommendation available.")
        
        return " ".join(response_parts)

# Global instance
disease_service = DiseasePredictionService()
