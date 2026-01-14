import requests
from geopy.distance import distance

API_URL = "https://data.economie.gouv.fr/api/records/1.0/search/"

def fetch_stations(
    lat: float,
    lon: float,
    carburant: str,
    rayon_km: float = 10,
    top_n: int = 5
):
    params = {
        "dataset": "prix-des-carburants-en-france-flux-instantane-v2",
        "rows": 100,
        "q": carburant,
        "geofilter.distance": f"{lat},{lon},{rayon_km * 1000}"
    }

    response = requests.get(API_URL, params=params, timeout=10)
    response.raise_for_status()

    records = response.json().get("records", [])
    stations = []

    for station in records:
        fields = station.get("fields", {})
        geom = fields.get("geom")

        if not geom or len(geom) != 2:
            continue

        lat_s, lon_s = geom
        prix = fields.get(f"{carburant.lower()}_prix")

        if prix is None:
            continue

        dist_km = distance((lat, lon), (lat_s, lon_s)).km

        if dist_km <= rayon_km:
            stations.append({
                "id": fields.get("id"),
                "address": fields.get("adresse"),
                "city": fields.get("ville"),
                "price": prix,
                "lat": lat_s,
                "lon": lon_s,
                "distance_km": round(dist_km, 2),
                "brand": fields.get("marque")
            })

    return sorted(stations, key=lambda x: x["price"])[:top_n]
