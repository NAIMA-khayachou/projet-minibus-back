import random
from typing import List, Tuple
from .solution import Solution

class GeneticOperators:
    """Opérateurs génétiques adaptés aux arrêts multiples"""
    
    def __init__(self, matrice_distances, stations_dict):
        self.matrice_distances = matrice_distances
        self.stations_dict = stations_dict
        self.station_ids_order = sorted(stations_dict.keys())
        self.station_id_to_index = {
            sid: idx for idx, sid in enumerate(self.station_ids_order)
        }
    
    def selection_tournoi(self, population: List[Solution], fitness_scores: List[float], 
                         taille_tournoi: int = 3) -> Solution:
        """Sélection par tournoi"""
        indices = random.sample(range(len(population)), min(taille_tournoi, len(population)))
        meilleur_idx = min(indices, key=lambda i: fitness_scores[i])
        return population[meilleur_idx].copy()
    
    def croisement_ordonne(self, parent1: Solution, parent2: Solution, 
                          prob_croisement: float = 0.8) -> Tuple[Solution, Solution]:
        """Croisement ordonné avec préservation des horaires"""
        if random.random() > prob_croisement:
            return parent1.copy(), parent2.copy()
        
        enfant1 = parent1.copy()
        enfant2 = parent2.copy()
        
        enfant1.affectations = {}
        enfant2.affectations = {}
        
        reservations = list(parent1.reservations_list)
        n = len(reservations)
        
        if n < 2:
            return enfant1, enfant2
        
        point1, point2 = sorted(random.sample(range(n), 2))
        
        # Enfant 1
        segment_parent1 = {}
        for i in range(point1, point2):
            res_id = reservations[i].id
            if res_id in parent1.affectations:
                segment_parent1[res_id] = parent1.affectations[res_id]
        
        for res_id, minibus_id in parent2.affectations.items():
            if res_id not in segment_parent1:
                enfant1.affectations[res_id] = minibus_id
        
        enfant1.affectations.update(segment_parent1)
        
        # Enfant 2
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
    
    def mutation(self, solution: Solution, prob_mutation: float = 0.15) -> Solution:
        """Applique une mutation adaptée aux contraintes horaires"""
        if random.random() > prob_mutation:
            return solution
        
        solution = solution.copy()
        
        type_mutation = random.choice([
            "reassign_compatible",  # ✅ NOUVEAU: réassigner à minibus compatible
            "swap_reservations",
            "reassign_minibus",
            "optimize_station_order"  # ✅ NOUVEAU: optimiser l'ordre des arrêts
        ])
        
        if type_mutation == "reassign_compatible":
            solution = self._mutation_reassign_compatible(solution)
        elif type_mutation == "swap_reservations":
            solution = self._mutation_swap_reservations(solution)
        elif type_mutation == "reassign_minibus":
            solution = self._mutation_reassign_minibus(solution)
        elif type_mutation == "optimize_station_order":
            solution = self._mutation_optimize_order(solution)
        
        return solution
    
    def _mutation_reassign_compatible(self, solution: Solution) -> Solution:
        """
        ✅ NOUVEAU: Réassigne une réservation à un minibus dont la route 
        passe déjà par sa station pickup
        """
        if not solution.affectations:
            return solution
        
        # Choisir une réservation au hasard
        res_id = random.choice(list(solution.affectations.keys()))
        reservation = next((r for r in solution.reservations_list if r.id == res_id), None)
        
        if not reservation:
            return solution
        
        # Chercher un minibus compatible
        minibus_compatible = solution.trouver_minibus_compatible(reservation)
        
        if minibus_compatible and minibus_compatible != solution.affectations[res_id]:
            solution.affectations[res_id] = minibus_compatible
        
        return solution
    
    def _mutation_swap_reservations(self, solution: Solution) -> Solution:
        """Échange deux réservations entre elles"""
        if len(solution.affectations) < 2:
            return solution
        
        res_ids = list(solution.affectations.keys())
        res1, res2 = random.sample(res_ids, 2)
        
        solution.affectations[res1], solution.affectations[res2] = \
            solution.affectations[res2], solution.affectations[res1]
        
        return solution
    
    def _mutation_reassign_minibus(self, solution: Solution) -> Solution:
        """Réassigne une réservation à un autre minibus"""
        if not solution.affectations:
            return solution
        
        res_id = random.choice(list(solution.affectations.keys()))
        ancien_minibus = solution.affectations[res_id]
        minibus_disponibles = [m.id for m in solution.minibus_list if m.id != ancien_minibus]
        
        if minibus_disponibles:
            nouveau_minibus = random.choice(minibus_disponibles)
            solution.affectations[res_id] = nouveau_minibus
        
        return solution
    
    def _mutation_optimize_order(self, solution: Solution) -> Solution:
        """
        ✅ NOUVEAU: Optimise l'ordre des arrêts dans un itinéraire
        en minimisant la distance tout en respectant les contraintes
        """
        minibus_utilises = [mid for mid in solution.itineraires.keys() 
                           if len(solution.itineraires[mid].arrets) > 4]
        
        if not minibus_utilises:
            return solution
        
        minibus_id = random.choice(minibus_utilises)
        itineraire = solution.itineraires[minibus_id]
        arrets = itineraire.arrets[1:-1]  # Exclure les dépôts
        
        if len(arrets) <= 2:
            return solution
        
        # Trier les arrêts par heure souhaitée minimale
        def get_min_time(arret):
            times = []
            for res in solution.reservations_list:
                if res.id in arret.pickups:
                    times.append(res.desired_time)
            from datetime import datetime
            return min(times) if times else datetime.max
        
        arrets_tries = sorted(arrets, key=get_min_time)
        
        # Reconstruire l'itinéraire
        itineraire.arrets = [itineraire.arrets[0]] + arrets_tries + [itineraire.arrets[-1]]
        
        return solution