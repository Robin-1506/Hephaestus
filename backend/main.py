from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import os
import re

# ======================================================
# ================== HELPERS ===========================
# ======================================================

def extract_radius(prompt: str, default_radius: float = 15) -> float:
    match = re.search(r"(\d+(?:\.\d+)?)\s*(?:km|kilom[eè]tres?)", prompt.lower())
    return float(match.group(1)) if match else default_radius


def extract_location_string(prompt: str) -> str | None:
    prompt = prompt.lower()

    # Adresse avec numéro (priorité)
    match = re.search(r"\b(\d+\s+[A-Za-zÀ-ÿ0-9,'\- ]+)", prompt)
    if match:
        location = match.group(1)
        location = re.split(r"(dans|rayon|km|kilom)", location)[0]
        return location.strip(" ,.")

    # Ville seule
    patterns = [
        r"\bà\s+([A-Za-zÀ-ÿ\- ]+)",
        r"\bautour de\s+([A-Za-zÀ-ÿ\- ]+)",
        r"\bprès de\s+([A-Za-zÀ-ÿ\- ]+)",
        r"\bdans\s+([A-Za-zÀ-ÿ\- ]+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, prompt)
        if match:
            location = match.group(1)
            location = re.split(r"(dans|rayon|km|kilom)", location)[0]
            return location.strip(" ,.")

    return None


def geocode_location(location: str):
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {"q": location, "format": "json", "limit": 1}
        headers = {"User-Agent": "fuel-api/1.0"}

        r = requests.get(url, params=params, headers=headers, timeout=10)
        r.raise_for_status()
        data = r.json()

        if not data:
            return None

        return {
            "lat": float(data[0]["lat"]),
            "lon": float(data[0]["lon"]),
        }

    except Exception as e:
        print(f"Geocoding error: {e}")
        return None


# ======================================================
# ================== APP ===============================
# ======================================================

from fuel_service import fetch_stations

app = FastAPI(title="Ollama + Carburant API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "ollama:11434")
OLLAMA_BASE_URL = OLLAMA_HOST if OLLAMA_HOST.startswith("http") else f"http://{OLLAMA_HOST}"
OLLAMA_URL = f"{OLLAMA_BASE_URL}/api/generate"
MODEL_NAME = "llama3"


class PromptRequest(BaseModel):
    prompt: str
    latitude: float | None = None
    longitude: float | None = None


class AIResponse(BaseModel):
    response: str


@app.get("/")
def health():
    return {"status": "OK"}


# ======================================================
# ================== CHAT ==============================
# ======================================================

@app.post("/chat", response_model=AIResponse)
def chat_with_ollama(data: PromptRequest):

    prompt_lower = data.prompt.lower()

    fuel_keywords = [
        "essence", "carburant", "gazole", "diesel",
        "sp95", "sp98", "e10", "e85",
        "station", "prix", "moins chère"
    ]

    is_fuel_request = any(k in prompt_lower for k in fuel_keywords)

    if not is_fuel_request:
        payload = {"model": MODEL_NAME, "prompt": data.prompt, "stream": False}
        r = requests.post(OLLAMA_URL, json=payload, timeout=600)
        r.raise_for_status()
        return AIResponse(response=r.json().get("response", ""))

    # ---------- LOCALISATION ----------
    near_me = any(k in prompt_lower for k in [
        "autour de moi", "près de moi", "ma position", "là où je suis"
    ])

    if near_me:
        if data.latitude is None or data.longitude is None:
            return AIResponse(
                response="❌ Pour une recherche autour de vous, j’ai besoin de votre position."
            )
        search_lat, search_lon = data.latitude, data.longitude

    else:
        location_str = extract_location_string(data.prompt)
        if location_str:
            coords = geocode_location(location_str)
            if not coords:
                return AIResponse(
                    response=f"❌ Impossible de localiser '{location_str}'."
                )
            search_lat, search_lon = coords["lat"], coords["lon"]

        elif data.latitude is not None and data.longitude is not None:
            search_lat, search_lon = data.latitude, data.longitude

        else:
            return AIResponse(
                response="❌ Impossible de déterminer la localisation."
            )

    # ---------- CARBURANT ----------
    fuel_type = "Gazole"
    for f in ["SP98", "SP95", "E10", "E85"]:
        if f.lower() in prompt_lower:
            fuel_type = f

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
            response=f"Aucune station {fuel_type} trouvée dans un rayon de {radius_km} km."
        )

    best = stations[0]

    response = (
        f"🚗 Station {fuel_type} la moins chère :\n\n"
        f"📍 {best['address']} – {best['city']}\n"
        f"💰 Prix : {best['price']} €/L\n"
        f"📏 Distance : {best['distance_km']} km\n\n"
        f"Autres stations proches :\n"
    )

    for i, s in enumerate(stations[1:], 1):
        response += (
            f"{i}. {s['address']} ({s['city']}) – "
            f"{s['price']} €/L – {s['distance_km']} km\n"
        )

    return AIResponse(response=response)
