"""
Module pour intégrer dynamiquement de nouvelles réservations
"""
import logging
from typing import Optional, Tuple
from datetime import datetime
from .solution import Solution

logger = logging.getLogger(__name__)

class ReservationIntegrator:
    """Gère l'intégration de nouvelles réservations dans des routes existantes"""
    
    def __init__(self, solution_builder, fitness_calculator):
        self.solution_builder = solution_builder
        self.fitness_calculator = fitness_calculator
    
    def integrer_nouvelle_reservation(
        self, 
        solution_actuelle: Solution, 
        nouvelle_reservation
    ) -> Tuple[bool, Optional[int], str]:
        """
        ✅ FONCTION PRINCIPALE: Intègre une nouvelle réservation
        
        Stratégie:
        1. Chercher un minibus dont la route passe par la station pickup
        2. Si trouvé, ajouter la réservation à ce minibus
        3. Sinon, assigner à un minibus peu chargé
        
        Returns:
            (succès: bool, minibus_id: int, message: str)
        """
        logger.info(f"🔍 Intégration de la réservation {nouvelle_reservation.id}")
        logger.info(f"   Pickup: Station {nouvelle_reservation.pickup_station_id}")
        logger.info(f"   Dropoff: Station {nouvelle_reservation.dropoff_station_id}")
        logger.info(f"   Personnes: {nouvelle_reservation.number_of_people}")
        logger.info(f"   Heure souhaitée: {nouvelle_reservation.desired_time}")
        
        # 1. Chercher un minibus compatible
        minibus_compatible = solution_actuelle.trouver_minibus_compatible(nouvelle_reservation)
        
        if minibus_compatible:
            logger.info(f"✅ Minibus compatible trouvé: {minibus_compatible}")
            
            # Ajouter la réservation
            solution_actuelle.affectations[nouvelle_reservation.id] = minibus_compatible
            
            # Ajouter à la liste des réservations
            if nouvelle_reservation not in solution_actuelle.reservations_list:
                solution_actuelle.reservations_list.append(nouvelle_reservation)
                solution_actuelle.reservations_by_id[nouvelle_reservation.id] = nouvelle_reservation
            
            # Reconstruire l'itinéraire de ce minibus
            self._reconstruire_itineraire_minibus(solution_actuelle, minibus_compatible)
            
            # Recalculer le fitness
            self.fitness_calculator.calculer_fitness(solution_actuelle)
            
            return (
                True, 
                minibus_compatible,
                f"Réservation intégrée au minibus {minibus_compatible} (route existante réutilisée)"
            )
        
        else:
            logger.info("⚠️ Aucun minibus compatible, assignation à un minibus peu chargé")
            
            # Trouver le minibus le moins chargé
            minibus_moins_charge = min(
                solution_actuelle.minibus_list,
                key=lambda m: solution_actuelle.itineraires[m.id].charge_maximale
            )
            
            # Vérifier la capacité
            capacite_disponible = (
                minibus_moins_charge.capacity - 
                solution_actuelle.itineraires[minibus_moins_charge.id].charge_maximale
            )
            
            if capacite_disponible >= nouvelle_reservation.number_of_people:
                solution_actuelle.affectations[nouvelle_reservation.id] = minibus_moins_charge.id
                
                if nouvelle_reservation not in solution_actuelle.reservations_list:
                    solution_actuelle.reservations_list.append(nouvelle_reservation)
                    solution_actuelle.reservations_by_id[nouvelle_reservation.id] = nouvelle_reservation
                
                # Reconstruire l'itinéraire
                self._reconstruire_itineraire_minibus(solution_actuelle, minibus_moins_charge.id)
                
                # Recalculer le fitness
                self.fitness_calculator.calculer_fitness(solution_actuelle)
                
                return (
                    True,
                    minibus_moins_charge.id,
                    f"Réservation assignée au minibus {minibus_moins_charge.id} (nouvelle route)"
                )
            else:
                logger.error("❌ Aucun minibus n'a la capacité suffisante")
                return (
                    False,
                    None,
                    f"Impossible d'intégrer: capacité insuffisante (besoin: {nouvelle_reservation.number_of_people}, dispo: {capacite_disponible})"
                )
    
    def _reconstruire_itineraire_minibus(self, solution: Solution, minibus_id: int):
        """Reconstruit l'itinéraire d'un seul minibus"""
        reservations = solution.get_reservations_by_minibus(minibus_id)
        
        if not reservations:
            return
        
        # Trier par heure souhaitée
        reservations = sorted(reservations, key=lambda r: r.desired_time or datetime.max)
        
        # Utiliser le solution_builder pour reconstruire
        self.solution_builder._construire_itineraire_optimise(
            solution, 
            minibus_id, 
            reservations
        )
    
    def analyser_impact(
        self, 
        solution_avant: Solution, 
        solution_apres: Solution
    ) -> dict:
        """
        ✅ Analyse l'impact de l'ajout d'une réservation
        """
        impact = {
            "distance_ajoutee": solution_apres.distance_totale_flotte - solution_avant.distance_totale_flotte,
            "duree_ajoutee": solution_apres.duree_totale_flotte - solution_avant.duree_totale_flotte,
            "fitness_avant": solution_avant.fitness,
            "fitness_apres": solution_apres.fitness,
            "degradation_fitness": solution_apres.fitness - solution_avant.fitness,
            "violations_ajoutees": solution_apres.violations_totales - solution_avant.violations_totales,
            "retard_ajoute": solution_apres.retard_total - solution_avant.retard_total
        }
        
        logger.info("\n📊 IMPACT DE L'INTÉGRATION:")
        logger.info(f"   Distance ajoutée: +{impact['distance_ajoutee']:.2f} km")
        logger.info(f"   Durée ajoutée: +{impact['duree_ajoutee']:.1f} min")
        logger.info(f"   Fitness: {impact['fitness_avant']:.2f} → {impact['fitness_apres']:.2f}")
        
        if impact['violations_ajoutees'] > 0:
            logger.warning(f"   ⚠️ Violations ajoutées: +{impact['violations_ajoutees']}")
        
        if impact['retard_ajoute'] > 0:
            logger.warning(f"   ⏰ Retard ajouté: +{impact['retard_ajoute']:.1f} min")
        
        return impact


def exemple_utilisation_integration():
    """
    ✅ EXEMPLE: Comment utiliser le système avec une nouvelle réservation
    """
    from app.Algorithme.genetic_algoritme import GeneticAlgorithm
    from models.route import RouteManager
    from models.station import StationManager
    from models.bus import BusManager
    from database import SessionLocal
    
    # 1. Récupérer les données
    db = SessionLocal()
    
    route_manager = RouteManager(db)
    station_manager = StationManager(db)
    bus_manager = BusManager(db)
    
    # Charger les données existantes
    stations = station_manager.load_all_stations()
    stations_dict = {s.id: s for s in stations}
    
    minibus_list = bus_manager.get_available_buses()
    reservations_existantes = route_manager.get_pending_reservations()
    
    # 2. Optimiser avec l'algorithme génétique
    from app.internal.osrm_engine import OSRMClient
    osrm = OSRMClient()
    
    coords = [(s.latitude, s.longitude) for s in stations]
    matrice_distances, matrice_durees = osrm.get_distance_matrix_from_coords(coords)
    
    ga = GeneticAlgorithm(
        reservations=reservations_existantes,
        minibus=minibus_list,
        stations_dict=stations_dict,
        matrice_distances=matrice_distances,
        matrice_durees=matrice_durees,
        depot_station_id=1,
        use_osrm=True,
        population_size=50,
        generations=100
    )
    
    solution_optimale, _ = ga.run()
    
    # 3. NOUVELLE RÉSERVATION ARRIVE
    from models.route import Reservation
    
    nouvelle_reservation = Reservation(
        id=999,  # ID temporaire
        client_id=1,
        pickup_station_id=5,
        dropoff_station_id=12,
        number_of_people=3,
        desired_time=datetime.now(),
        status='pending'
    )
    
    # 4. Intégrer la nouvelle réservation
    integrator = ReservationIntegrator(
        ga.solution_builder,
        ga.fitness_calculator
    )
    
    solution_avant = solution_optimale.copy()
    
    succes, minibus_id, message = integrator.integrer_nouvelle_reservation(
        solution_optimale,
        nouvelle_reservation
    )
    
    if succes:
        print(f"✅ {message}")
        
        # Analyser l'impact
        impact = integrator.analyser_impact(solution_avant, solution_optimale)
        
        # Sauvegarder dans la BD
        route_solution = solution_optimale.to_route_solution(minibus_id)
        if route_solution:
            route_manager.save_optimized_route(route_solution)
    else:
        print(f"❌ {message}")
    
    db.close()