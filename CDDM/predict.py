# predict.py
import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
import numpy as np
import json
import os

# Load model and class names
model = load_model("crop_disease_model_mobilenetv2.h5")

with open("class_names_mobilenetv2.txt", "r") as f:
    class_names = [line.strip() for line in f.readlines()]

# Load pesticide recommendations
with open("pesticides.json", "r") as f:
    pesticide_data = json.load(f)

from collections import defaultdict

# Build a crop-to-class index map
crop_to_indices = defaultdict(list)
for idx, name in enumerate(class_names):
    crop = name.split("_")[0].lower()  # handle cases like "maize_Blight"
    crop_to_indices[crop].append(idx)



def predict_disease(img_path, selected_crop):
    selected_crop = selected_crop.lower()

    if selected_crop not in crop_to_indices:
        print(f"⚠️ Crop '{selected_crop}' not found in class mappings.")
        return

    # Load and preprocess image
    img = image.load_img(img_path, target_size=(180, 180))
    img_array = image.img_to_array(img) / 255.0  # Normalize
    img_array = tf.expand_dims(img_array, 0)

    # Predict
    predictions = model.predict(img_array)[0]

    # Filter predictions to selected crop
    valid_indices = crop_to_indices[selected_crop]
    filtered_probs = [predictions[i] for i in valid_indices]
    best_index_in_filtered = np.argmax(filtered_probs)
    actual_index = valid_indices[best_index_in_filtered]
    predicted_class = class_names[actual_index]
    confidence = filtered_probs[best_index_in_filtered] * 100

    print(f"\n🔍 Predicted Class: {predicted_class}")
    print(f"✅ Confidence: {confidence:.2f}%")

    # Get pesticide recommendation
    recommendation = pesticide_data.get(predicted_class)
    print(recommendation)
    if recommendation:
        print("\n🧪 Pesticide Recommendation:")
        print(f"Crop: {recommendation.get('crop')}")
        print(f"Disease: {recommendation.get('disease')}")
        print(f"Type: {recommendation.get('type')}")
        print(f"Recommended Pesticide: {recommendation.get('recommended_pesticide')}")
        if "application_frequency" in recommendation:
            print(f"Application Frequency: {recommendation.get('application_frequency')}")
        if "expected_control_time" in recommendation:
            print(f"Expected Control Time: {recommendation.get('expected_control_time')}")
    else:
        print("\n⚠️ No pesticide recommendation found for this prediction.")


# Example usage
predict_disease("potato early.png", "potato")