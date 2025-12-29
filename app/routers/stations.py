from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import List
from ..database import crud
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Modèles Pydantic
class StationBase(BaseModel):
    name: str
    latitude: float
    longitude: float

class StationCreate(StationBase):
    pass

class StationUpdate(StationBase):
    pass

class Station(StationBase):
    id: int
    
    class Config:
        from_attributes = True

@router.get("/api/stations", response_model=List[dict])
async def get_stations():
    """Récupère toutes les stations depuis la base de données"""
    try:
        stations_data = crud.get_all_stations()
        # Convertir les tuples en dictionnaires
        stations = [
            {
                "id": station[0],
                "name": station[1],
                "latitude": station[2],
                "longitude": station[3]
            }
            for station in stations_data
        ]
        logger.info(f"✅ Récupéré {len(stations)} stations")
        return stations
    except Exception as e:
        logger.error(f"❌ Erreur lors de la récupération des stations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la récupération des stations"
        )

@router.post("/api/stations", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_station(station: StationCreate):
    """Crée une nouvelle station"""
    try:
        station_id = crud.create_station(
            name=station.name,
            latitude=station.latitude,
            longitude=station.longitude
        )
        
        if station_id:
            logger.info(f"✅ Station créée: {station.name}")
            return {
                "id": station_id,
                "name": station.name,
                "latitude": station.latitude,
                "longitude": station.longitude
            }
        else:
             raise Exception("Échec de l'insertion en base de données")
    except Exception as e:
        logger.error(f"❌ Erreur lors de la création de la station: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la création de la station"
        )

@router.put("/api/stations/{station_id}", response_model=dict)
async def update_station(station_id: int, station: StationUpdate):
    """Met à jour une station existante"""
    try:
        success = crud.update_station(
            station_id=station_id,
            name=station.name,
            latitude=station.latitude,
            longitude=station.longitude
        )
        
        if success:
            logger.info(f"✅ Station {station_id} mise à jour")
            return {
                "id": station_id,
                "name": station.name,
                "latitude": station.latitude,
                "longitude": station.longitude
            }
        else:
             raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Station non trouvée"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur lors de la mise à jour de la station: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la mise à jour de la station"
        )

@router.delete("/api/stations/{station_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_station(station_id: int):
    """Supprime une station"""
    try:
        success = crud.delete_station(station_id)
        if success:
            logger.info(f"✅ Station {station_id} supprimée")
            return None
        else:
             raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Station non trouvée"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur lors de la suppression de la station: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la suppression de la station"
        )
