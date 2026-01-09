"""À partir d’une API qui donne des mots random, on affiche un mot random dans le terminal

python3 -m venv "Test_FastAPI”
source Test_FastAPI/bin/activate
pip install FastAPI
pip install uvicorn requests
fastapi dev test_API_Lea.py   ⇒ si marche pas essayer : pip install "fastapi[standard]”

control + C pour revenir au bash

deactivate ⇒ pour revenir dans l’environnement d’origine"""


from fastapi import FastAPI

import requests

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/random-word")
async def random_word():
    url = "https://www.wordgamedb.com/api/v2/words/random"
    response = requests.get(url)
    data = response.json()
    mot = data["word"]
    print(mot)
    return response.json()["word"]


