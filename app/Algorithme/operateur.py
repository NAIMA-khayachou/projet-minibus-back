# app/algorithms/operators.py

import random
from typing import List, Tuple
from .solution import Solution, Arret

class GeneticOperators:
    """Opérateurs génétiques pour l'algorithme"""
    
    def __init__(self, matrice_distances,stations_dict):
        self.matrice_distances = matrice_distances
        self.stations_dict = stations_dict
        self.station_ids_order = sorted(stations_dict.keys())
        self.station_id_to_index = {
            sid: idx for idx, sid in enumerate(self.station_ids_order)
        }
    
    # ============= SÉLECTION =============
    
    def selection_tournoi(self, population: List[Solution], fitness_scores: List[float], 
                         taille_tournoi: int = 3) -> Solution:
        """Sélection par tournoi"""
        # Sélectionner aléatoirement des participants
        indices = random.sample(range(len(population)), min(taille_tournoi, len(population)))
        
        # Trouver le meilleur (fitness minimal)
        meilleur_idx = min(indices, key=lambda i: fitness_scores[i])
        
        return population[meilleur_idx].copy()
    
    # ============= CROISEMENT =============
    
    def croisement_ordonne(self, parent1: Solution, parent2: Solution, 
                          prob_croisement: float = 0.8) -> Tuple[Solution, Solution]:
        """
        Croisement ordonné (Order Crossover - OX)
        Préserve l'ordre relatif des réservations
        """
        if random.random() > prob_croisement:
            return parent1.copy(), parent2.copy()
        
        enfant1 = parent1.copy()
        enfant2 = parent2.copy()
        
        # Réinitialiser les affectations
        enfant1.affectations = {}
        enfant2.affectations = {}
        
        # Obtenir la liste des réservations
        reservations = list(parent1.reservations_list)
        n = len(reservations)
        
        if n < 2:
            return enfant1, enfant2
        
        # Sélectionner deux points de coupure
        point1, point2 = sorted(random.sample(range(n), 2))
        
        # Créer les affectations pour enfant1
        # Copier le segment du parent1
        segment_parent1 = {}
        for i in range(point1, point2):
            res_id = reservations[i].id
            if res_id in parent1.affectations:
                segment_parent1[res_id] = parent1.affectations[res_id]
        
        # Compléter avec parent2
        for res_id, minibus_id in parent2.affectations.items():
            if res_id not in segment_parent1:
                enfant1.affectations[res_id] = minibus_id
        
        # Ajouter le segment
        enfant1.affectations.update(segment_parent1)
        
        # Même chose pour enfant2 (inversé)
        segment_parent2 = {}
        for i in range(point1, point2):
            res_id = reservations[i].id
            if res_id in parent2.affectations:
                segment_parent2[res_id] = parent2.affectations[res_id]
        
        for res_id, minibus_id in parent1.affectations.items():
            if res_id not in segment_parent2:
                enfant2.affectations[res_id] = minibus_id
        
        enfant2.affectations.update(segment_parent2)
        
        return enfant1, enfant2
    
    # ============= MUTATION =============
    
    def mutation(self, solution: Solution, prob_mutation: float = 0.15) -> Solution:
        """
        Applique une mutation aléatoire à la solution
        """
        if random.random() > prob_mutation:
            return solution
        
        solution = solution.copy()
        
        # Choisir un type de mutation
        type_mutation = random.choice([
            "swap_reservations",
            "reassign_minibus",
            "inverse_sequence",
            "insert_reservation"
        ])
        
        if type_mutation == "swap_reservations":
            solution = self._mutation_swap_reservations(solution)
        
        elif type_mutation == "reassign_minibus":
            solution = self._mutation_reassign_minibus(solution)
        
        elif type_mutation == "inverse_sequence":
            solution = self._mutation_inverse_sequence(solution)
        
        elif type_mutation == "insert_reservation":
            solution = self._mutation_insert_reservation(solution)
        
        return solution
    
    def _mutation_swap_reservations(self, solution: Solution) -> Solution:
        """Échange deux réservations entre elles"""
        if len(solution.affectations) < 2:
            return solution
        
        res_ids = list(solution.affectations.keys())
        res1, res2 = random.sample(res_ids, 2)
        
        # Échanger les minibus assignés
        solution.affectations[res1], solution.affectations[res2] = \
            solution.affectations[res2], solution.affectations[res1]
        
        return solution
    
    def _mutation_reassign_minibus(self, solution: Solution) -> Solution:
        """Réassigne une réservation à un autre minibus"""
        if not solution.affectations:
            return solution
        
        # Choisir une réservation aléatoire
        res_id = random.choice(list(solution.affectations.keys()))
        
        # Choisir un nouveau minibus
        ancien_minibus = solution.affectations[res_id]
        minibus_disponibles = [m.id for m in solution.minibus_list if m.id != ancien_minibus]
        
        if minibus_disponibles:
            nouveau_minibus = random.choice(minibus_disponibles)
            solution.affectations[res_id] = nouveau_minibus
        
        return solution
    
    def _mutation_inverse_sequence(self, solution: Solution) -> Solution:
        """Inverse un segment dans un itinéraire"""
        # Choisir un minibus au hasard parmi ceux utilisés
        minibus_utilises = [mid for mid in solution.itineraires.keys() 
                           if len(solution.itineraires[mid].arrets) > 4]
        
        if not minibus_utilises:
            return solution
        
        minibus_id = random.choice(minibus_utilises)
        arrets = solution.itineraires[minibus_id].arrets
        
        # Choisir deux points (en excluant le depot de départ et d'arrivée)
        if len(arrets) <= 4:
            return solution
        
        i = random.randint(1, len(arrets) - 3)
        j = random.randint(i + 1, len(arrets) - 2)
        
        # Inverser le segment
        arrets[i:j+1] = reversed(arrets[i:j+1])
        
        return solution
    
    def _mutation_insert_reservation(self, solution: Solution) -> Solution:
        """Retire et réinsère une réservation à une position aléatoire"""
        if not solution.affectations:
            return solution
        
        # Choisir une réservation
        res_id = random.choice(list(solution.affectations.keys()))
        minibus_id = solution.affectations[res_id]
        
        # Trouver la réservation
        reservation = next((r for r in solution.reservations_list if r.id == res_id), None)
        if not reservation:
            return solution
        
        # Retirer les arrêts de cette réservation
        arrets = solution.itineraires[minibus_id].arrets
        arrets_filtres = [a for a in arrets if a.reservation_id != res_id]
        
        # Réinsérer à une position aléatoire
        if len(arrets_filtres) >= 2:
            # Position pour pickup (entre depot départ et dernier arrêt)
            pos_pickup = random.randint(1, len(arrets_filtres) - 1)
            # Position pour dropoff (après pickup)
            pos_dropoff = random.randint(pos_pickup, len(arrets_filtres) - 1)
            
            pickup = Arret(
                station_id=reservation.pickup_station_id,
                station_name = solution.stations_dict[reservation.pickup_station_id]["name"],

                type="PICKUP",
                reservation_id=reservation.id,
                personnes=reservation.number_of_people
            )
            
            dropoff = Arret(
                station_id=reservation.dropoff_station_id,
                station_name=solution.stations_dict[reservation.dropoff_station_id]["name"],
                type="DROPOFF",
                reservation_id=reservation.id,
                personnes=reservation.number_of_people
            )
            
            arrets_filtres.insert(pos_pickup, pickup)
            arrets_filtres.insert(pos_dropoff + 1, dropoff)
            
            solution.itineraires[minibus_id].arrets = arrets_filtres
        
        return solution