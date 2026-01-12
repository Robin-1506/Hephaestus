from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen3:latest"

class PromptRequest(BaseModel):
    prompt: str

class AIResponse(BaseModel):
    response: str

@app.get("/")
def health_check():
    return {"status": "Ollama FastAPI backend running"}

@app.post("/chat", response_model=AIResponse)
def chat_with_ollama(data: PromptRequest):

    payload = {
        "model": MODEL_NAME,
        "prompt": data.prompt,
        "stream": False,
        "temperature": 0.7,
        "num_predict": 1024
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=120)
        response.raise_for_status()

        result = response.json()
        print("Réponse brute Ollama:", result)

        return {"response": result.get("response", "Réponse vide")}

    except Exception as e:
        return {"response": f"Erreur Ollama: {str(e)}"}
