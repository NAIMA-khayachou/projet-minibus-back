from app.models.bus import Bus
from app.models.station import Station
from app.internal.optimizer import optimize_routes
from app.internal.osrm_engine import get_distance_matrix
from app.database import crud
import logging

logging.basicConfig(level=logging.INFO)

def optimize_routes_service(params=None):
    """
    Orchestration de l'optimisation :
    - Récupère les données nécessaires depuis la base
    - Calcule la matrice de distances
    - Appelle l'optimiseur
    - Formate la réponse pour l'API
    """
    # 1. Récupération des données
    bus_data = crud.get_all_minibuses()
    route_data = crud.get_all_routes()
    station_data = crud.get_all_stations()

    # 2. Calcul matrice distances
    distance_matrix = get_distance_matrix(station_data)
    logging.info("Distance matrix calculated")

    # 3. Définir paramètres si absent
    if params is None:
        params = {"population_size": 50, "generations": 100}

    # 4. Appel de l'optimiseur
    result = optimize_routes(bus_data, route_data, station_data, distance_matrix, params)
    if not isinstance(result, dict):
        result = {"routes": [], "cost": None, "meta": {}}

    logging.info(f"Optimization result: {result}")

    # 5. Préparation réponse
    response = {
        "optimized_routes": result.get("routes", []),
        "total_cost": result.get("cost", None),
        "meta": result.get("meta", {})
    }
    return response
