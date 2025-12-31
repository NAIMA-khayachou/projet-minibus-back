# app/models/prediction.py
"""Modèles Pydantic pour les requêtes/réponses de prédiction"""

from pydantic import BaseModel, Field
from typing import List, Optional


class PredictionRequest(BaseModel):
    """Modèle pour la requête de prédiction minibus"""
    
    hour_of_day: int = Field(..., ge=0, le=23, description="Heure du jour (0-23)")
    day_of_week: str = Field(..., description="Jour de la semaine (Monday, Tuesday, etc.)")
    passenger_count: int = Field(..., ge=1, le=30, description="Nombre de passagers (1-30)")
    from_station_id: int = Field(..., description="ID de la station de départ")
    to_station_id: int = Field(..., description="ID de la station d'arrivée")
    
    class Config:
        schema_extra = {
            "example": {
                "hour_of_day": 14,
                "day_of_week": "Monday",
                "passenger_count": 5,
                "from_station_id": 1,
                "to_station_id": 7
            }
        }


class MinibusOption(BaseModel):
    """Modèle pour une option minibus dans la réponse"""
    
    id: int
    license_plate: str
    capacity: int
    current_passengers: int
    available_seats: int
    score: float = Field(..., description="Score de pertinence (0-1)")


class PredictionResponse(BaseModel):
    """Modèle pour la réponse de prédiction"""
    
    success: bool
    message: str
    predicted_minibus: List[MinibusOption]
    total_options: int
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "2 minibus convenables trouvés",
                "predicted_minibus": [
                    {
                        "id": 1,
                        "license_plate": "M-1234-AB",
                        "capacity": 20,
                        "current_passengers": 5,
                        "available_seats": 15,
                        "score": 0.95
                    }
                ],
                "total_options": 1
            }
        }
