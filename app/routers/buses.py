from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from ..database import crud
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Modèles Pydantic
class BusBase(BaseModel):
    capacity: int
    license_plate: str
    status: Optional[str] = "available"

class BusCreate(BusBase):
    pass

class BusUpdate(BusBase):
    pass

class Bus(BusBase):
    id: int
    current_passengers: int
    last_maintenance: Optional[str] = None
    
    class Config:
        from_attributes = True

@router.get("/minibus", response_model=List[dict])
async def get_minibus():
    """Récupère tous les minibus"""
    try:
        minibus_data = crud.get_all_minibus()
        # Convertir les objets Bus en dictionnaires
        buses = [bus.to_dict() for bus in minibus_data]
        logger.info(f"✅ Récupéré {len(buses)} minibus")
        return buses
    except Exception as e:
        logger.error(f"❌ Erreur lors de la récupération des minibus: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la récupération des minibus"
        )

@router.post("/minibus", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_minibus(bus: BusCreate):
    """Crée un nouveau minibus"""
    try:
        bus_id = crud.create_minibus(
            capacity=bus.capacity,
            license_plate=bus.license_plate
        )
        
        if bus_id:
            return {
                "id": bus_id,
                "capacity": bus.capacity,
                "license_plate": bus.license_plate,
                "status": "available",
                "current_passengers": 0
            }
        else:
            raise Exception("Échec de la création du minibus")
    except Exception as e:
        logger.error(f"❌ Erreur lors de la création du minibus: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la création du minibus"
        )

@router.put("/minibus/{bus_id}", response_model=dict)
async def update_minibus(bus_id: int, bus: BusUpdate):
    """Met à jour un minibus existant"""
    try:
        success = crud.update_minibus(
            minibus_id=bus_id,
            capacity=bus.capacity,
            license_plate=bus.license_plate,
            status=bus.status
        )
        
        if success:
            return {
                "id": bus_id,
                "capacity": bus.capacity,
                "license_plate": bus.license_plate,
                "status": bus.status
            }
        else:
             raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Minibus non trouvé"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur lors de la mise à jour du minibus: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la mise à jour du minibus"
        )

@router.delete("/minibus/{bus_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_minibus(bus_id: int):
    """Supprime un minibus"""
    try:
        success = crud.delete_minibus(bus_id)
        if success:
            return None
        else:
             raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Minibus non trouvé"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur lors de la suppression du minibus: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la suppression du minibus"
        )
