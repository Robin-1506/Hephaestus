"""À partir d’une API qui donne des mots random, on affiche un mot random dans le terminal

python3 -m venv "Test_FastAPI”
source Test_FastAPI/bin/activate
pip install FastAPI
pip install uvicorn requests
uvicorn test_API_Lea:app --port 8000 --reload  ⇒ pour lancer le serveur FastAPI

control + C pour revenir au bash

deactivate ⇒ pour revenir dans l’environnement d’origine"""


from fastapi import FastAPI

import requests

import random

app = FastAPI()

BASE_DE_DONNEES = [
    {"word": "python", "category": "programmation", "difficulty": "facile"},
    {"word": "fastapi", "category": "web", "difficulty": "moyen"},
    {"word": "docker", "category": "devops", "difficulty": "difficile"},
    {"word": "ollama", "category": "ia", "difficulty": "moyen"}
]

@app.get("/words/random")
async def get_random():
    return random.choice(BASE_DE_DONNEES)


@app.get("/")
async def root():
    return {"message": "Hello World"}

"""@app.get("/random-word")
async def random_word_backend():
    url = "https://www.wordgamedb.com/api/v2/words/random"
    response = requests.get(url)
    data = response.json()
    return {"random_word_backend": data["word"]}"""