# app/routers/optimization.py
from fastapi import APIRouter, HTTPException
from app.database.crud import get_all_stations, get_all_reservations, get_all_minibus
from app.internal.osrm_engine import get_cost_matrices
from app.Algorithme.genetic_algoritme import GeneticAlgorithm
import logging
import httpx

router = APIRouter()
logger = logging.getLogger(__name__)

OSRM_BASE_URL = "http://router.project-osrm.org"

async def get_route_geometry(coords_list):
    """
    Récupère la vraie géométrie de route entre plusieurs points via OSRM
    coords_list: [(lon1, lat1), (lon2, lat2), ...]
    Retourne: liste de [lat, lon] pour tracer sur la carte
    """
    if len(coords_list) < 2:
        return []
    
    # Format OSRM: "lon1,lat1;lon2,lat2;..."
    coordinates_str = ";".join([f"{lon},{lat}" for lon, lat in coords_list])
    url = f"{OSRM_BASE_URL}/route/v1/driving/{coordinates_str}"
    
    params = {
        "overview": "full",
        "geometries": "geojson"
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params)
            
        if response.status_code == 200:
            data = response.json()
            if data.get("code") == "Ok" and data.get("routes"):
                # Récupérer la géométrie (liste de [lon, lat])
                geometry = data["routes"][0]["geometry"]["coordinates"]
                # Inverser pour avoir [lat, lon] (format Leaflet)
                return [[lat, lon] for lon, lat in geometry]
        
        logger.warning(f"OSRM route failed: {response.status_code}")
        return []
        
    except Exception as e:
        logger.error(f"Erreur OSRM route: {e}")
        return []


@router.post("/optimize")
async def optimize_routes():
    """
    Lance l'optimisation et retourne la solution avec vraies routes GPS
    """
    try:
        logger.info("🚀 Démarrage de l'optimisation...")
        
        # 1️⃣ Charger les données
        stations_raw = get_all_stations()
        reservations_raw = get_all_reservations()
        minibus_raw = get_all_minibus()
        
        if not stations_raw:
            raise HTTPException(status_code=400, detail="Aucune station")
        if not reservations_raw:
            raise HTTPException(status_code=400, detail="Aucune réservation")
        if not minibus_raw:
            raise HTTPException(status_code=400, detail="Aucun minibus")
        
        logger.info(f"🚀 Lancement de l'optimisation avec {len(minibus_raw)} minibus")
        
        # 2️⃣ Construire stations_dict
        stations_dict = {}
        for (station_id, name, lat, lon) in stations_raw:
            stations_dict[station_id] = {
                'name': name,
                'latitude': lat,
                'longitude': lon
            }
        
        # 3️⃣ Matrices OSRM
        points = [(lon, lat) for (_, _, lat, lon) in stations_raw]
        matrice_durees, matrice_distances = get_cost_matrices(points)
        
        if matrice_distances is None or matrice_durees is None:
            raise HTTPException(status_code=503, detail="OSRM indisponible")
        
        # 4️⃣ Dépôt
        DEPOT_STATION_ID = 2
        
        # 5️⃣ Algorithme génétique
        logger.info("🧬 Lancement de l'algorithme génétique...")
        ga = GeneticAlgorithm(
            reservations=reservations_raw,
            minibus=minibus_raw,
            stations_dict=stations_dict,
            matrice_distances=matrice_distances,
            matrice_durees=matrice_durees,
            depot_station_id=DEPOT_STATION_ID,
            use_osrm=True,
            population_size=50,
            generations=100,
            prob_croisement=0.8,
            prob_mutation=0.2
        )
        
        best_solution, best_details = ga.run()
        
        if best_solution is None:
            raise HTTPException(status_code=500, detail="Optimisation échouée")
        
        # 6️⃣ Convertir en dict
        solution_dict = best_solution.to_dict()
        
        # 7️⃣ AJOUTER les coordonnées ET les vraies routes GPS
        logger.info("🗺️ Calcul des routes GPS réelles...")
        
        for minibus_key, minibus_data in solution_dict.items():
            if minibus_key == "METRIQUES_GLOBALES":
                continue
            
            itineraire = minibus_data.get('itineraire', [])
            coords_sequence = []
            
            # Ajouter lat/lon à chaque arrêt
            for arret in itineraire:
                station_id = arret.get('station_id')
                if station_id and station_id in stations_dict:
                    lat = stations_dict[station_id]['latitude']
                    lon = stations_dict[station_id]['longitude']
                    arret['latitude'] = lat
                    arret['longitude'] = lon
                    coords_sequence.append((lon, lat))
            
            # Récupérer la vraie route GPS via OSRM
            if len(coords_sequence) >= 2:
                route_geometry = await get_route_geometry(coords_sequence)
                minibus_data['route_geometry'] = route_geometry
                logger.info(f"✅ Route OSRM calculée pour {minibus_key}: {len(route_geometry)} points")
            else:
                minibus_data['route_geometry'] = []
        
        logger.info("✅ Optimisation terminée")
        
        return {
            "success": True,
            "solution": solution_dict,
            "metrics": best_details
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/solutions/latest")
async def get_latest_solution():
    """
    Retourne la dernière solution sauvegardée (ou une solution par défaut)
    """
    try:
        # Pour l'instant, retourner une solution vide
        # Plus tard, vous pouvez charger depuis la base de données
        return {
            "success": True,
            "data": {
                "METRIQUES_GLOBALES": {
                    "distance_totale_flotte": 0,
                    "duree_totale_flotte": 0,
                    "nombre_minibus_utilises": 0,
                    "nombre_total_reservations": 0
                }
            }
        }
    except Exception as e:
        logger.error(f"Erreur récupération solution: {e}")
        raise HTTPException(status_code=500, detail=str(e))