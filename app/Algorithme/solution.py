# app/algorithms/solution.py

from typing import List, Dict, Optional
from dataclasses import dataclass, field
from copy import deepcopy
import copy
import random

@dataclass
class Arret:
    """Représente un arrêt dans l'itinéraire"""
    station_id: int
    station_name: str
    type: str  # "DEPOT", "PICKUP", "DROPOFF"
    reservation_id: Optional[int] = None
    personnes: int = 0
    distance_depuis_precedent: float = 0.0
    duree_depuis_precedent: float = 0.0
    passagers_a_bord: int = 0
    capacite_restante: int = 0

@dataclass
class ItineraireMinibus:
    """Représente l'itinéraire complet d'un minibus"""
    minibus_id: int
    capacite: int
    arrets: List[Arret] = field(default_factory=list)
    distance_totale: float = 0.0
    duree_totale: float = 0.0
    charge_maximale: int = 0
    reservations_servies: List[int] = field(default_factory=list)
    violations_capacite: int = 0

class Solution:
    """Représente une solution complète du problème VRP"""
    
    def __init__(self, minibus_list, reservations_list, stations_dict):
        self.minibus_list = minibus_list
        self.reservations_list = reservations_list
        self.stations_dict = stations_dict
        
        # Dictionnaire: minibus_id -> ItineraireMinibus
        self.itineraires: Dict[int, ItineraireMinibus] = {}
        
        # Initialiser les itinéraires vides
        for minibus in minibus_list:
            self.itineraires[minibus.id] = ItineraireMinibus(
                minibus_id=minibus.id,
                capacite=minibus.capacity
            )
        
        # Affectations: reservation_id -> minibus_id
        self.affectations: Dict[int, int] = {}
        
        # Métriques globales
        self.distance_totale_flotte: float = 0.0
        self.duree_totale_flotte: float = 0.0
        self.nombre_minibus_utilises: int = 0
        self.fitness: float = float('inf')
        self.violations_totales: int = 0
    
    def copy(self):
        nouvelle = Solution(
            self.minibus_list, 
            self.reservations_list, 
            self.stations_dict
        )
        
        # ✅ COPIE PROFONDE OBLIGATOIRE
        nouvelle.affectations = copy.deepcopy(self.affectations)
        nouvelle.itineraires = copy.deepcopy(self.itineraires)
        nouvelle.fitness = self.fitness
        nouvelle.distance_totale_flotte = self.distance_totale_flotte
        nouvelle.duree_totale_flotte = self.duree_totale_flotte
        
        return nouvelle
    
    def get_reservations_by_minibus(self, minibus_id: int) -> List:
        """Retourne les réservations assignées à un minibus"""
        reservation_ids = [rid for rid, mid in self.affectations.items() if mid == minibus_id]
        return [r for r in self.reservations_list if r.id in reservation_ids]
    
    def get_stations_parcourues(self, minibus_id: int) -> List[str]:
        """Retourne la liste des noms de stations parcourues"""
        return [arret.station_name for arret in self.itineraires[minibus_id].arrets]
    
    def to_dict(self) -> Dict:
        """Convertit la solution au format dictionnaire pour l'API"""
        result = {}
        
        for minibus_id, itineraire in self.itineraires.items():
            result[f"minibus_{minibus_id}"] = {
                "itineraire": [
                    {
                        "station": arret.station_name,
                        "type": arret.type,
                        "distance_depuis_precedent": round(arret.distance_depuis_precedent, 2),
                        "duree_depuis_precedent": round(arret.duree_depuis_precedent, 0),
                        "personnes_montantes": arret.personnes if arret.type == "PICKUP" else 0,
                        "personnes_descendantes": arret.personnes if arret.type == "DROPOFF" else 0,
                        "passagers_a_bord": arret.passagers_a_bord,
                        "capacite_restante": arret.capacite_restante
                    }
                    for arret in itineraire.arrets
                ],
                "stations_parcourues": self.get_stations_parcourues(minibus_id),
                "distance_totale": round(itineraire.distance_totale, 2),
                "duree_totale": round(itineraire.duree_totale, 0),
                "capacite_minibus": itineraire.capacite,
                "charge_maximale_atteinte": itineraire.charge_maximale,
                "reservations_servies": itineraire.reservations_servies,
                "nombre_arrets": len(itineraire.arrets)
            }
        
        result["METRIQUES_GLOBALES"] = {
            "distance_totale_flotte": round(self.distance_totale_flotte, 2),
            "duree_totale_flotte": round(self.duree_totale_flotte, 0),
            "nombre_minibus_utilises": self.nombre_minibus_utilises,
            "nombre_total_reservations": len(self.reservations_list),
            "reservations_satisfaites": len(self.affectations),
            "violations_capacite": self.violations_totales,
            "fitness_score": round(self.fitness, 2)
        }
        
        return result