from django.shortcuts import render
import sys
import os
import pandas as pd
import requests
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, mean_absolute_error

# Create your views here.
def index(request):
    return render(request, "index.html")

def crop_protection(request):
    return render(request, "crop_protection.html")

def seed(request):
    return render(request, "seeds.html")

def fertilizer(request):
    return render(request, "fertilizers.html")

def tools(request):
    return render(request, "tools.html")

def test_disease_detection(request):
    return render(request, "test_disease_detection.html")

def yield_prediction(request):
    if request.method == 'POST':
        # Get form data
        location = request.POST.get('location', '').strip()
        n = int(request.POST.get('nitrogen', 0))
        p = int(request.POST.get('phosphorus', 0))
        k = int(request.POST.get('potassium', 0))
        ph = float(request.POST.get('ph', 7.0))
        crop = request.POST.get('crop', '').strip().title()
        previous_crop = request.POST.get('previous_crop', '').strip().title()
        
        # Get weather data
        temperature, rainfall = get_weather_data(location)
        
        # Prepare user input
        user_input = {
            "N": n, "P": p, "K": k, "pH": ph,
            "Temperature": temperature,    
            "Rainfall": rainfall,          
            "Crop": crop, "PreviousCrop": previous_crop
        }
        
        # Get prediction result
        result = predict_from_input(user_input)
        
        return render(request, "yield_prediction.html", {
            'result': result,
            'form_data': {
                'location': location,
                'nitrogen': n,
                'phosphorus': p,
                'potassium': k,
                'ph': ph,
                'crop': crop,
                'previous_crop': previous_crop
            }
        })
    
    return render(request, "yield_prediction.html")

# Yield prediction functions (adapted from withoutregion.py)
def fertility_score(n, p, k, ph):
    score = 0
    score += 1 if n < 280 else 2 if n <= 560 else 3
    score += 1 if p < 10 else 2 if p <= 25 else 3
    score += 1 if k < 110 else 2 if k <= 280 else 3

    # pH scoring with strong penalties
    if ph < 4.5 or ph > 9.0:
        return 3  # extreme stress → very low fertility score
    elif ph < 5.5 or ph > 8.5:
        score += 1
    elif 5.5 <= ph <= 6.5 or 7.5 <= ph <= 8.5:
        score += 2
    else:
        score += 3
    return score

def ph_recommendation(ph):
    if ph < 5.5:
        return [
            f"Soil is too acidic (pH={ph:.2f}). Apply lime (CaCO₃) to raise pH.",
            "Incorporate organic compost to buffer acidity.",
            "Avoid ammonium-based fertilizers."
        ]
    elif ph > 8.5:
        return [
            f"Soil is too alkaline (pH={ph:.2f}). Use sulfur or gypsum to lower pH.",
            "Avoid excessive irrigation with alkaline water.",
            "Grow pH-tolerant crops (e.g., barley, cotton)."
        ]
    elif 6.5 <= ph <= 7.5:
        return [f"Soil pH is optimal ({ph:.2f}). No pH correction needed."]
    else:
        return [f"Soil pH ({ph:.2f}) is moderately acidic/alkaline. Monitor crop performance and adjust as needed."]

def get_weather_data(location):
    api_key = "ede03c074c5059fce9a08c247bf12533"
    
    # Geocoding
    geo_url = "http://api.openweathermap.org/geo/1.0/direct"
    geo_params = {
        "q": location,
        "limit": 1,
        "appid": api_key
    }
    
    try:
        geo_res = requests.get(geo_url, params=geo_params)
        geo_res.raise_for_status()
        geo_data = geo_res.json()
        
        if not geo_data:
            return (25.0, 800.0)  # Default values
            
        lat = geo_data[0]['lat']
        lon = geo_data[0]['lon']

    except requests.exceptions.RequestException as e:
        return (25.0, 800.0)

    # Weather data
    weather_url = "https://api.openweathermap.org/data/2.5/weather"
    weather_params = {
        "lat": lat,
        "lon": lon,
        "appid": api_key,
        "units": "metric"
    }

    try:
        weather_res = requests.get(weather_url, params=weather_params)
        weather_res.raise_for_status()
        weather_data = weather_res.json()
        
        temperature = weather_data['main']['temp']
        
        # Location-based rainfall defaults
        location_defaults = {
            "andaman and nicobar islands": 2967.0, "andhra pradesh": 903.6, "arunachal pradesh": 2782.0,
            "assam": 2818.0, "bihar": 1186.0, "chandigarh": 617.0, "chhattisgarh": 1160.0,
            "dadra and nagar haveli": 2000.0, "daman and diu": 2000.0, "delhi": 617.0, "goa": 3005.0,
            "gujarat": 840.0, "haryana": 617.0, "himachal pradesh": 1251.0, "jammu and kashmir": 1011.0,
            "jharkhand": 1326.0, "karnataka": 1150.0, "kerala": 3055.0, "ladakh": 100.0,
            "lakshadweep": 1515.0, "madhya pradesh": 1150.0, "maharashtra": 1180.0, "manipur": 1881.0,
            "meghalaya": 2818.0, "mizoram": 1881.0, "nagaland": 1881.0, "odisha": 1489.0,
            "puducherry": 998.0, "punjab": 649.0, "rajasthan": 494.0, "sikkim": 2739.0,
            "tamil nadu": 998.0, "telangana": 961.0, "tripura": 1881.0, "uttar pradesh": 960.0,
            "uttarakhand": 1667.0, "west bengal": 2089.0,"hyderabad": 961.0, "mumbai": 3005.0, "delhi": 617.0, "chennai": 998.0, "kolkata": 1439.0, "bangalore": 1126.0, "ahmedabad": 800.0, "pune": 901.0, "jaipur": 675.0, "lucknow": 1025.0, "patna": 1186.0, "bhopal": 1017.0, "thiruvananthapuram": 3055.0, "guwahati": 2818.0, "bhubaneswar": 1489.0, "visakhapatnam": 1094.0 
        }

        rainfall = location_defaults.get(location.lower(), 800.0)
        return (temperature, rainfall)

    except requests.exceptions.RequestException as e:
        return (25.0, 800.0)

def predict_from_input(user_input):
    # Load and prepare the model (this would ideally be cached)
    try:
        # Add the project root to Python path to access the dataset
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        dataset_path = os.path.join(project_root, 'yeildprediction', 'augmented_dataset_no_region.csv')
        
        df = pd.read_csv(dataset_path)
        
        # Add derived features
        df["FertilityScore"] = df.apply(lambda row: fertility_score(row["N"], row["P"], row["K"], row["pH"]), axis=1)
        df["NPK_sum"] = df["N"] + df["P"] + df["K"]
        df["N_per_Temp"] = df["N"] / (df["Temperature"] + 1)
        df["Rainfall_per_K"] = df["Rainfall"] / (df["K"] + 1)

        # One-hot encoding
        df_encoded = pd.get_dummies(df, columns=["Crop", "PreviousCrop"])

        # Train models
        X_remark = df_encoded.drop(["Yield", "Remark"], axis=1)
        y_remark = df["Remark"]
        Xr_train, Xr_test, yr_train, yr_test = train_test_split(X_remark, y_remark, test_size=0.2, random_state=42)

        remark_model = RandomForestClassifier(n_estimators=100, random_state=42)
        remark_model.fit(Xr_train, yr_train)

        # Train yield regressor
        df_encoded["PredictedRemark"] = remark_model.predict(X_remark)
        df_encoded["PredictedRemark"] = df_encoded["PredictedRemark"].apply(lambda x: 1 if x == "normal" else 0)

        X_yield = df_encoded.drop(["Yield", "Remark"], axis=1)
        y_yield = df["Yield"]
        Xy_train, Xy_test, yy_train, yy_test = train_test_split(X_yield, y_yield, test_size=0.2, random_state=42)

        yield_model = RandomForestRegressor(n_estimators=200, random_state=42)
        yield_model.fit(Xy_train, yy_train)

        # Process user input
        user_input["FertilityScore"] = fertility_score(user_input["N"], user_input["P"], user_input["K"], user_input["pH"])
        user_input["NPK_sum"] = user_input["N"] + user_input["P"] + user_input["K"]
        user_input["N_per_Temp"] = user_input["N"] / (user_input["Temperature"] + 1)
        user_input["Rainfall_per_K"] = user_input["Rainfall"] / (user_input["K"] + 1)

        df_input = pd.DataFrame([user_input])
        df_input_encoded = pd.get_dummies(df_input)

        # Align columns
        for col in X_remark.columns:
            if col not in df_input_encoded.columns:
                df_input_encoded[col] = 0
        df_input_encoded = df_input_encoded[X_remark.columns]

        predicted_remark = remark_model.predict(df_input_encoded)[0]
        predicted_remark_numeric = 1 if predicted_remark == "normal" else 0

        df_input_encoded["PredictedRemark"] = predicted_remark_numeric

        for col in X_yield.columns:
            if col not in df_input_encoded.columns:
                df_input_encoded[col] = 0
        df_input_encoded = df_input_encoded[X_yield.columns]

        predicted_yield = yield_model.predict(df_input_encoded)[0]
        
        # Apply yield adjustments
        raw_yield, crop_factor, ph_factor, temp_factor, rain_factor, adjusted_yield = adjust_yield(
            predicted_yield, user_input["Crop"], user_input["pH"], user_input["Temperature"], user_input["Rainfall"]
        )

        # Final remark override
        DATASET_AVG_YIELD = 1645
        if adjusted_yield < 0.4 * DATASET_AVG_YIELD:
            predicted_remark = "crop failure"
        elif adjusted_yield < 0.7 * DATASET_AVG_YIELD:
            predicted_remark = "crop failure"
        else:
            predicted_remark = "normal"

        recs = fertilizer_recommendation(
            user_input["Crop"], user_input["N"], user_input["P"], user_input["K"], user_input["pH"], user_input["FertilityScore"]
        )

        return {
            "Soil_Fertility_Score": user_input["FertilityScore"],
            "Predicted_Remark": predicted_remark,
            "Raw_Yield_kg_ha": raw_yield,
            "Crop_Factor": crop_factor,
            "pH_Factor": ph_factor,
            "Temperature_Factor": temp_factor,
            "Rainfall_Factor": rain_factor,
            "Final_Adjusted_Yield_kg_ha": max(5, adjusted_yield/100),
            "final2": max(0,(adjusted_yield/100)-10),
            "Recommendations": recs
        }
        
    except Exception as e:
        # Return error result
        return {
            "error": f"Error processing prediction: {str(e)}",
            "Soil_Fertility_Score": 0,
            "Predicted_Remark": "error",
            "Raw_Yield_kg_ha": 0,
            "Final_Adjusted_Yield_kg_ha": 0,
            "Recommendations": ["Please check your input values and try again."]
        }

def adjust_yield(predicted_yield, crop_name, ph, temperature, rainfall):
    DATASET_AVG_YIELD = 1645  # kg/ha
    crop_baseline = {"Rice": 4000, "Wheat": 3500, "Cotton": 2500, "Maize": 5000, "Soybean": 2800}
    crop_caps = {"Rice": 9000, "Wheat": 8000, "Maize": 8500, "Cotton": 6000, "Soybean": 5000}
    
    crop_key = crop_name.title()
    crop_factor = crop_baseline.get(crop_key, DATASET_AVG_YIELD) / DATASET_AVG_YIELD
    adjusted = predicted_yield * crop_factor

    # pH stress
    if ph < 4.5 or ph > 9:
        ph_factor = 0.03 if ph < 4.5 else 0.05
    elif ph < 5.5 or ph > 8.5:
        ph_factor = 0.5
    elif ph < 6.0 or ph > 8.0:
        ph_factor = 0.8
    else:
        ph_factor = 1.0
    adjusted *= ph_factor

    # Temperature stress
    crop_optimal = {
        "wheat": {"temp_min": 10, "temp_max": 30},
        "rice": {"temp_min": 20, "temp_max": 35},
        "maize": {"temp_min": 18, "temp_max": 32},
        "cotton": {"temp_min": 20, "temp_max": 35},
        "soybean": {"temp_min": 18, "temp_max": 32},
    }
    
    opt = crop_optimal.get(crop_name.lower(), {"temp_min": 20, "temp_max": 30})
    tmin, tmax = opt["temp_min"], opt["temp_max"]
    if temperature < tmin:
        temp_factor = 0.9 if temperature >= tmin - 2 else 0.7
    elif temperature > tmax:
        delta = temperature - tmax
        if delta <= 2: temp_factor = 0.8
        elif delta <= 5: temp_factor = 0.6
        else: temp_factor = 0.4
    else:
        temp_factor = 1.0
    adjusted *= temp_factor

    # Rainfall factor
    rf = rainfall_factor(crop_name, rainfall)
    adjusted *= rf

    # Clamp to crop cap
    adjusted = max(0, min(adjusted, crop_caps.get(crop_key, 10000)))
    return round(predicted_yield, 2), crop_factor, ph_factor, temp_factor, rf, round(adjusted, 2)

def rainfall_factor(crop, rainfall):
    crop_optimal = {
        "wheat": {"rain_min": 300, "rain_max": 900},
        "rice": {"rain_min": 1000, "rain_max": 2000},
        "maize": {"rain_min": 500, "rain_max": 800},
        "cotton": {"rain_min": 500, "rain_max": 1200},
        "soybean": {"rain_min": 700, "rain_max": 1000},
    }
    
    crop = crop.lower()
    if crop not in crop_optimal:
        return 1.0
    rmin, rmax = crop_optimal[crop]["rain_min"], crop_optimal[crop]["rain_max"]
    if rainfall < rmin:
        return rainfall / rmin
    elif rainfall > rmax:
        return rmax / rainfall
    else:
        return 1.0

def fertilizer_recommendation(crop, N, P, K, ph, fertility_score_val):
    recommended_npk = {
        "Rice": {"N": 150, "P": 60, "K": 40},
        "Wheat": {"N": 120, "P": 60, "K": 40},
        "Maize": {"N": 150, "P": 75, "K": 40},
        "Cotton": {"N": 100, "P": 50, "K": 50},
        "Soybean": {"N": 20, "P": 60, "K": 40},
    }
    
    crop = crop.title()
    ideal = recommended_npk.get(crop, {"N": 100, "P": 50, "K": 50})

    add_N = max(0, round(ideal["N"] - N))
    add_P = max(0, round(ideal["P"] - P))
    add_K = max(0, round(ideal["K"] - K))

    recs = [
        f"Apply additional Nitrogen (N): {add_N} kg/ha",
        f"Apply additional Phosphorus (P₂O₅): {add_P} kg/ha",
        f"Apply additional Potassium (K₂O): {add_K} kg/ha"
    ]

    if fertility_score_val <= 6:
        recs.extend(["Apply organic compost", "Use green manure (e.g., Dhaincha)", "Add biofertilizers with FYM"])
    elif fertility_score_val <= 9:
        recs.extend(["Moderately alkaline","Apply balanced NPK (20:20:0)", "Incorporate green manure before sowing"])
    else:
        recs.extend(["Maintain current fertilization routine", "Use micronutrients only if deficiencies appear","Strongly alkaline (sodic soils)","Apply gypsum (CaSO₄) to improve soil structure","Incorporate organic matter to enhance microbial activity"])

    recs.extend(ph_recommendation(ph))
    return recs



# import requests
# from django.http import JsonResponse
# from django.conf import settings

# def govt_agri_updates(request):
#     url = "https://api.data.gov.in//resource/35985678-0d79-46b4-9ed6-6f13308a1d24"

#     params = {
#         "api-key": settings.NEWS_API_KEY,
#         "format": "json",
#         "limit": 10
#     }

#     r = requests.get(url, params=params).json()
#     return JsonResponse(r)



# import requests
# from django.http import JsonResponse
# from django.conf import settings

# def agriculture_news(request):
#     url = "https://newsapi.org/v2/everything"

#     params = {
#     "q": (
#         "crops OR agriculture OR farming OR fertilizer OR pesticide "
#         "OR irrigation OR harvest OR MSP OR mandi OR agri policy OR Subsidy"
#     ),
#     "language": "en",
#     "domains": "thehindu.com,indianexpress.com,livemint.com,business-standard.com,financialexpress.com",
#     "sortBy": "publishedAt",
#     "pageSize": 10,
#     "apiKey": settings.NEWS_API_KEY
#     }

#     # url = "https://newsapi.org/v2/top-headlines"

#     # params = {
#     #     "country": "in",
#     #     "category": "business",
#     #     "q": "agriculture OR farming OR crops",
#     #     "pageSize": 10,
#     #     "apiKey": settings.NEWS_API_KEY
#     # }
#     response = requests.get(url, params=params)
#     data = response.json()

#     return JsonResponse(data)

# import feedparser

# AGRI_FEEDS = [
#     "https://www.thehindu.com/sci-tech/agriculture/feeder/default.rss",
#     "https://www.business-standard.com/rss/agriculture-102.rss",
#     "https://www.financialexpress.com/industry/agriculture/feed/"
# ]


# KEYWORDS = [
#     "agriculture", "farmer", "farmers", "crop", "crops",
#     "fertilizer", "pesticide", "irrigation", "harvest",
#     "msp", "mandi", "kharif", "rabi", "soil"
# ]

# def agri_rss_news(request):
#     articles = []

#     for feed_url in AGRI_FEEDS:
#         feed = feedparser.parse(
#             feed_url,
#             request_headers={
#                 "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
#             }
#         )

#         print(feed_url, "→", len(feed.entries))

#         for entry in feed.entries[:10]:
#             text = f"{entry.get('title','')} {entry.get('summary','')}".lower()
#             if any(k in text for k in KEYWORDS):
#                 articles.append({
#                     "title": entry.title,
#                     "summary": entry.get("summary", ""),
#                     "link": entry.link,
#                     "published": entry.get("published", "")
#                 })

#     return JsonResponse({
#         "status": "ok",
#         "articles": articles[:10]
#     })

# for feed_url in AGRI_FEEDS:
#     feed = feedparser.parse(
#     feed_url,
#     )
#     print(feed_url, "→", len(feed.entries))