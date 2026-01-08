from fastapi import FastAPI
import requests

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Backend FastAPI OK"}

@app.get("/ollama")
def call_ollama():
    response = requests.post(
        "http://ollama:11434/api/generate",
        json={"model": "llama3", "prompt": "Bonjour"}
    )
    return response.json()
