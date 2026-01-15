from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import os
import re
from fuel_service import fetch_stations

# ======================================================
# ================== HELPERS ==========================
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
# ================== APP ==============================
# ======================================================

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
# ================== CHAT =============================
# ======================================================

@app.post("/chat", response_model=AIResponse)
def chat_with_ollama(data: PromptRequest):

    prompt_lower = data.prompt.lower()

    fuel_keywords = [
    # Carburants (général)
    "carburant", "carburants", "fuel", "essence", "diesel", "gazole", "gasoil",
    "sans plomb", "sans-plomb", "plomb", "super",

    # Types essence
    "sp95", "sp 95", "sp98", "sp 98", "e10", "e-10", "e85", "bioéthanol",
    "ethanol", "éthanol",

    # Diesel & dérivés
    "diesel+", "diesel plus", "gazole+", "gazole plus",
    "diesel premium", "gazole premium",

    # Énergies alternatives
    "gpl", "gplc", "gaz", "gaz naturel", "gnv",
    "électrique", "electric", "borne", "borne de recharge",
    "recharge", "recharger", "chargeur", "superchargeur",
    "hydrogène", "h2",

    # Stations-service
    "station", "station-service", "station service", "pompe", "pompes",
    "pompe à essence", "pompe essence",
    "aire d'autoroute", "aire de service",

    # Marques courantes
    "total", "totalenergies", "total énergie",
    "shell", "esso", "bp",
    "carrefour", "auchan", "leclerc", "intermarché", "super u",
    "casino", "avиа", "eni",

    # Prix & coût
    "prix", "coût", "tarif", "facture",
    "moins cher", "moins chère", "pas cher", "bon marché",
    "cher", "chère", "économique",
    "comparateur", "comparaison",

    # Actions & usage
    "faire le plein", "plein", "plein d'essence", "plein carburant",
    "ravitailler", "ravitaillement",
    "consommation", "conso", "l/100", "litre", "litres",

    # Paiement
    "paiement", "payer", "carte", "cb", "sans contact",
    "24/24", "24h", "automate"
    ]

    is_fuel_request = any(k in prompt_lower for k in fuel_keywords)

    if not is_fuel_request:
        return AIResponse(
            response=(
                "❌ Je suis spécialisé uniquement dans la recherche de stations-service, "
                "de carburants et de prix. "
                "Merci de poser une question liée à l'essence ou à l'énergie."
            )
        )

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
    FUEL_MAP = {
        "gazole": "gazole",
        "diesel": "gazole",
        "sp95": "sp95",
        "sp 95": "sp95",
        "sp98": "sp98",
        "sp 98": "sp98",
        "e10": "e10",
        "e-10": "e10",
        "e85": "e85",
        "bioéthanol": "e85",
        "ethanol": "e85",
        "éthanol": "e85",
        "super": "sp95",
        "gpl": "gplc",  # correspond au dataset, vérifier si gpl_prix ou gplc_prix
        "gplc": "gplc",
        "gaz": "gplc",
        "gaz naturel": "gnv",
        "gnv": "gnv",
        "électrique": "elec",
        "electric": "elec",
        "hydrogène": "h2",
        "h2": "h2"
    }

    fuel_type = "gazole"  # valeur par défaut
    prompt_lower = data.prompt.lower()
    for key, val in FUEL_MAP.items():
        if key in prompt_lower:
            fuel_type = val
            break

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
        f"⛽ Station {fuel_type} la moins chère :\n\n"
        f"📍 {best['address']} – {best['city']}\n"
        f"💰 Prix : {best['price']} €/L\n"
        f"🚗 Distance : {best['distance_km']} km\n\n\n"
        f"Autres stations proches :\n\n"
    )

    for i, s in enumerate(stations[1:], 1):
        response += (
            f"{i}. {s['address']} ({s['city']}) – "
            f"{s['price']} €/L – {s['distance_km']} km\n\n"
        )

    return AIResponse(response=response)
