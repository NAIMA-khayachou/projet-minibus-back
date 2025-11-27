from fastapi import APIRouter
from app.internal.route_service import optimize_routes_service

router = APIRouter()

@router.get("/optimize", tags=["Optimization"])
def optimize_routes_endpoint():
    """
    Endpoint pour lancer l'optimisation des itinéraires minibus.
    Retourne les itinéraires optimisés, le coût total et des infos meta.
    """
    result = optimize_routes_service()
    return result
