"""uvicorn test_Backend_API_Lea:app --port 8001 --reload  ⇒ pour lancer le serveur FastAPI sur un autre port que 8000 (ici 8001)
car 8000 est déjà pris par l’autre fichier test_API_Lea.py et donc on peut faire des requêtes entre les deux serveurs
si c'est sur le même port ça marche pas car il y a un conflit de ports"""

from fastapi import FastAPI
import random

app = FastAPI()

# Ta propre base de données simplifiée
BASE_DE_DONNEES = [
    {"word": "python", "category": "programmation", "difficulty": "facile"},
    {"word": "fastapi", "category": "web", "difficulty": "moyen"},
    {"word": "docker", "category": "devops", "difficulty": "difficile"},
    {"word": "ollama", "category": "ia", "difficulty": "moyen"}
]

@app.get("/words/random")
async def get_random():
    # On pioche dans NOTRE liste
    return random.choice(BASE_DE_DONNEES)