from fastapi import APIRouter, HTTPException
from ..models.station import Station # Importer le modèle

# Crée l'objet de routage FastAPI
router = APIRouter()

# Schéma de réponse pour la station (A DEFINIR DANS app/models/station.py)
# from pydantic import BaseModel
# class StationResponse(BaseModel):
#     id: int
#     name: str
#     latitude: float
#     longitude: float

# La route sera accessible à /api/stations (grâce au prefix dans app/main.py)
@router.get("/stations") # , response_model=list[StationResponse])
def get_all_stations():
    """
    Récupère la liste de toutes les stations depuis la DB.
    """
    try:
        stations = Station.get_all()
        # La méthode get_all retourne une liste d'objets, to_dict() les convertit
        stations_data = [station.to_dict() for station in stations]
        
        # FastAPI exige que la réponse soit directe (pas d'objet jsonify enveloppé)
        return {"stations": stations_data} # Ceci deviendra le JSON { "stations": [...] }
        
    except Exception as e:
        # FastAPI lève des HTTPExceptions en cas d'erreur
        raise HTTPException(
            status_code=500, 
            detail=f"Erreur interne lors du chargement des stations: {e}"
        )