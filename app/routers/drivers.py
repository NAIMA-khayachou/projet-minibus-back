# app/routers/drivers.py
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from ..database import crud
import logging
import traceback

logger = logging.getLogger(__name__)

router = APIRouter()

# Modèles Pydantic
class DriverBase(BaseModel):
    nom: str
    prenom: str
    telephone: Optional[str] = None
    email: EmailStr  # Email est obligatoire
    status: str = "active"

class DriverCreate(DriverBase):
    pass

class DriverUpdate(DriverBase):
    pass

# ==================== ROUTES CRUD ====================

@router.get("/drivers", response_model=List[dict])
async def get_drivers():
    """Récupère tous les chauffeurs"""
    try:
        chauffeurs_data = crud.get_users_by_role('chauffeur')
        
        drivers = [
            {
                "id": user[0],
                "email": user[1] if user[1] else "",
                "nom": user[4] if len(user) > 4 else "",
                "prenom": user[5] if len(user) > 5 else "",
                "telephone": "N/A",
                "status": "active"
            }
            for user in chauffeurs_data
        ]
        
        logger.info(f"✅ Récupéré {len(drivers)} chauffeurs")
        return drivers
    except Exception as e:
        logger.error(f"❌ Erreur get_drivers: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur: {str(e)}"
        )

@router.get("/drivers/{driver_id}", response_model=dict)
async def get_driver(driver_id: int):
    """Récupère un chauffeur par son ID"""
    try:
        chauffeurs = crud.get_users_by_role('chauffeur')
        driver = next((d for d in chauffeurs if d[0] == driver_id), None)
        
        if not driver:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chauffeur non trouvé"
            )
        
        return {
            "id": driver[0],
            "email": driver[1],
            "nom": driver[4],
            "prenom": driver[5],
            "telephone": "N/A",
            "status": "active"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur get_driver: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/drivers", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_driver(driver: DriverCreate):
    """Crée un nouveau chauffeur"""
    try:
        logger.info(f"🔵 Tentative de création chauffeur: {driver.prenom} {driver.nom} ({driver.email})")
        
        # Vérifier si l'email existe déjà
        try:
            existing_user = crud.get_user_by_email(driver.email)
            if existing_user:
                logger.warning(f"⚠️ Email déjà existant: {driver.email}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Un utilisateur avec cet email existe déjà"
                )
        except Exception as check_error:
            logger.info(f"Email {driver.email} disponible")
        
        # Importer la fonction de hashage
        try:
            from .auth import get_password_hash
            logger.info("✅ Fonction get_password_hash importée")
        except ImportError as import_error:
            logger.error(f"❌ Impossible d'importer get_password_hash: {import_error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erreur d'importation de la fonction de hashage"
            )
        
        # Créer le mot de passe hashé
        try:
            hashed_password = get_password_hash("chauffeur123")
            logger.info("✅ Mot de passe hashé créé")
        except Exception as hash_error:
            logger.error(f"❌ Erreur lors du hashage: {hash_error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erreur de hashage: {str(hash_error)}"
            )
        
        # Créer l'utilisateur
        try:
            user_id = crud.create_user(
                email=driver.email,
                password=hashed_password,
                role="chauffeur",
                nom=driver.nom,
                prenom=driver.prenom
            )
            logger.info(f"✅ create_user appelé, résultat: {user_id}")
        except Exception as create_error:
            logger.error(f"❌ Erreur crud.create_user: {create_error}")
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erreur de création dans la base: {str(create_error)}"
            )
        
        if user_id:
            logger.info(f"✅ Chauffeur créé avec succès (ID: {user_id})")
            return {
                "id": user_id,
                "nom": driver.nom,
                "prenom": driver.prenom,
                "email": driver.email,
                "telephone": driver.telephone if driver.telephone else "N/A",
                "status": driver.status
            }
        else:
            logger.error("❌ create_user a retourné None")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Échec de la création (ID null)"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur create_driver: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur inattendue: {str(e)}"
        )

@router.put("/drivers/{driver_id}", response_model=dict)
async def update_driver(driver_id: int, driver: DriverUpdate):
    """Met à jour un chauffeur"""
    try:
        logger.info(f"🔵 Mise à jour chauffeur ID: {driver_id}")
        
        success = crud.update_user(
            user_id=driver_id,
            email=driver.email,
            role="chauffeur",
            nom=driver.nom,
            prenom=driver.prenom
        )
        
        if success:
            logger.info(f"✅ Chauffeur {driver_id} mis à jour")
            return {
                "id": driver_id,
                "nom": driver.nom,
                "prenom": driver.prenom,
                "email": driver.email,
                "telephone": driver.telephone if driver.telephone else "N/A",
                "status": driver.status
            }
        else:
            logger.warning(f"⚠️ Chauffeur {driver_id} non trouvé")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chauffeur non trouvé"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur update_driver: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur: {str(e)}"
        )

@router.delete("/drivers/{driver_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_driver(driver_id: int):
    """Supprime un chauffeur"""
    try:
        logger.info(f"🔵 Suppression chauffeur ID: {driver_id}")
        
        success = crud.delete_user(driver_id)
        if success:
            logger.info(f"✅ Chauffeur {driver_id} supprimé")
            return None
        else:
            logger.warning(f"⚠️ Chauffeur {driver_id} non trouvé")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chauffeur non trouvé"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur delete_driver: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur: {str(e)}"
        )