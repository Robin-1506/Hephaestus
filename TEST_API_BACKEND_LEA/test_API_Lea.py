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

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/random-word-API")
async def random_word():
    url = "https://www.wordgamedb.com/api/v2/words/random"
    response = requests.get(url)
    data = response.json()
    #mot = data["word"]
    #print(mot)
    #return response.json()["word"]
    return {"random_word": data["word"]}

@app.get("/random-word-backend")
async def random_word_backend():
    url = "http://127.0.0.1:8001/words/random"
    response = requests.get(url)
    data = response.json()
    #mot = data["word"]
    #print(mot)
    #return response.json()["word"]
    return {"random_word_backend": data["word"]}