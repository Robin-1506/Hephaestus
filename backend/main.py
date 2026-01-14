from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import os

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

        # -------- Localisation obligatoire --------
        if is_near_me:
            if data.latitude is None or data.longitude is None:
                return AIResponse(
                    response="❌ Pour chercher autour de vous, j’ai besoin de votre position."
                )
            search_lat = data.latitude
            search_lon = data.longitude
        else:
            return AIResponse(
                response="❌ Précisez si vous cherchez une station *autour de vous*."
            )

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
        stations = fetch_stations(
            lat=search_lat,
            lon=search_lon,
            carburant=fuel_type,
            rayon_km=15,
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
