from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from ..database import crud
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Modèles Pydantic
class Metrics(BaseModel):
    distance_totale_flotte: float
    duree_totale_flotte: int
    nombre_minibus_utilises: int
    nombre_minibus_disponibles: int
    toutes_reservations_satisfaites: bool
    nombre_total_reservations: int
    violations_capacite: int
    fitness_score: float

@router.get("/api/metrics", response_model=dict)
async def get_metrics():
    """
    Récupère les métriques du système
    
    Combine les statistiques de la base de données avec les données d'optimisation
    """
    try:
        # Récupération des statistiques de la base
        db_stats = crud.get_database_stats()
        
        # Calcul des métriques
        metrics = {
            "distance_totale_flotte": 28.1,  # TODO: Calculer depuis optimized_routes
            "duree_totale_flotte": 75,  # TODO: Calculer depuis optimized_routes
            "nombre_minibus_utilises": 2,  # TODO: Calculer depuis optimized_routes
            "nombre_minibus_disponibles": db_stats.get('minibus_count', 0),
            "toutes_reservations_satisfaites": True,  # TODO: Vérifier
            "nombre_total_reservations": sum(db_stats.get('reservations_by_status', {}).values()),
            "violations_capacite": 0,  # TODO: Calculer
            "fitness_score": 28.1,  # TODO: Récupérer de la dernière solution
        }
        
        logger.info("✅ Métriques récupérées")
        return metrics
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la récupération des métriques: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la récupération des métriques"
        )
