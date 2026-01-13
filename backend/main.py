from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware # Added this import as it is required for CORS
from pydantic import BaseModel
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

# --- From Embedding Branch: New Feature ---
@app.post("/find-fuel")
def find_fuel(data: PromptRequest):
    print(f"Analyzing: {data.prompt}")
    
    # 1. Ask Ollama (Make sure "qwen3" is the right name or use MODEL_NAME if you want to share)
    # Note: You are using "qwen3:0.6b" here specifically for embedding/extraction
    extracted = embedding.extract_search_params(data.prompt, model_name="qwen3:0.6b")
    
    if not extracted or "city" not in extracted:
        raise HTTPException(status_code=400, detail="AI could not understand the city or fuel.")

    # 2. Get Coordinates
    coords = embedding.get_coordinates(extracted["city"])
    if not coords:
        raise HTTPException(status_code=404, detail="City not found.")

    # 3. Get Prices
    stations = embedding.fetch_fuel_data(
        coords['lat'], coords['lon'], extracted.get("fuel_type", "Gazole")
    )

    return {"analysis": extracted, "results": stations}

# --- From Main Branch: Existing Features ---
@app.get("/")
def health_check():
    return {"status": "Ollama FastAPI backend running"}

@app.post("/chat", response_model=AIResponse)
def chat_with_ollama(data: PromptRequest):
    print(data.prompt)
    payload = {
        "model": MODEL_NAME,
        "prompt": data.prompt,
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