from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import os
import time

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "ollama:11434")
# Ajoute http:// si absent
if not OLLAMA_HOST.startswith("http"):
    OLLAMA_BASE_URL = f"http://{OLLAMA_HOST}"
    OLLAMA_URL = f"{OLLAMA_BASE_URL}/api/generate"
else:
    OLLAMA_BASE_URL = OLLAMA_HOST
    OLLAMA_URL = f"{OLLAMA_HOST}/api/generate"
MODEL_NAME = "llama3"

class PromptRequest(BaseModel):
    prompt: str

class AIResponse(BaseModel):
    response: str

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
