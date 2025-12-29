from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from ..database import crud
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter()

# Modèles Pydantic
class OptimizationParams(BaseModel):
    num_minibus: Optional[int] = 3
    capacity: Optional[int] = 20

class Solution(BaseModel):
    id: Optional[int] = None
    created_at: Optional[str] = None
    fitness_score: float
    distance_totale: float
    duree_totale: int
    minibus_utilises: int

@router.post("/api/optimize")
async def run_optimization(params: OptimizationParams):
    """
    Lance l'algorithme d'optimisation
    
    TODO: Intégrer l'algorithme métaheuristique existant
    Pour le moment, retourne une solution mock
    """
    try:
        logger.info(f"🚀 Lancement de l'optimisation avec {params.num_minibus} minibus")
        
        # Solution mock pour le moment
        mock_solution = {
            "minibus_1": {
                "itineraire": [
                    {
                        "station": "Depot Central",
                        "type": "DEPART",
                        "distance_depuis_precedent": 0,
                        "duree_depuis_precedent": 0,
                        "personnes_montantes": 0,
                        "personnes_descendantes": 0,
                        "passagers_a_bord": 0,
                        "capacite_restante": params.capacity,
                    }
                ],
                "stations_parcourues": ["Depot Central"],
                "distance_totale": 0,
                "duree_totale": 0,
                "capacite_minibus": params.capacity,
                "charge_maximale_atteinte": 0,
                "reservations_servies": [],
                "nombre_arrets": 1,
            }
        }
        
        logger.info("✅ Optimisation terminée")
        return mock_solution
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'optimisation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'optimisation: {str(e)}"
        )

@router.get("/api/solutions/latest")
async def get_latest_solution():
    """
    Récupère la dernière solution d'optimisation
    
    TODO: Récupérer depuis la table optimized_routes
    """
    try:
        # Solution mock pour le moment
        mock_solution = {
            "minibus_1": {
                "itineraire": [
                    {
                        "station": "Depot Central",
                        "type": "DEPART",
                        "distance_depuis_precedent": 0,
                        "duree_depuis_precedent": 0,
                        "personnes_montantes": 0,
                        "personnes_descendantes": 0,
                        "passagers_a_bord": 0,
                        "capacite_restante": 20,
                    },
                    {
                        "station": "Gueliz",
                        "type": "PICKUP",
                        "distance_depuis_precedent": 3.2,
                        "duree_depuis_precedent": 8,
                        "personnes_montantes": 3,
                        "personnes_descendantes": 0,
                        "passagers_a_bord": 3,
                        "capacite_restante": 17,
                    },
                ],
                "stations_parcourues": ["Depot Central", "Gueliz"],
                "distance_totale": 3.2,
                "duree_totale": 8,
                "capacite_minibus": 20,
                "charge_maximale_atteinte": 3,
                "reservations_servies": ["R1"],
                "nombre_arrets": 2,
            },
            "minibus_2": {
                "itineraire": [],
                "stations_parcourues": [],
                "distance_totale": 0,
                "duree_totale": 0,
                "capacite_minibus": 20,
                "charge_maximale_atteinte": 0,
                "reservations_servies": [],
                "nombre_arrets": 0,
            },
        }
        
        logger.info("✅ Dernière solution récupérée")
        return mock_solution
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la récupération de la solution: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la récupération de la solution"
        )

@router.get("/api/solutions", response_model=List[dict])
async def get_solutions():
    """
    Récupère l'historique des solutions d'optimisation
    
    TODO: Récupérer depuis la table optimized_routes
    """
    try:
        # Historique mock pour le moment
        mock_solutions = [
            {
                "id": 1,
                "created_at": datetime.now().isoformat(),
                "fitness_score": 28.1,
                "distance_totale": 28.1,
                "duree_totale": 75,
                "minibus_utilises": 2,
            },
            {
                "id": 2,
                "created_at": datetime.now().isoformat(),
                "fitness_score": 32.5,
                "distance_totale": 32.5,
                "duree_totale": 85,
                "minibus_utilises": 2,
            },
        ]
        
        logger.info(f"✅ Récupéré {len(mock_solutions)} solutions")
        return mock_solutions
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la récupération des solutions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la récupération des solutions"
        )
