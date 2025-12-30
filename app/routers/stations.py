# app/routers/stations.py
from fastapi import APIRouter, HTTPException
from app.database.crud import (
    get_all_stations, 
    create_station, 
    update_station, 
    delete_station
)
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/stations")
async def get_stations():
    """Récupère toutes les stations"""
    try:
        stations = get_all_stations()
        
        # Formater les données
        stations_list = []
        for (station_id, name, lat, lon) in stations:
            stations_list.append({
                "id": station_id,
                "name": name,
                "latitude": lat,
                "longitude": lon
            })
        
        logger.info(f"✅ Récupéré {len(stations_list)} stations")
        
        return {
            "success": True,
            "data": stations_list
        }
    except Exception as e:
        logger.error(f"❌ Erreur récupération stations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stations")
async def add_station(station_data: dict):
    """Crée une nouvelle station"""
    try:
        name = station_data.get("name")
        latitude = station_data.get("latitude")
        longitude = station_data.get("longitude")
        
        if not all([name, latitude, longitude]):
            raise HTTPException(status_code=400, detail="Données manquantes")
        
        station_id = create_station(name, latitude, longitude)
        
        return {
            "success": True,
            "data": {
                "id": station_id,
                "name": name,
                "latitude": latitude,
                "longitude": longitude
            }
        }
    except Exception as e:
        logger.error(f"❌ Erreur création station: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/stations/{station_id}")
async def modify_station(station_id: int, station_data: dict):
    """Met à jour une station"""
    try:
        name = station_data.get("name")
        latitude = station_data.get("latitude")
        longitude = station_data.get("longitude")
        
        update_station(station_id, name, latitude, longitude)
        
        return {
            "success": True,
            "message": "Station mise à jour"
        }
    except Exception as e:
        logger.error(f"❌ Erreur mise à jour station: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/stations/{station_id}")
async def remove_station(station_id: int):
    """Supprime une station"""
    try:
        delete_station(station_id)
        
        return {
            "success": True,
            "message": "Station supprimée"
        }
    except Exception as e:
        logger.error(f"❌ Erreur suppression station: {e}")
        raise HTTPException(status_code=500, detail=str(e))