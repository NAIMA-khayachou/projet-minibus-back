# app/algorithms/fitness.py


from typing import List, Dict, Optional,Tuple
from .solution import Solution

class FitnessCalculator:
    """Calcule le fitness d'une solution"""
    
    def __init__(self, matrice_distances, matrice_durees, stations_dict):
        self.matrice_distances = matrice_distances
        self.matrice_durees = matrice_durees
        self.stations_dict = stations_dict
        
        # Poids des pénalités
        self.PENALITE_CAPACITE = 10000
        self.PENALITE_RESERVATION_NON_SERVIE = 50000
        self.PENALITE_ORDRE_INVALIDE = 100000
    
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
            
            # Calculer distance et durée pour ce minibus
            dist, duree, charge_max, violations_cap, violations_ord = self._evaluer_itineraire(
                itineraire,
                solution.itineraires[minibus_id].capacite
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
    
    def _evaluer_itineraire(self, itineraire, capacite) -> Tuple[float, float, int, int, int]:
        """
        Évalue un itinéraire et calcule ses métriques
        
        Retourne: (distance, duree, charge_max, violations_capacite, violations_ordre)
        """
        distance_totale = 0.0
        duree_totale = 0.0
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
                
                dist = self.matrice_distances[arret_precedent.station_id][arret.station_id]
                duree = self.matrice_durees[arret_precedent.station_id][arret.station_id]
                
                distance_totale += dist
                duree_totale += duree
                
                arret.distance_depuis_precedent = dist / 1000  # Convertir en km
                arret.duree_depuis_precedent = duree / 60  # Convertir en minutes
            
            # Gérer les passagers
            if arret.type == "PICKUP":
                charge_actuelle += arret.personnes
                pickups_vus.add(arret.reservation_id)
                
                if charge_actuelle > capacite:
                    violations_capacite += 1
            
            elif arret.type == "DROPOFF":
                # Vérifier que le pickup a été fait avant
                if arret.reservation_id not in pickups_vus:
                    violations_ordre += 1
                
                charge_actuelle -= arret.personnes
            
            # Enregistrer l'état
            arret.passagers_a_bord = charge_actuelle
            arret.capacite_restante = capacite - charge_actuelle
            charge_max = max(charge_max, charge_actuelle)
        
        return distance_totale / 1000, duree_totale / 60, charge_max, violations_capacite, violations_ordre