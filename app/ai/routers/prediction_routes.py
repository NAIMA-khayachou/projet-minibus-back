from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from app.ai.Services.ai_service import AIService

predict_router = APIRouter()
ai_service = AIService()


class PredictionRequest(BaseModel):
    """
    Request model for ETA prediction.
    
    Note: hour_of_day and day_of_week are optional because 
    the AI service calculates them automatically if not provided.
    """
    from_station_id: int = Field(..., alias="pickup_station_id", ge=1, le=10)
    to_station_id: int = Field(..., alias="dropoff_station_id", ge=1, le=10)
    passenger_count: int = Field(..., alias="number_of_people", ge=1, le=100)
    departure_time: Optional[str] = Field(None, description="Format ISO: 2025-01-15T14:30:00")
    
    class Config:
        populate_by_name = True  # Permet d'utiliser les alias ou noms originaux


class PredictionResponse(BaseModel):
    """Response model for ETA prediction."""
    predicted_duration_minutes: float
    distance_km: float
    is_night: bool
    from_station: str
    to_station: str
    hour_of_day: int
    day_of_week: int


@predict_router.post("/predict-travel", response_model=PredictionResponse)
async def get_prediction(data: PredictionRequest):
    """
    Predict tramway travel duration between two stations.
    
    Args:
        data: Prediction request with station IDs and passenger count
    
    Returns:
        Prediction with ETA, distance, and journey details
    
    Raises:
        HTTPException: If prediction fails or station IDs are invalid
    """
    try:
        # Validation: cannot travel to same station
        if data.from_station_id == data.to_station_id:
            raise HTTPException(
                status_code=400,
                detail="Les stations de départ et d'arrivée doivent être différentes"
            )
        
        # Parse departure_time if provided
        departure_time = None
        if data.departure_time:
            try:
                departure_time = datetime.fromisoformat(data.departure_time)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Format de date invalide. Utilisez le format ISO: 2025-01-15T14:30:00"
                )
        
        # Call AI service
        result = ai_service.predict_eta(
            from_station_id=data.from_station_id,
            to_station_id=data.to_station_id,
            passenger_count=data.passenger_count,
            departure_time=departure_time
        )
        
        return PredictionResponse(
            predicted_duration_minutes=result['eta_minutes'],
            distance_km=result['distance_km'],
            is_night=result['is_night'],
            from_station=result['from_station'],
            to_station=result['to_station'],
            hour_of_day=result['hour_of_day'],
            day_of_week=result['day_of_week']
        )
    
    except ValueError as e:
        # Station not found or validation error
        raise HTTPException(status_code=400, detail=str(e))
    
    except RuntimeError as e:
        # Model not loaded
        raise HTTPException(status_code=503, detail=f"Service IA indisponible: {str(e)}")
    
    except Exception as e:
        # Unexpected error
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")


@predict_router.post("/predict-travel-batch")
async def get_batch_predictions(journeys: list[PredictionRequest]):
    """
    Predict ETA for multiple journeys at once.
    
    Args:
        journeys: List of prediction requests
    
    Returns:
        List of predictions or errors
    """
    try:
        # Convert requests to format expected by AI service
        journey_data = []
        for journey in journeys:
            departure_time = None
            if journey.departure_time:
                try:
                    departure_time = datetime.fromisoformat(journey.departure_time)
                except ValueError:
                    pass  # Will be handled by batch prediction
            
            journey_data.append({
                'from_station_id': journey.from_station_id,
                'to_station_id': journey.to_station_id,
                'passenger_count': journey.passenger_count,
                'departure_time': departure_time
            })
        
        # Call AI service batch prediction
        results = ai_service.predict_batch(journey_data)
        
        return {"predictions": results, "total": len(results)}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur batch prediction: {str(e)}")


@predict_router.get("/stations")
async def get_stations():
    """
    Get list of all available stations.
    
    Returns:
        Dictionary of station IDs and their information
    """
    try:
        stations = ai_service.get_all_stations()
        
        # Format for frontend
        stations_list = [
            {
                'id': station_id,
                'name': info['name'],
                'latitude': info['latitude'],
                'longitude': info['longitude']
            }
            for station_id, info in stations.items()
        ]
        
        return {"stations": stations_list, "total": len(stations_list)}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur récupération stations: {str(e)}")


@predict_router.get("/stations/{station_id}")
async def get_station_info(station_id: int):
    """
    Get information about a specific station.
    
    Args:
        station_id: Station ID (1-10 for Marrakech)
    
    Returns:
        Station information
    """
    try:
        station_info = ai_service.get_station_info(station_id)
        
        if station_info is None:
            raise HTTPException(
                status_code=404,
                detail=f"Station {station_id} non trouvée"
            )
        
        return {
            'id': station_id,
            'name': station_info['name'],
            'latitude': station_info['latitude'],
            'longitude': station_info['longitude']
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@predict_router.get("/health")
async def health_check():
    """
    Check if the AI service is healthy and ready.
    
    Returns:
        Health status of the service
    """
    try:
        stations_count = len(ai_service.get_all_stations())
        
        return {
            "status": "healthy",
            "model_loaded": ai_service.model is not None,
            "stations_loaded": stations_count,
            "service": "AI Prediction Service"
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Service unhealthy: {str(e)}"
        )