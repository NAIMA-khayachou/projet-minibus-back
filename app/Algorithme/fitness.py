from typing import Tuple, Dict
from .solution import Solution
import logging

logger = logging.getLogger(__name__)

class FitnessCalculator:
    """Calcule le fitness avec contraintes horaires et arrêts multiples"""
    
    def __init__(self, matrice_distances, matrice_durees, stations_dict, use_osrm=True):
        self.matrice_distances = matrice_distances
        self.matrice_durees = matrice_durees
        self.stations_dict = stations_dict
        self.use_osrm = use_osrm
        
        self.station_ids_order = sorted(stations_dict.keys())
        self.station_id_to_index = {
            sid: idx for idx, sid in enumerate(self.station_ids_order)
        }
        
        # Poids des pénalités
        self.PENALITE_CAPACITE = 10000
        self.PENALITE_RESERVATION_NON_SERVIE = 50000
        self.PENALITE_ORDRE_INVALIDE = 100000
        self.PENALITE_RETARD_PAR_MINUTE = 500
        self.BONUS_REUTILISATION = -100
        
        # ✅ NOUVEAU : Temps d'arrêt fixe (en MINUTES)
        self.TEMPS_ARRET_MINUTES = 2
        
        logger.info(f"✅ FitnessCalculator initialisé (OSRM={use_osrm})")
    
    def calculer_fitness(self, solution: Solution) -> Tuple[float, Dict]:
        """
        Calcule le fitness de la solution avec contraintes horaires
        
        Retourne: (fitness, details)
        """
        distance_totale = 0.0
        duree_totale = 0.0
        violations_capacite = 0
        violations_ordre = 0
        violations_horaire = 0
        retard_total = 0.0
        minibus_utilises = 0
        bonus_reutilisation = 0
        
        for minibus_id, itineraire in solution.itineraires.items():
            if len(itineraire.arrets) <= 2:
                continue
            
            minibus_utilises += 1
            
            minibus_obj = next((m for m in solution.minibus_list if m.id == minibus_id), None)
            capacite = minibus_obj.capacity if minibus_obj else 20
            
            # Évaluer l'itinéraire
            dist, duree, charge_max, viol_cap, viol_ord, viol_hor, retard, bonus = \
                self._evaluer_itineraire(itineraire, capacite, solution.reservations_list)
            
            distance_totale += dist
            duree_totale += duree
            violations_capacite += viol_cap
            violations_ordre += viol_ord
            violations_horaire += viol_hor
            retard_total += retard
            bonus_reutilisation += bonus
            
            # Mettre à jour l'itinéraire
            itineraire.distance_totale = dist
            itineraire.duree_totale = duree
            itineraire.charge_maximale = charge_max
            itineraire.violations_capacite = viol_cap
            itineraire.violations_horaire = viol_hor
        
        # Réservations non servies
        reservations_servies = len(solution.affectations)
        total_reservations = len(solution.reservations_list)
        reservations_non_servies = total_reservations - reservations_servies
        
        # ✅ CALCUL DU FITNESS AVEC CONTRAINTES HORAIRES
        fitness = distance_totale
        fitness += violations_capacite * self.PENALITE_CAPACITE
        fitness += reservations_non_servies * self.PENALITE_RESERVATION_NON_SERVIE
        fitness += violations_ordre * self.PENALITE_ORDRE_INVALIDE
        fitness += retard_total * self.PENALITE_RETARD_PAR_MINUTE
        fitness += bonus_reutilisation * self.BONUS_REUTILISATION
        
        # Mettre à jour la solution
        solution.distance_totale_flotte = distance_totale
        solution.duree_totale_flotte = duree_totale
        solution.nombre_minibus_utilises = minibus_utilises
        solution.fitness = fitness
        solution.violations_totales = violations_capacite + violations_ordre + violations_horaire
        solution.retard_total = retard_total
        
        details = {
            "distance_totale": distance_totale,
            "duree_totale": duree_totale,
            "violations_capacite": violations_capacite,
            "violations_ordre": violations_ordre,
            "violations_horaire": violations_horaire,
            "retard_total_minutes": retard_total,
            "reservations_non_servies": reservations_non_servies,
            "minibus_utilises": minibus_utilises,
            "bonus_reutilisation": bonus_reutilisation
        }
        
        return fitness, details
    
    def _evaluer_itineraire(self, itineraire, capacite: int, reservations_list) -> Tuple:
        """
        ✅ CORRIGÉ : Évalue un itinéraire avec conversion correcte des unités
        
        Retourne: (distance_km, duree_min, charge_max, violations_capacite, 
                  violations_ordre, violations_horaire, retard_total, bonus_reutilisation)
        """
        distance_totale = 0.0
        duree_totale = 0.0
        charge_actuelle = 0
        charge_max = 0
        violations_capacite = 0
        violations_ordre = 0
        violations_horaire = 0
        retard_total = 0.0
        bonus_reutilisation = 0
        
        # Suivre les pickups effectués
        pickups_effectues = set()
        
        # Dictionnaire des réservations
        reservations_dict = {r.id: r for r in reservations_list}
        
        for i in range(len(itineraire.arrets)):
            arret = itineraire.arrets[i]
            
            # Calculer distance et durée
            if i > 0:
                arret_precedent = itineraire.arrets[i-1]
                
                idx_prec = self.station_id_to_index.get(arret_precedent.station_id)
                idx_curr = self.station_id_to_index.get(arret.station_id)
                
                if idx_prec is not None and idx_curr is not None:
                    dist_brut = self.matrice_distances[idx_prec][idx_curr]
                    duree_brut = self.matrice_durees[idx_prec][idx_curr]
                    
                    # ✅ CORRECTION PRINCIPALE : Conversion correcte des unités OSRM
                    if self.use_osrm:
                        # OSRM retourne : distances en MÈTRES, durées en SECONDES
                        dist_km = dist_brut / 1000.0
                        duree_min = duree_brut / 60.0
                    else:
                        # Matrices déjà en km et minutes
                        dist_km = dist_brut
                        duree_min = duree_brut
                    
                    # ✅ Ajouter le temps d'arrêt seulement si ce n'est pas le dépôt final
                    if arret.type != "DEPOT" or i < len(itineraire.arrets) - 1:
                        duree_min += self.TEMPS_ARRET_MINUTES
                    
                    # Accumuler
                    distance_totale += dist_km
                    duree_totale += duree_min
                    
                    # Stocker dans l'arrêt
                    arret.distance_depuis_precedent = dist_km
                    arret.duree_depuis_precedent = duree_min
            
            # ✅ Gérer les DROPOFFS d'abord
            for dropoff_id in arret.dropoffs:
                if dropoff_id not in pickups_effectues:
                    violations_ordre += 1
                    logger.warning(f"⚠️ DROPOFF avant PICKUP pour réservation {dropoff_id}")
                else:
                    # Retirer les passagers
                    reservation = reservations_dict.get(dropoff_id)
                    if reservation:
                        charge_actuelle -= reservation.number_of_people
            
            # ✅ Gérer les PICKUPS ensuite
            for pickup_id in arret.pickups:
                reservation = reservations_dict.get(pickup_id)
                if reservation:
                    charge_actuelle += reservation.number_of_people
                    pickups_effectues.add(pickup_id)
                    
                    # ✅ Vérifier le retard
                    if arret.heure_arrivee and reservation.est_en_retard(arret.heure_arrivee):
                        retard = reservation.calculer_retard(arret.heure_arrivee)
                        retard_total += retard
                        violations_horaire += 1
                        logger.debug(f"⏰ Retard de {retard:.1f} min pour réservation {pickup_id}")
                    
                    # ✅ Bonus si plusieurs pickups à la même station
                    if len(arret.pickups) > 1:
                        bonus_reutilisation += 1
            
            # Vérifier la capacité
            if charge_actuelle > capacite:
                violations_capacite += 1
                logger.warning(f"⚠️ Surcharge: {charge_actuelle}/{capacite} à {arret.station_name}")
            
            # Enregistrer l'état
            arret.passagers_a_bord = charge_actuelle
            arret.capacite_restante = capacite - charge_actuelle
            charge_max = max(charge_max, charge_actuelle)
            
        return (distance_totale, duree_totale, charge_max, violations_capacite, 
                violations_ordre, violations_horaire, retard_total, bonus_reutilisation)