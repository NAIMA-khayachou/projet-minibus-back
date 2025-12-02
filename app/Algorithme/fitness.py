# app/algorithms/fitness.py - VERSION CORRIGÉE AVEC OSRM

from typing import List, Dict, Optional, Tuple
from .solution import Solution
import logging

logger = logging.getLogger(__name__)

class FitnessCalculator:
    """Calcule le fitness d'une solution avec support OSRM"""
    
    def __init__(self, matrice_distances, matrice_durees, stations_dict, use_osrm=True):
        """
        Args:
            matrice_distances: Si use_osrm=True → distances en MÈTRES
                              Si use_osrm=False → distances en KM (haversine)
            matrice_durees: Si use_osrm=True → durées en SECONDES
                           Si use_osrm=False → durées en MINUTES (estimées)
            stations_dict: Dict des stations
            use_osrm: True si matrices viennent d'OSRM, False si haversine
        """
        self.matrice_distances = matrice_distances
        self.matrice_durees = matrice_durees
        self.stations_dict = stations_dict
        self.use_osrm = use_osrm
        
        # ✅ Construction du mapping
        self.station_ids_order = sorted(stations_dict.keys())
        self.station_id_to_index = {
            sid: idx for idx, sid in enumerate(self.station_ids_order)
        }
        
        # Poids des pénalités
        self.PENALITE_CAPACITE = 10000
        self.PENALITE_RESERVATION_NON_SERVIE = 50000
        self.PENALITE_ORDRE_INVALIDE = 100000
        
        logger.info(f"✅ FitnessCalculator initialisé (OSRM={use_osrm})")
    
    def calculer_fitness(self, solution: Solution) -> Tuple[float, Dict]:
        """
        Calcule le fitness de la solution
        
        Retourne: (fitness, details)
        """
        distance_totale = 0.0
        duree_totale = 0.0
        violations_capacite = 0
        violations_ordre = 0
        minibus_utilises = 0
        
        for minibus_id, itineraire in solution.itineraires.items():
            if len(itineraire.arrets) <= 2:  # Seulement depot départ/retour
                continue
            
            minibus_utilises += 1
            
            # Trouver la capacité du minibus
            minibus_obj = next((m for m in solution.minibus_list if m.id == minibus_id), None)
            capacite = minibus_obj.capacity if minibus_obj else 20
            
            # ✅ CORRECTION: Passer la capacité correctement
            dist, duree, charge_max, violations_cap, violations_ord = self._evaluer_itineraire(
                itineraire,
                capacite
            )
            
            distance_totale += dist
            duree_totale += duree
            violations_capacite += violations_cap
            violations_ordre += violations_ord
            
            # Mettre à jour l'itinéraire
            itineraire.distance_totale = dist
            itineraire.duree_totale = duree
            itineraire.charge_maximale = charge_max
            itineraire.violations_capacite = violations_cap
        
        # Vérifier que toutes les réservations sont servies
        reservations_servies = len(solution.affectations)
        total_reservations = len(solution.reservations_list)
        reservations_non_servies = total_reservations - reservations_servies
        
        # Calcul du fitness
        fitness = distance_totale
        fitness += violations_capacite * self.PENALITE_CAPACITE
        fitness += reservations_non_servies * self.PENALITE_RESERVATION_NON_SERVIE
        fitness += violations_ordre * self.PENALITE_ORDRE_INVALIDE
        
        # Mettre à jour la solution
        solution.distance_totale_flotte = distance_totale
        solution.duree_totale_flotte = duree_totale
        solution.nombre_minibus_utilises = minibus_utilises
        solution.fitness = fitness
        solution.violations_totales = violations_capacite + violations_ordre
        
        details = {
            "distance_totale": distance_totale,
            "duree_totale": duree_totale,
            "violations_capacite": violations_capacite,
            "violations_ordre": violations_ordre,
            "reservations_non_servies": reservations_non_servies,
            "minibus_utilises": minibus_utilises
        }
        
        return fitness, details
    
    def _evaluer_itineraire(self, itineraire, capacite: int) -> Tuple[float, float, int, int, int]:
        """
        ✅ VERSION CORRIGÉE: Évalue un itinéraire avec gestion OSRM/Haversine
        
        Retourne: (distance_km, duree_min, charge_max, violations_capacite, violations_ordre)
        """
        distance_totale = 0.0  # En MÈTRES si OSRM, en KM si haversine
        duree_totale = 0.0     # En SECONDES si OSRM, en MINUTES si haversine
        charge_actuelle = 0
        charge_max = 0
        violations_capacite = 0
        violations_ordre = 0
        
        # Vérifier l'ordre pickup-dropoff
        pickups_vus = set()
        
        for i in range(len(itineraire.arrets)):
            arret = itineraire.arrets[i]
            
            # Calculer distance et durée depuis l'arrêt précédent
            if i > 0:
                arret_precedent = itineraire.arrets[i-1]
                
                idx_precedent = self.station_id_to_index.get(arret_precedent.station_id)
                idx_courant = self.station_id_to_index.get(arret.station_id)
                
                if idx_precedent is None or idx_courant is None:
                    logger.warning(f"⚠️ Index invalide: {arret_precedent.station_id} → {arret.station_id}")
                    dist = 0
                    duree = 0
                else:
                    # ✅ RÉCUPÉRATION DES DONNÉES BRUTES
                    dist = self.matrice_distances[idx_precedent][idx_courant]
                    duree = self.matrice_durees[idx_precedent][idx_courant]
                    
                    # ✅ VÉRIFICATION DE COHÉRENCE
                    if dist < 0.01 and idx_precedent != idx_courant:
                        logger.warning(
                            f"⚠️ Distance suspecte: {arret_precedent.station_name} → {arret.station_name} = {dist}"
                        )
                
                # Accumuler
                distance_totale += dist
                duree_totale += duree
                
                # ✅ STOCKER DANS L'ARRÊT (AVEC CONVERSION SI OSRM)
                if self.use_osrm:
                    arret.distance_depuis_precedent = dist / 1000  # Mètres → Km
                    arret.duree_depuis_precedent = duree / 60      # Secondes → Minutes
                else:
                    arret.distance_depuis_precedent = dist  # Déjà en km
                    arret.duree_depuis_precedent = duree   # Déjà en minutes
            
            # Gérer les passagers
            if arret.type == "PICKUP":
                charge_actuelle += arret.personnes
                pickups_vus.add(arret.reservation_id)
                
                if charge_actuelle > capacite:
                    violations_capacite += 1
                    logger.warning(f"⚠️ Surcharge: {charge_actuelle}/{capacite} à l'arrêt {arret.station_name}")
            
            elif arret.type == "DROPOFF":
                # Vérifier que le pickup a été fait avant
                if arret.reservation_id not in pickups_vus:
                    violations_ordre += 1
                    logger.warning(f"⚠️ DROPOFF avant PICKUP pour réservation {arret.reservation_id}")
                
                charge_actuelle -= arret.personnes
            
            # Enregistrer l'état
            arret.passagers_a_bord = charge_actuelle
            arret.capacite_restante = capacite - charge_actuelle
            charge_max = max(charge_max, charge_actuelle)
        
        # ✅ CONVERSION FINALE SELON LE FORMAT DES MATRICES
        if self.use_osrm:
            # OSRM retourne mètres et secondes
            distance_km = distance_totale / 1000
            duree_min = duree_totale / 60
        else:
            # Haversine retourne déjà km et minutes
            distance_km = distance_totale
            duree_min = duree_totale
        
        return distance_km, duree_min, charge_max, violations_capacite, violations_ordre