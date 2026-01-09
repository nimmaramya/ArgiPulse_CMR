from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
import json
import requests
import datetime
#from .models import SoilCropRecommendation
#from .models import CropDuration
#from .models import PlantingCalendar
#from .disease_prediction_service import disease_service

@csrf_exempt
def dialogflow_webhook(request):
    # print(request)
    # print("****************************")
    if request.method == 'POST':
        try:
            # Handle both JSON and multipart form data
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            elif request.content_type and 'multipart/form-data' in request.content_type:
                # For file uploads, we'll get parameters from form data
                data = {
                    'queryResult': {
                        'intent': {'displayName': 'crop_disease_prediction'},
                        'parameters': {
                            'crop': request.POST.get('crop', '')
                        }
                    }
                }
            else:
                data = json.loads(request.body)
            # print(data)
            intent = data['queryResult']['intent']['displayName']

            if intent == 'get_weather':
                parameters = data['queryResult']['parameters']

                # Handle default city
                city = parameters.get('geo-city')
                if not city or city.strip() == '':
                    city = 'Hyderabad'
                    # print("boo",city,"m")

                # Handle default date
                date = parameters.get('date-time')
                if not date or date.strip() == '':
                    date = datetime.date.today().isoformat()
                    # print("me",date,"rrr")

                # Weather API
                api_key = "b1ecbbe66c7efb6ecacc284013dc655a"
                url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={api_key}&units=metric"

                try:
                    weather_data = requests.get(url).json()

                    if weather_data.get('cod') != "200":
                        weather_response = f"Sorry, I couldn't find the weather for {city}."
                    else:
                        date=date[:10:]
                        # print(date)
                        #print(weather_data)
                        forecasts = weather_data['list']
                        day_forecasts = [f for f in forecasts if (f['dt_txt'].startswith(date) and (f['dt_txt'].endswith('09:00:00') or f['dt_txt'].endswith('18:00:00')))]
                        parts = [f"Forecast for {city} on {date}:"]
                        # print(day_forecasts)
                        if len(day_forecasts)>=2:
                            parts.append(f"morning 🌅 : {day_forecasts[0]['main']['temp']} C and {day_forecasts[0]['weather'][0]['description']}")
                            parts.append(f"evening 🌇 : {day_forecasts[1]['main']['temp']} C and {day_forecasts[1]['weather'][0]['description']}")
                        elif len(day_forecasts)==1:
                            parts.append(f"morning 🌅 : {day_forecasts[0]['main']['temp']} C and {day_forecasts[0]['weather'][0]['description']}")
                        else:
                            parts.append("sorry iam unable to fetch weather right now")
                        weather_response = "\n".join(parts)

                except Exception as e:
                    weather_response = f"Error fetching weather data: {str(e)}"

                return JsonResponse({"fulfillmentText": weather_response})
            elif intent == 'get_irrigation_advice':
                parameters = data['queryResult']['parameters']
                crop = parameters.get('crop-name')
                soil = parameters.get('soil-type')

                if not crop or not soil:
                    response = "Please provide both the crop type and the soil type."
                else:
                    tip = get_irrigation_tip(crop, soil)
                    if "error" in tip:
                        response = tip["error"]
                    else:
                        response = (
                            f"Irrigation advice for {crop} in {soil} soil:\n\n"
                            f"🌱 Seeding: {tip['seeding']}\n\n"
                            f"🌸 Flowering: {tip['flowering']}\n\n"
                            f"🍓 Fruitful stage: {tip['fruitful']}"
                        )

                return JsonResponse({"fulfillmentText": response})
            elif intent == "crop_recomandition":
                parameters = data['queryResult']['parameters']
                soil = parameters.get('soil-type')
                soil=soil.lower()
                # print("soil is",soil)
                crops = SoilCropRecommendation.objects.filter(soil_type__iexact=soil).order_by('priority')
                # print("*************************")
                # print(crops)
                if crops.exists():
                    crop_list = [crop.crop_name for crop in crops]
                    response_text = f"Crops suitable for {soil} soil in priority order are: " + ", ".join(crop_list)
                else:
                    response_text = f"Sorry, I don't have crop suggestions for {soil} soil yet."

                return JsonResponse({'fulfillmentText': response_text})
            elif intent=='crop_duration':
                parameters=data['queryResult']['parameters']
                crop=parameters.get('crop-name')
                crop=crop.lower()
                # print("crop is ",crop)
                duration=CropDuration.objects.filter(crop_name__iexact=crop)
                if duration.exists():
                    return JsonResponse({"fulfillmentText":str(duration.first())})
                else:
                    return JsonResponse({"fulfillmentText":"As of now I dont have the data of particular crop"})
                print("duration is ",str(duration.first()))
            elif intent=='Planting Calendar':
                # print("&&&&&&&&&&&&&&&&&&&")
                parameters=data['queryResult']['parameters']
                # print(parameters)
                crop=parameters.get('crop-name')
                crop=crop.lower()
                state = parameters.get('geo-state')
                if not state or state.strip() == '':
                    state = 'Telangana'
                # print(crop," ",state)
                try:
                    entry = PlantingCalendar.objects.get(crop_name__iexact=crop, region__iexact=state)
                    print("entry is ",entry)
                    response_text = (
                        f"The best time to plant {entry.crop_name.title()} in {entry.region.title()} "
                        f"is from {entry.planting_start_month} to {entry.planting_end_month}."
                    )
                except PlantingCalendar.DoesNotExist:
                    response_text = (
                        f"Sorry, I couldn't find the planting season for {crop.title()} in {state.title()}."
                    )

                return JsonResponse({
                    "fulfillmentText": response_text
                })
            elif intent == 'crop_disease_prediction':
                parameters = data['queryResult']['parameters']
                crop = parameters.get('crop')
                
                if not crop:
                    response = "Please provide the crop type for disease prediction."
                else:
                    # Check if there's an uploaded file
                    if 'image' in request.FILES:
                        uploaded_file = request.FILES['image']
                        try:
                            # Save uploaded file temporarily
                            import tempfile
                            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
                                for chunk in uploaded_file.chunks():
                                    temp_file.write(chunk)
                                temp_file_path = temp_file.name
                            
                            # Use the disease prediction service with uploaded file
                            prediction_result = disease_service.predict_disease(temp_file_path, crop)
                            response = disease_service.format_response(prediction_result)
                            
                            # Clean up temporary file
                            import os
                            if os.path.exists(temp_file_path):
                                os.unlink(temp_file_path)
                                
                        except Exception as e:
                            response = f"Sorry, I encountered an error while analyzing your image: {str(e)}"
                    else:
                        response = "Please upload an image file for disease prediction."
                
                return JsonResponse({"fulfillmentText": response})
            return JsonResponse({"fulfillmentText": "Sorry, I only handle weather queries for now."})

        except Exception as e:
            return JsonResponse({"fulfillmentText": f"Error: {str(e)}"})

    return JsonResponse({"fulfillmentText": "Only POST requests are accepted."})



#from .models import CropSoilIrrigation
def get_irrigation_tip(crop, soil):
    try:
        # print("hii")
        entry = CropSoilIrrigation.objects.get(crop_type__iexact=crop, soil_type__iexact=soil)
        # print(entry)
        return {
            "seeding": entry.seeding_advice,
            "flowering": entry.flowering_advice,
            "fruitful": entry.fruitful_advice
        }
    except CropSoilIrrigation.DoesNotExist:
        # print("hello")
        # print(entry)
        return {
            "error": f"No irrigation data found for crop '{crop}' and soil '{soil}'."
        }

def test_upload_page(request):
    """Test page for file upload functionality."""
    return render(request, 'test_upload.html')

def crop_disease_prediction(request):
    """Simple crop disease prediction using predict.py directly."""
    result = None
    
    if request.method == 'POST':
        crop_name = request.POST.get('crop_name', '').strip()
        uploaded_file = request.FILES.get('image')
        
        if crop_name and uploaded_file:
            try:
                # Import predict.py functionality directly
                import sys
                import os
                sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'CDDM'))
                
                # Load the predict.py functions
                import tensorflow as tf
                from tensorflow.keras.models import load_model
                from tensorflow.keras.preprocessing import image
                import numpy as np
                import json
                from collections import defaultdict
                import tempfile
                
                # Paths to model files
                base_path = os.path.join(os.path.dirname(__file__), '..', '..', 'CDDM')
                model_path = os.path.join(base_path, 'crop_disease_model_mobilenetv2.h5')
                class_names_path = os.path.join(base_path, 'class_names_mobilenetv2.txt')
                pesticides_path = os.path.join(base_path, 'pesticides.json')
                
                # Load model and data
                model = load_model(model_path)
                
                with open(class_names_path, "r") as f:
                    class_names = [line.strip() for line in f.readlines()]
                
                with open(pesticides_path, "r") as f:
                    pesticide_data = json.load(f)
                
                # Build crop-to-class index map
                crop_to_indices = defaultdict(list)
                for idx, name in enumerate(class_names):
                    crop = name.split("_")[0].lower()
                    crop_to_indices[crop].append(idx)
                
                # Save uploaded file temporarily
                with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
                    for chunk in uploaded_file.chunks():
                        temp_file.write(chunk)
                    temp_file_path = temp_file.name
                
                # Run prediction (same logic as predict.py)
                selected_crop = crop_name.lower()
                
                if selected_crop not in crop_to_indices:
                    result = {
                        'error': f"Crop '{selected_crop}' not found in our database. Supported crops: {', '.join(crop_to_indices.keys())}"
                    }
                else:
                    # Load and preprocess image
                    img = image.load_img(temp_file_path, target_size=(180, 180))
                    img_array = image.img_to_array(img) / 255.0
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
                    
                    # Get pesticide recommendation
                    recommendation = pesticide_data.get(predicted_class)
                    
                    # Extract disease name from predicted class (remove crop name and underscores)
                    disease_name = predicted_class.split('_', 1)[1].replace('_', ' ').title()
                    
                    # Encode uploaded image for display
                    uploaded_file = request.FILES.get('image')
                    if uploaded_file:
                        import base64
                        # Read the uploaded file and encode as base64
                        uploaded_file.seek(0)  # Reset file pointer
                        image_data = uploaded_file.read()
                        image_base64 = base64.b64encode(image_data).decode('utf-8')
                        
                        result = {
                            'disease_name': disease_name,
                            'recommendation': recommendation,
                            'uploaded_image_base64': image_base64
                        }
                    else:
                        result = {
                            'disease_name': disease_name,
                            'recommendation': recommendation
                        }
                
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    
            except Exception as e:
                result = {
                    'error': f"Prediction failed: {str(e)}"
                }
        else:
            result = {
                'error': 'Please provide both crop name and image file.'
            }
    
    return render(request, 'crop_disease.html', {'result': result})

