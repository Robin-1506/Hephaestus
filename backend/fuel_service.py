import requests
import math

API_URL = "https://data.economie.gouv.fr/api/records/1.0/search/"

# ======================================================
# Distance Haversine (remplace geopy)
# ======================================================
def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0  # Rayon de la Terre en km

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(d_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    )

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


# ======================================================
# Géocodage texte → latitude / longitude
# ======================================================
def geocode_location(location: str):
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": location,
        "format": "json",
        "limit": 1
    }

    headers = {
        "User-Agent": "fuel-api/1.0"
    }

    response = requests.get(url, params=params, headers=headers, timeout=10)
    response.raise_for_status()

    results = response.json()
    if not results:
        return None

    return {
        "lat": float(results[0]["lat"]),
        "lon": float(results[0]["lon"])
    }


# ======================================================
# Fonction principale
# ======================================================
def fetch_stations(
    carburant: str,
    rayon_km: float = 10,
    top_n: int = 5,
    lat: float | None = None,
    lon: float | None = None,
    location: str | None = None
):
    # -------- Déterminer le centre de recherche --------
    if location:
        coords = geocode_location(location)
        if not coords:
            raise ValueError("Lieu introuvable")
        lat = coords["lat"]
        lon = coords["lon"]

    if lat is None or lon is None:
        raise ValueError("Latitude et longitude requises")

    # -------- Paramètres API --------
    params = {
        "dataset": "prix-des-carburants-en-france-flux-instantane-v2",
        "rows": 100,
        "q": carburant,
        "geofilter.distance": f"{lat},{lon},{rayon_km * 1000}"
    }

    print("📡 API_URL :", API_URL)
    print("📍 Centre :", lat, lon)
    print("📏 Rayon (km) :", rayon_km)

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

        dist_km = haversine_km(lat, lon, lat_s, lon_s)

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
