import requests
import json
import logging
import re

# --- CONFIGURATION ---
# 1. PASTE YOUR API KEY HERE
API_KEY = "f35ebea6c04645899842cbdb84c869c9.zYegL3mWtObRHESfuKDTWant"  # <--- REPLACE THIS with your actual Qwen Key

# 2. Qwen/DashScope API Endpoint (Standard for Qwen models)
# If you use a different provider (like OpenRouter), change this URL.
API_URL = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1/chat/completions"

# Government APIs (Keep these the same)
GEO_API_URL = "https://api-adresse.data.gouv.fr/search/"
FUEL_API_URL = "https://data.economie.gouv.fr/api/explore/v2.1/catalog/datasets/prix-des-carburants-en-france-flux-instantane-v2/records"

def extract_search_params(prompt: str, model_name: str = "qwen-turbo"):
    """
    Sends the prompt to Qwen Cloud API to extract City and Fuel.
    """
    system_instruction = (
        "You are a JSON extractor. Extract 'city' and 'fuel_type' from the user prompt. "
        "Fuel type must be one of: Gazole, SP95, SP98, E10, E85, GPLc. "
        "Map 'diesel' to 'Gazole'. "
        "Return ONLY valid JSON. No markdown formatting. Example: {\"city\": \"Lyon\", \"fuel_type\": \"SP98\"}"
    )

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "qwen-plus", # Or "qwen-turbo", "qwen-max" depending on your key access
        "messages": [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1 # Low temperature for precise JSON
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        result = response.json()
        
        # Extract the text content from the cloud response
        content = result['choices'][0]['message']['content']
        
        # Clean up if the AI added Markdown code blocks (```json ... ```)
        if "```" in content:
            content = content.replace("```json", "").replace("```", "").strip()

        return json.loads(content)

    except Exception as e:
        print(f"Cloud API Error: {e}")
        # Fallback: If API fails, return None or try regex
        return None

def get_coordinates(city_or_address: str):
    """ Converts city name to Latitude/Longitude using French BAN API """
    params = {"q": city_or_address, "limit": 1}
    try:
        r = requests.get(GEO_API_URL, params=params)
        data = r.json()
        if data["features"]:
            coords = data["features"][0]["geometry"]["coordinates"]
            return {"lon": coords[0], "lat": coords[1]}
    except Exception as e:
        print(f"Geocoding error: {e}")
    return None

def fetch_fuel_data(lat, lon, fuel_type, radius_km=20):
    """ Queries the Government Fuel API """
    radius_meters = radius_km * 1000
    price_col = f"{fuel_type.lower()}_prix"

    where_clause = f"distance(geom, geom'POINT({lon} {lat})', {radius_meters}m)"
    
    params = {
        "where": where_clause,
        "limit": 15,
        "refine": f'carburants_disponibles:"{fuel_type}"'
    }

    try:
        r = requests.get(FUEL_API_URL, params=params)
        r.raise_for_status()
        data = r.json()
        
        results = []
        for record in data.get("results", []):
            try:
                price = record.get(price_col)
                if not price and "price" in record: price = record["price"]

                if price:
                    results.append({
                        "address": record.get("adresse"),
                        "city": record.get("ville"),
                        "fuel_type": fuel_type,
                        "price": float(price),
                        "brand": record.get("services_service", "Unknown")
                    })
            except:
                continue
        
        return sorted(results, key=lambda x: x['price'])
        
    except Exception as e:
        print(f"Fuel API error: {e}")
        return []