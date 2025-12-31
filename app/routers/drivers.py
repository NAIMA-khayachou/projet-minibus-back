from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from ..database import crud
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Modèles Pydantic
class DriverBase(BaseModel):
    nom: str
    prenom: str
    telephone: Optional[str] = None
    email: Optional[EmailStr] = None
    status: str = "active"

class DriverCreate(DriverBase):
    pass

class DriverUpdate(DriverBase):
    pass

class Driver(DriverBase):
    id: int
    
    class Config:
        from_attributes = True

@router.get("/api/drivers", response_model=List[dict])
async def get_drivers():
    """
    Récupère tous les chauffeurs depuis la base de données
    Note: Utilise la table clients pour le moment
    """
    try:
        clients_data = crud.get_all_clients()
        # Convertir les clients en format chauffeurs
        drivers = [
            {
                "id": client[0],
                "nom": client[2],  # last_name
                "prenom": client[1],  # first_name
                "email": client[3],
                "telephone": client[4],
                "status": client[5] if len(client) > 5 else "active"
            }
            for client in clients_data
        ]
        logger.info(f"✅ Récupéré {len(drivers)} chauffeurs")
        return drivers
    except Exception as e:
        logger.error(f"❌ Erreur lors de la récupération des chauffeurs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la récupération des chauffeurs"
        )

@router.post("/api/drivers", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_driver(driver: DriverCreate):
    """Crée un nouveau chauffeur"""
    try:
        # Utilise create_client pour le moment
        driver_id = crud.create_client(
            first_name=driver.prenom,
            last_name=driver.nom,
            email=driver.email,
            phone=driver.telephone,
            status=driver.status
        )
        
        if driver_id:
            logger.info(f"✅ Chauffeur créé avec ID: {driver_id}")
            return {
                "id": driver_id,
                "nom": driver.nom,
                "prenom": driver.prenom,
                "email": driver.email,
                "telephone": driver.telephone,
                "status": driver.status
            }
        else:
            raise Exception("Échec de la création du chauffeur")
    except Exception as e:
        logger.error(f"❌ Erreur lors de la création du chauffeur: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la création du chauffeur"
        )

@router.put("/api/drivers/{driver_id}", response_model=dict)
async def update_driver(driver_id: int, driver: DriverUpdate):
    """Met à jour un chauffeur existant"""
    try:
        success = crud.update_client(
            client_id=driver_id,
            first_name=driver.prenom,
            last_name=driver.nom,
            email=driver.email,
            phone=driver.telephone,
            status=driver.status
        )
        
        if success:
            logger.info(f"✅ Chauffeur {driver_id} mis à jour")
            return {
                "id": driver_id,
                "nom": driver.nom,
                "prenom": driver.prenom,
                "email": driver.email,
                "telephone": driver.telephone,
                "status": driver.status
            }
        else:
             raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chauffeur non trouvé"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur lors de la mise à jour du chauffeur: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la mise à jour du chauffeur"
        )

@router.delete("/api/drivers/{driver_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_driver(driver_id: int):
    """Supprime un chauffeur"""
    try:
        success = crud.delete_client(driver_id)
        if success:
            logger.info(f"✅ Chauffeur {driver_id} supprimé")
            return None
        else:
             raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chauffeur non trouvé"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur lors de la suppression du chauffeur: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la suppression du chauffeur"
        )
