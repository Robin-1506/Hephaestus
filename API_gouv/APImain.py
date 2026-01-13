""" Comment ça fonctionne

[Utilisateur]
    |
    | Requête GET /stations?lat=48.85&lon=2.35&carburant=Gazole...
    v
[FastAPI (ton serveur)]
    |
    | Récupère les paramètres : lat, lon, carburant, rayon_km, top_n
    v
[Prépare la requête API externe]
    |
    | params = { dataset, rows=100, q=carburant, geofilter.distance }
    v
[Appel API Externe]
    |
    | requests.get(API_URL, params=params)
    v
[Réponse API Externe]
    |
    | JSON avec toutes les stations filtrées par carburant et rayon (max 100)
    v
[Filtrage et traitement côté serveur]
    |
    | Pour chaque station :
    |   - Vérifie latitude/longitude
    |   - Vérifie prix du carburant
    |   - Calcule distance exacte
    |   - Ajoute si dans le rayon
    v
[Trier par prix]
    |
    | sorted(stations, key=lambda x: x["prix"])
    | top_n = stations les moins chères
    v
[Renvoi JSON]
    |
    | JSONResponse(content=stations_sorted)
    v
[Utilisateur]
    |
    | Reçoit JSON :
    | [
    |   {"id": ..., "adresse": ..., "ville": ..., "prix": ..., "lat": ..., "lon": ..., "distance_km": ...},
    |   ...
    | ]

python3 -m venv "Test_FastAPI”
source Test_FastAPI/bin/activate
pip install FastAPI
pip install uvicorn requests
python -m pip install geopy
uvicorn test_API_Lea:app --port 8000 --reload
"""

# On importe les modules nécessaires

# FastAPI : le framework web pour créer l'API
from fastapi import FastAPI, Query, HTTPException

# JSONResponse : pour renvoyer des réponses en JSON
from fastapi.responses import JSONResponse

# requests : pour faire des appels HTTP à l'API externe
import requests

# geopy.distance : pour calculer la distance entre deux points GPS
from geopy.distance import distance

# Création de l'application FastAPI
app = FastAPI(title="Stations Carburant API Optimisée")

# URL de l'API publique du gouvernement pour les prix des carburants
API_URL = "https://data.economie.gouv.fr/api/records/1.0/search/"

# Définition d'une route GET "/stations" pour récupérer les stations
@app.get("/stations")
def get_stations(
    # Latitude du point central où l'utilisateur veut chercher
    lat: float = Query(..., description="Latitude du point central"),
    
    # Longitude du point central
    lon: float = Query(..., description="Longitude du point central"),
    
    # Type de carburant : Gazole, E10, SP98, etc.
    carburant: str = Query(..., description="Type de carburant (ex: Gazole, E10, SP98)"),
    
    # Rayon autour du point central (en km)
    rayon_km: float = Query(10, description="Rayon en km autour du point"),
    
    # Nombre maximum de stations à retourner (les moins chères)
    top_n: int = Query(5, description="Nombre de stations les moins chères à retourner")
):
    try:
        # 1. Préparer les paramètres pour l'API externe
        # On filtre directement côté API pour ne pas récupérer des milliers de stations inutiles
        params = {
            "dataset": "prix-des-carburants-en-france-flux-instantane-v2",  # nom du dataset
            "rows": 100,  # nombre maximum de stations à récupérer (pour optimiser)
            "q": f"{carburant}",  # filtre sur le carburant
            "geofilter.distance": f"{lat},{lon},{rayon_km*1000}"  # rayon en mètres
        }

        # 2. Appel à l'API externe
        response = requests.get(API_URL, params=params)
        response.raise_for_status()  # déclenche une erreur si le serveur répond mal
        data = response.json().get("records", [])  # on récupère les stations

        # 3. Filtrage et traitement côté serveur
        stations = []

        for station in data:
            fields = station.get("fields", {})  # toutes les infos sur la station
            geom = fields.get("geom")  # coordonnées GPS

            # Extraire latitude et longitude
            if isinstance(geom, list) and len(geom) == 2:
                lat_s, lon_s = geom
            elif isinstance(geom, dict) and "lat" in geom and "lon" in geom:
                lat_s, lon_s = geom["lat"], geom["lon"]
            else:
                # Si on ne trouve pas les coordonnées, on ignore la station
                continue

            # Vérifie que le carburant demandé a un prix
            prix = fields.get(f"{carburant.lower()}_prix")
            if prix is None:
                continue  # si pas de prix, on ignore

            # Calcul de la distance exacte entre le point central et la station
            dist_km = distance((lat, lon), (lat_s, lon_s)).km

            # On garde uniquement les stations dans le rayon demandé
            if dist_km <= rayon_km:
                stations.append({
                    "id": fields.get("id"),              # identifiant unique
                    "adresse": fields.get("adresse"),    # adresse
                    "ville": fields.get("ville"),        # ville
                    "prix": prix,                        # prix du carburant
                    "lat": lat_s,                        # latitude
                    "lon": lon_s,                        # longitude
                    "distance_km": round(dist_km, 2)     # distance arrondie
                })

        # 4. Trier les stations par prix croissant
        stations_sorted = sorted(stations, key=lambda x: x["prix"])[:top_n]

        # 5. Retourner la réponse en JSON
        return JSONResponse(content=stations_sorted)
    
    except requests.RequestException as e:
        # Erreur si l'API externe ne répond pas correctement
        raise HTTPException(status_code=500, detail=f"Erreur API externe: {e}")
    except Exception as e:
        # Toute autre erreur
        raise HTTPException(status_code=500, detail=f"Erreur interne: {e}")
