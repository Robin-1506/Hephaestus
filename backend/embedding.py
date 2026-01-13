import requests
import json
import logging

# --- CONFIGURATION ---
# "host.docker.internal" lets Docker talk to your Windows/Mac computer
OLLAMA_URL = "http://host.docker.internal:11434/api/generate"

# Government APIs
GEO_API_URL = "https://api-adresse.data.gouv.fr/search/"
FUEL_API_URL = "https://data.economie.gouv.fr/api/explore/v2.1/catalog/datasets/prix-des-carburants-en-france-flux-instantane-v2/records"

def extract_search_params(prompt: str, model_name: str = "qwen3:0.6b"):
    """
    Sends the prompt to LOCAL Ollama to extract City and Fuel.
    """
    system_instruction = (
        "You are a JSON extractor. Extract 'city' and 'fuel_type' from the user prompt. "
        "Fuel type must be one of: Gazole, SP95, SP98, E10, E85, GPLc. "
        "Map 'diesel' to 'Gazole'. "
        "Return ONLY valid JSON. Example: {\"city\": \"Lyon\", \"fuel_type\": \"SP98\"}"
    )

    payload = {
        "model": model_name,  # Make sure this matches 'ollama list'
        "prompt": f"{system_instruction}\nUser Prompt: {prompt}",
        "stream": False,
        "format": "json",  # Forces JSON output
        "temperature": 0.1
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        
        # Ollama returns the text in the 'response' field
        return json.loads(data["response"])

    except Exception as e:
        print(f"Ollama Local Error: {e}")
        return None

def get_coordinates(city_or_address: str):
    """ Converts city name to GPS coordinates """
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
    """ Queries Government Fuel API """
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