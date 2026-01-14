from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import os
import re

def extract_radius(prompt: str, default_radius: float = 15) -> float:
    """
    Extrait le rayon en km depuis le texte. 
    Si aucun rayon trouvé, retourne default_radius.
    """
    match = re.search(r"(\d+(?:\.\d+)?)\s*(?:km|kilom[eè]tres?)", prompt.lower())
    if match:
        return float(match.group(1))
    return default_radius

# --- Services internes ---
from fuel_service import fetch_stations
import embedding

app = FastAPI(title="Ollama + Carburant API")

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Ollama config ---
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "ollama:11434")
if not OLLAMA_HOST.startswith("http"):
    OLLAMA_BASE_URL = f"http://{OLLAMA_HOST}"
else:
    OLLAMA_BASE_URL = OLLAMA_HOST

OLLAMA_URL = f"{OLLAMA_BASE_URL}/api/generate"
MODEL_NAME = "llama3"

# --- Models ---
class PromptRequest(BaseModel):
    prompt: str
    latitude: float | None = None
    longitude: float | None = None

class AIResponse(BaseModel):
    response: str

# --- Health check ---
@app.get("/")
def health():
    return {"status": "OK"}

# ==========================================================
# ======================== CHAT =============================
# ==========================================================
@app.post("/chat", response_model=AIResponse)
def chat_with_ollama(data: PromptRequest):

    prompt_lower = data.prompt.lower()

    # -------- Détection carburant --------
    fuel_keywords = [
        "essence", "carburant", "gazole", "diesel",
        "sp95", "sp98", "e10", "e85",
        "station", "prix", "moins chère"
    ]

    is_fuel_request = any(k in prompt_lower for k in fuel_keywords)

    # ======================================================
    # CAS 1 : REQUÊTE STATION ESSENCE (MODE STRICT)
    # ======================================================
    if is_fuel_request:

        # -------- Détection localisation --------
        near_me_keywords = [
            "autour de moi", "près de moi", "pres de moi",
            "à côté de moi", "a coté de moi",
            "ma position", "là où je suis"
        ]

        is_near_me = any(k in prompt_lower for k in near_me_keywords)
        
        # -------- Localisation --------
        search_lat = None
        search_lon = None

        # Extraire la ville ou l'adresse du prompt
        def extract_city(prompt: str):
            prompt = prompt.lower()
            # à <ville>
            match = re.search(r"\bà ([A-Za-zÀ-ÿ \-]+?)(?:\s|$)", prompt)
            if match:
                return match.group(1).strip()
            # autour de <ville>
            match = re.search(r"\bautour de ([A-Za-zÀ-ÿ \-]+?)(?:\s|$)", prompt)
            if match:
                return match.group(1).strip()
            # autour <ville> (sans "de")
            match = re.search(r"\bautour ([A-Za-zÀ-ÿ \-]+?)(?:\s|$)", prompt)
            if match:
                return match.group(1).strip()
            # près de <ville>
            match = re.search(r"\bprès de ([A-Za-zÀ-ÿ \-]+?)(?:\s|$)", prompt)
            if match:
                return match.group(1).strip()
            return None

        city_name = extract_city(data.prompt)

        # Géocoder la ville si trouvée
        coords = None
        if city_name:
            coords = embedding.get_coordinates(city_name)  # ou geocode_location(city_name)
            if coords is None:
                return AIResponse(
                    response=f"❌ Impossible de trouver la ville '{city_name}'."
                )

        # Si pas de ville extraite, fallback sur latitude/longitude fournie
        if coords is None:
            if data.latitude is not None and data.longitude is not None:
                coords = {"lat": data.latitude, "lon": data.longitude}
            else:
                return AIResponse(
                    response="❌ Impossible de déterminer la localisation. Précisez la ville, l'adresse ou votre position."
                )

        # On a maintenant les coordonnées à utiliser pour la recherche
        search_lat = coords['lat']
        search_lon = coords['lon']

        # -------- Type de carburant --------
        fuel_type = "Gazole"
        if "sp98" in prompt_lower:
            fuel_type = "SP98"
        elif "sp95" in prompt_lower:
            fuel_type = "SP95"
        elif "e10" in prompt_lower:
            fuel_type = "E10"
        elif "e85" in prompt_lower:
            fuel_type = "E85"

        # -------- Appel API carburant --------
        radius_km = extract_radius(data.prompt, default_radius=15)
        stations = fetch_stations(
            lat=search_lat,
            lon=search_lon,
            carburant=fuel_type,
            rayon_km=radius_km,
            top_n=5
        )

        if not stations:
            return AIResponse(
                response=f"Aucune station {fuel_type} trouvée autour de vous."
            )
        
        # -------- Réponse FACTUELLE --------
        best = stations[0]

        response_text = (
            f"🚗 Station {fuel_type} la moins chère autour de vous :\n\n"
            f"📍 {best['address']} – {best['city']}\n"
            f"💰 Prix : {best['price']} €/L\n"
            f"📏 Distance : {best['distance_km']} km\n\n"
            f"Autres stations proches :\n"
        )

        for i, s in enumerate(stations[1:], 1):
            response_text += (
                f"{i}. {s['address']} ({s['city']}) – "
                f"{s['price']} €/L – {s['distance_km']} km\n"
            )

        # 🚫 AUCUN APPEL OLLAMA ICI
        return AIResponse(response=response_text)

    # ======================================================
    # CAS 2 : AUTRE DEMANDE → OLLAMA NORMAL
    # ======================================================
    payload = {
        "model": MODEL_NAME,
        "prompt": data.prompt,
        "stream": False
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=600)
        response.raise_for_status()
        result = response.json()
        return AIResponse(response=result.get("response", ""))

    except Exception as e:
        return AIResponse(response=f"Erreur Ollama: {str(e)}")
