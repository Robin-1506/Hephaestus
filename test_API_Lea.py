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
