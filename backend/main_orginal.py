from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware # Added this import as it is required for CORS
from pydantic import BaseModel
from fastapi import Query
from fuel_service import fetch_stations
import requests
import os
import time

# --- From Embedding Branch ---
# IMPORTANT: Ensure this matches your file name (embedding.py)
import embedding 

app = FastAPI()

# --- From Main Branch: Configuration ---
# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "ollama:11434")
# Add http:// if missing
if not OLLAMA_HOST.startswith("http"):
    OLLAMA_BASE_URL = f"http://{OLLAMA_HOST}"
    OLLAMA_URL = f"{OLLAMA_BASE_URL}/api/generate"
else:
    OLLAMA_BASE_URL = OLLAMA_HOST
    OLLAMA_URL = f"{OLLAMA_HOST}/api/generate"

MODEL_NAME = "llama3"

# --- Shared Models ---
class PromptRequest(BaseModel):
    prompt: str
    latitude: float = None  # Optionnel : latitude de l'utilisateur
    longitude: float = None  # Optionnel : longitude de l'utilisateur

class AIResponse(BaseModel):
    response: str

# --- From Main Branch: Helpers ---
def ensure_model_pulled():
    """Ensure the model is pulled, pull it if necessary."""
    try:
        pull_url = f"{OLLAMA_BASE_URL}/api/pull"
        payload = {"name": MODEL_NAME}
        print(f"Pulling model {MODEL_NAME}...")
        response = requests.post(pull_url, json=payload, timeout=600)
        if response.status_code in [200, 201]:
            print(f"Model {MODEL_NAME} pulled successfully")
            return True
        else:
            print(f"Pull failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"Pull error: {str(e)}")
        return False
    
    return False

# --- From Fuel Service Branch: New Endpoint ---
@app.get("/stations")
def get_stations(
    lat: float = Query(...),
    lon: float = Query(...),
    carburant: str = Query(...),
    rayon_km: float = Query(10),
    top_n: int = Query(5),
):
    try:
        return fetch_stations(lat, lon, carburant, rayon_km, top_n)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- From Embedding Branch: New Feature ---
@app.post("/find-fuel")
def find_fuel(data: PromptRequest):

    extracted = embedding.extract_search_params(
        data.prompt,
        model_name="llama3"
    )

    if not extracted or "city" not in extracted:
        raise HTTPException(400, "Ville ou carburant non compris")

    coords = embedding.get_coordinates(extracted["city"])
    if not coords:
        raise HTTPException(404, "Ville introuvable")

    stations = fetch_stations(
        lat=coords["lat"],
        lon=coords["lon"],
        carburant=extracted.get("fuel_type", "Gazole"),
        rayon_km=20,
        top_n=5
    )

    return {
        "analysis": extracted,
        "results": stations
    }

# --- From Main Branch: Existing Features ---
@app.get("/")
def health_check():
    return {"status": "Ollama FastAPI backend running"}

@app.post("/chat", response_model=AIResponse)
def chat_with_ollama(data: PromptRequest):
    print(f"User prompt: {data.prompt}")
    # Mots-clés pour détecter une requête sur les stations essence
    fuel_keywords = [
        "essence", "carburant", "gazole", "diesel",
        "sp95", "sp98", "e10", "e85", "gpl",
        "station", "prix", "moins chère"
    ]

    prompt_lower = data.prompt.lower()

    is_fuel_request = any(k in prompt_lower for k in fuel_keywords)

    if is_fuel_request:
        if data.latitude is None or data.longitude is None:
            return AIResponse(
                response="❌ Je ne peux pas répondre sans votre position (latitude et longitude)."
            )

    # Mots-clés pour détecter une demande de localisation
    location_keywords = ["où", "localisation", "position", "coordonnées", "latitude", "longitude", "ma position", "mon adresse", "près de moi"]
    
    prompt_lower = data.prompt.lower()
    
    enriched_prompt = data.prompt
    
    # Vérifier si l'utilisateur demande sa localisation
    if any(keyword in prompt_lower for keyword in location_keywords):
        print("Détection d'une demande de localisation...")
        if data.latitude is not None and data.longitude is not None:
            enriched_prompt += f"\nL'utilisateur est situé à la latitude {data.latitude} et longitude {data.longitude}."
    
    # Vérifier si c'est une requête sur les stations essence
    if any(keyword in prompt_lower for keyword in fuel_keywords):
        print("Détection d'une requête sur les carburants...")
        try:
            # Extraire ville et type de carburant du prompt
            extracted = embedding.extract_search_params(data.prompt)
            
            if extracted and "city" in extracted:
                print(f"Paramètres extraits: {extracted}")
                
                # Récupérer les coordonnées
                coords = embedding.get_coordinates(extracted["city"])
                
                if coords:
                    # Récupérer les données des stations
                    fuel_type = extracted.get("fuel_type", "Gazole")
                    stations = fetch_stations(
                    lat=data.latitude,
                    lon=data.longitude,
                    carburant=fuel_type,
                    rayon_km=15,
                    top_n=5
                )

                    
                    if stations:
                        # Enrichir le prompt avec les données réelles
                        stations_info = "Voici les stations essence trouvées:\n"
                        for i, station in enumerate(stations[:5], 1):  # Top 5 stations
                            stations_info += f"{i}. {station.get('address', 'Adresse inconnue')} - {station.get('city', '')} - {fuel_type}: {station.get('price', 'N/A')}€/L - Marque: {station.get('brand', 'Unknown')}\n"
                        
                        enriched_prompt = f"{data.prompt}\n\nContexte des stations essence disponibles:\n{stations_info}"
                        print(f"Prompt enrichi avec {len(stations)} stations")
                    if not stations:
                        return AIResponse(
                            response="Aucune station diesel trouvée dans un rayon de 15 km autour de vous."
    )
        
        except Exception as e:
            print(f"Erreur lors de l'enrichissement du prompt: {e}")
            # Continue sans enrichissement si erreur

    payload = {
        "model": MODEL_NAME,
        "prompt": enriched_prompt,
        "stream": False,
        #"temperature": 0.7,
        #"num_predict": 1024
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=600)
        
        # If model not found, try to pull it
        if response.status_code == 404:
            print(f"Model {MODEL_NAME} not found, attempting to pull...")
            if ensure_model_pulled():
                # Retry the request after pulling
                response = requests.post(OLLAMA_URL, json=payload, timeout=120)
            else:
                return AIResponse(response=f"Erreur: Impossible de télécharger le modèle {MODEL_NAME}")
        
        response.raise_for_status()

        result = response.json()
        print("Réponse brute Ollama:", result)

        return AIResponse(response=result.get("response", "Réponse vide"))

    except Exception as e:
        return AIResponse(response=f"Erreur Ollama: {str(e)}")