from fastapi import APIRouter
from app.database import crud

router = APIRouter()

@router.get("/routes", tags=["Routes"])
def get_routes():
    """
    Endpoint pour récupérer la liste des trajets optimisés depuis la base de données.
    """
    routes = crud.get_optimized_routes()
    # Formatage simple pour l'API (à adapter selon le front)
    formatted_routes = [
        {
            "id": r[0],
            "minibus": r[1],
            "station_sequence": r[2],
            "total_distance": r[3],
            "total_passengers": r[4],
            "calculation_time": r[5]
        }
        for r in routes
    ]
    return {"routes": formatted_routes}
