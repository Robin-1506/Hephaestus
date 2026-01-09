from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests

app = FastAPI()

# CORS pour tests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# URL et modèle pour qwen-3
OLLAMA_URL = "http://localhost:11434/generate"
MODEL_NAME = "qwen3"

class PromptRequest(BaseModel):
    prompt: str

class AIResponse(BaseModel):
    response: str

@app.get("/")
def health_check():
    return {"status": "Ollama FastAPI backend running"}

@app.post("/chat", response_model=AIResponse)
def chat_with_ollama(data: PromptRequest):
    if not data.prompt:
        return {"response": "Le prompt est vide"}

    payload = {
        "model": MODEL_NAME,       # qwen-3
        "prompt": data.prompt,
        "stream": False,
        "max_tokens": 1024,
        "temperature": 0.7
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=60)
        response.raise_for_status()
        result = response.json()
        print("Réponse brute d'Ollama:", result)

        text = result.get("response") or result.get("completion") or "Réponse vide"
        return {"response": text}

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"response": f"Erreur lors de la communication avec Ollama: {str(e)}"}

