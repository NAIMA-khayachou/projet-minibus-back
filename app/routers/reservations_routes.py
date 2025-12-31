from fastapi import APIRouter, HTTPException, Body
from fastapi.responses import JSONResponse
from ..models.reservation import Reservation

router = APIRouter()

# Pour FastAPI, il est préférable d'utiliser Pydantic pour définir le corps de la requête
# Voici un exemple de modèle Pydantic, que vous devriez ajouter dans app/models/reservation.py
# class ReservationRequest(BaseModel):
#     first_name: str
#     last_name: str
#     email: str
#     phone: str | None = None  # Optionnel
#     pickup_station_id: int
#     dropoff_station_id: int
#     number_of_people: int
#     desired_time: str

@router.post("/reservations")
def create_new_reservation(data: dict = Body(...)):
    """
    Crée une nouvelle réservation et le client associé.
    """
    try:
        # Valider les champs requis
        required_fields = ['first_name', 'last_name', 'email', 'pickup_station_id', 
                           'dropoff_station_id', 'number_of_people', 'desired_time']
        for field in required_fields:
            if field not in data:
                return JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "message": f"Le champ '{field}' est obligatoire."
                    }
                )

        # Appeler le modèle pour créer la réservation
        reservation_id = Reservation.create(data)
        
        return JSONResponse(
            status_code=201,
            content={
                "success": True,
                "message": "Réservation créée avec succès.",
                "reservation_id": reservation_id
            }
        )

    except ValueError as ve:
        # ✅ Gestion des erreurs de validation métier (téléphone/email en conflit)
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "message": str(ve)  # Le message sera affiché tel quel sur le frontend
            }
        )

    except HTTPException:
        # Laisse passer les erreurs HTTP que nous avons levées
        raise
        
    except Exception as e:
        # ✅ Erreur serveur inattendue
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "Une erreur est survenue lors de la création de votre réservation. Veuillez réessayer."
            }
        )