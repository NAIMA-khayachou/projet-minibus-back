from fastapi import APIRouter
from app.database import crud

router = APIRouter()

@router.get("/stations", tags=["Stations"])
def get_stations():
    """
    Endpoint pour récupérer la liste des stations depuis la base de données.
    """
    stations = crud.get_all_stations()
    formatted_stations = [
        {
            "id": s[0],
            "name": s[1],
            "latitude": s[2],
            "longitude": s[3]
        }
        for s in stations
    ]
    return {"stations": formatted_stations}
