from fastapi import APIRouter
from app.database import crud

router = APIRouter()

@router.get("/buses", tags=["Buses"])
def get_buses():
    """
    Endpoint pour récupérer la liste des minibus depuis la base de données.
    """
    buses = crud.get_all_minibus()
    formatted_buses = [
        {
            "id": b[0],
            "capacity": b[1],
            "license_plate": b[2],
            "current_passengers": b[3],
            "status": b[4],
            "last_maintenance": b[5]
        }
        for b in buses
    ]
    return {"buses": formatted_buses}
