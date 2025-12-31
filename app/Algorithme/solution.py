from typing import List, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import copy

@dataclass
class Arret:
    """Représente un arrêt dans l'itinéraire (peut combiner pickup ET dropoff)"""
    station_id: int
    station_name: str
    type: str  # "DEPOT" ou "STOP"
    heure_arrivee: Optional[datetime] = None
    
    # ✅ NOUVEAU: Listes des réservations à gérer à cet arrêt
    pickups: List[int] = field(default_factory=list)  # reservation_ids à prendre
    dropoffs: List[int] = field(default_factory=list)  # reservation_ids à déposer
    
    # Totaux de personnes
    personnes_montantes: int = 0
    personnes_descendantes: int = 0
    
    # Métriques de distance
    distance_depuis_precedent: float = 0.0
    duree_depuis_precedent: float = 0.0
    passagers_a_bord: int = 0
    capacite_restante: int = 0
    
    def ajouter_pickup(self, reservation_id: int, nb_personnes: int):
        """Ajoute un pickup à cet arrêt"""
        if reservation_id not in self.pickups:
            self.pickups.append(reservation_id)
            self.personnes_montantes += nb_personnes
    
    def ajouter_dropoff(self, reservation_id: int, nb_personnes: int):
        """Ajoute un dropoff à cet arrêt"""
        if reservation_id not in self.dropoffs:
            self.dropoffs.append(reservation_id)
            self.personnes_descendantes += nb_personnes
    
    def has_action(self) -> bool:
        """Vérifie si l'arrêt a au moins une action (pickup ou dropoff)"""
        return len(self.pickups) > 0 or len(self.dropoffs) > 0

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
    violations_horaire: int = 0
    
    def peut_ajouter_reservation(self, reservation) -> bool:
        """
        ✅ Vérifie si une réservation peut être ajoutée à cet itinéraire
        (si la route passe déjà par la station pickup)
        """
        for arret in self.arrets:
            if arret.station_id == reservation.pickup_station_id:
                return True
        return False
    
    def get_arret_by_station(self, station_id: int) -> Optional[Arret]:
        """Retourne l'arrêt correspondant à une station (ou None)"""
        for arret in self.arrets:
            if arret.station_id == station_id:
                return arret
        return None

class Solution:
    """Solution complète du VRP avec contraintes horaires"""
    
    def __init__(self, minibus_list, reservations_list, stations_dict):
        """
        Args:
            minibus_list: Liste d'objets Bus (SQLAlchemy)
            reservations_list: Liste d'objets Reservation (SQLAlchemy)
            stations_dict: Dict {station_id: Station object}
        """
        self.minibus_list = minibus_list
        self.reservations_list = reservations_list
        self.stations_dict = stations_dict
        
        # Créer un dict pour accès rapide aux réservations
        self.reservations_by_id = {r.id: r for r in reservations_list}
        
        # Itinéraires: {minibus_id -> ItineraireMinibus}
        self.itineraires: Dict[int, ItineraireMinibus] = {}
        
        # Initialiser les itinéraires vides
        for minibus in minibus_list:
            self.itineraires[minibus.id] = ItineraireMinibus(
                minibus_id=minibus.id,
                capacite=minibus.capacity
            )
        
        # Affectations: {reservation_id -> minibus_id}
        self.affectations: Dict[int, int] = {}
        
        # Métriques globales
        self.distance_totale_flotte: float = 0.0
        self.duree_totale_flotte: float = 0.0
        self.nombre_minibus_utilises: int = 0
        self.fitness: float = float('inf')
        self.violations_totales: int = 0
        self.retard_total: float = 0.0
    
    def copy(self):
        """Copie profonde de la solution"""
        nouvelle = Solution(
            self.minibus_list, 
            self.reservations_list, 
            self.stations_dict
        )
        
        nouvelle.affectations = copy.deepcopy(self.affectations)
        nouvelle.itineraires = copy.deepcopy(self.itineraires)
        nouvelle.fitness = self.fitness
        nouvelle.distance_totale_flotte = self.distance_totale_flotte
        nouvelle.duree_totale_flotte = self.duree_totale_flotte
        nouvelle.retard_total = self.retard_total
        nouvelle.violations_totales = self.violations_totales
        
        return nouvelle
    
    def get_reservations_by_minibus(self, minibus_id: int) -> List:
        """Retourne les réservations assignées à un minibus"""
        reservation_ids = [rid for rid, mid in self.affectations.items() 
                          if mid == minibus_id]
        return [self.reservations_by_id[rid] for rid in reservation_ids 
                if rid in self.reservations_by_id]
    
    def get_stations_parcourues(self, minibus_id: int) -> List[str]:
        """Retourne la liste des noms de stations parcourues"""
        return [arret.station_name for arret in self.itineraires[minibus_id].arrets]
    
    def trouver_minibus_compatible(self, reservation) -> Optional[int]:
        """
        ✅ MÉTHODE CLÉ: Trouve un minibus dont la route passe déjà 
        par la station pickup de la réservation
        """
        for minibus_id, itineraire in self.itineraires.items():
            # Vérifier si la route passe par la station pickup
            if itineraire.peut_ajouter_reservation(reservation):
                # Vérifier la capacité disponible
                minibus = next((m for m in self.minibus_list if m.id == minibus_id), None)
                if minibus:
                    capacite_necessaire = reservation.number_of_people
                    capacite_disponible = minibus.capacity - itineraire.charge_maximale
                    
                    if capacite_disponible >= capacite_necessaire:
                        return minibus_id
        
        return None
    
    def to_dict(self) -> Dict:
        """Convertit la solution au format dictionnaire pour l'API"""
        result = {}
        
        for minibus_id, itineraire in self.itineraires.items():
            # Trouver le minibus correspondant
            minibus = next((m for m in self.minibus_list if m.id == minibus_id), None)
            
            result[f"minibus_{minibus_id}"] = {
                "license_plate": minibus.license_plate if minibus else "N/A",
                "itineraire": [
                    {
                        "station": arret.station_name,
                        "station_id": arret.station_id,
                        "type": arret.type,
                        "heure_arrivee": arret.heure_arrivee.isoformat() if arret.heure_arrivee else None,
                        "pickups": arret.pickups,
                        "dropoffs": arret.dropoffs,
                        "distance_depuis_precedent": round(arret.distance_depuis_precedent, 2),
                        "duree_depuis_precedent": round(arret.duree_depuis_precedent, 0),
                        "personnes_montantes": arret.personnes_montantes,
                        "personnes_descendantes": arret.personnes_descendantes,
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
                "nombre_arrets": len(itineraire.arrets),
                "violations_horaire": itineraire.violations_horaire
            }
        
        result["METRIQUES_GLOBALES"] = {
            "distance_totale_flotte": round(self.distance_totale_flotte, 2),
            "duree_totale_flotte": round(self.duree_totale_flotte, 0),
            "nombre_minibus_utilises": self.nombre_minibus_utilises,
            "nombre_total_reservations": len(self.reservations_list),
            "reservations_satisfaites": len(self.affectations),
            "violations_capacite": self.violations_totales,
            "retard_total_minutes": round(self.retard_total, 2),
            "fitness_score": round(self.fitness, 2)
        }
        
        return result
    
    def to_route_solution(self, minibus_id: int):
        """
        ✅ Convertit un itinéraire au format RouteSolution (compatible avec vos modèles)
        """
        from models.route import RouteSolution
        
        itineraire = self.itineraires[minibus_id]
        minibus = next((m for m in self.minibus_list if m.id == minibus_id), None)
        
        if not minibus or len(itineraire.arrets) <= 2:
            return None
        
        # Construire la séquence de stations au format attendu
        station_sequence = []
        for arret in itineraire.arrets:
            if arret.type == "DEPOT":
                station_sequence.append({
                    'station_id': arret.station_id,
                    'station_name': arret.station_name,
                    'action': 'depot',
                    'time': arret.heure_arrivee.isoformat() if arret.heure_arrivee else None
                })
            else:
                # Ajouter les pickups
                for res_id in arret.pickups:
                    reservation = self.reservations_by_id.get(res_id)
                    if reservation:
                        station_sequence.append({
                            'station_id': arret.station_id,
                            'station_name': arret.station_name,
                            'action': 'pickup',
                            'passengers': reservation.number_of_people,
                            'reservation_id': res_id,
                            'time': arret.heure_arrivee.isoformat() if arret.heure_arrivee else None
                        })
                
                # Ajouter les dropoffs
                for res_id in arret.dropoffs:
                    reservation = self.reservations_by_id.get(res_id)
                    if reservation:
                        station_sequence.append({
                            'station_id': arret.station_id,
                            'station_name': arret.station_name,
                            'action': 'dropoff',
                            'passengers': reservation.number_of_people,
                            'reservation_id': res_id,
                            'time': arret.heure_arrivee.isoformat() if arret.heure_arrivee else None
                        })
        
        route_solution = RouteSolution(
            bus=minibus,
            station_sequence=station_sequence,
            total_distance=itineraire.distance_totale
        )
        
        route_solution.total_passengers = itineraire.charge_maximale
        route_solution.fitness_score = self.fitness
        
        return route_solution