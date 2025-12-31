from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from datetime import time, datetime, timedelta


@dataclass
class Reservation:
    """Modèle pour une réservation"""
    id: int
    client_name: str
    pickup_station_id: int
    dropoff_station_id: int
    number_of_people: int
    desired_time: datetime  # ✅ Heure souhaitée d'arrivée au pickup
    status: str = "pending"
    desired_time: time 
    
    def __post_init__(self):
        """Convertit desired_time en datetime si c'est une string"""
        if isinstance(self.desired_time, str):
            self.desired_time = datetime.fromisoformat(self.desired_time.replace('Z', '+00:00'))
    
    def est_en_retard(self, heure_arrivee: datetime, tolerance_minutes: int = 5) -> bool:
        """
        Vérifie si l'arrivée du minibus est en retard par rapport à l'heure souhaitée
        
        Args:
            heure_arrivee: Heure d'arrivée effective du minibus
            tolerance_minutes: Tolérance en minutes (défaut 5 min)
        """
        if heure_arrivee is None:
            return False
        
        difference = (heure_arrivee - self.desired_time).total_seconds() / 60
        return difference > tolerance_minutes
    
    def calculer_retard(self, heure_arrivee: datetime) -> float:
        """
        Calcule le retard en minutes (0 si en avance ou à l'heure)
        """
        if heure_arrivee is None:
            return 0.0
        
        difference = (heure_arrivee - self.desired_time).total_seconds() / 60
        return max(0, difference)