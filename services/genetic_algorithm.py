# app/services/genetic_algorithm.py

import random
import copy
import logging
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from datetime import time

from app.core.config import settings
from app.core.osrm_engine import get_cost_matrices
from app.database.connection import db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Station:
    id: int
    name: str
    latitude: float
    longitude: float


@dataclass
class Minibus:
    id: int
    capacity: int
    license_plate: str


@dataclass
class Reservation:
    id: int
    client_id: int
    pickup_station_id: int
    dropoff_station_id: int
    number_of_people: int
    desired_time: Optional[time]


@dataclass
class StopPoint:
    station_id: int
    type: str  # 'PICKUP' ou 'DROPOFF'
    reservation_id: int
    passengers: int


class Individual:
    """Représente un individu (solution) dans la population"""
    
    def __init__(self, minibus_routes: Dict[int, List[StopPoint]]):
        self.minibus_routes = minibus_routes
        self.fitness = float('inf')
        self.total_distance = 0.0
        self.violations = 0
    
    def __lt__(self, other):
        return self.fitness < other.fitness


class GeneticAlgorithm:
    """Algorithme génétique pour l'optimisation des routes de minibus"""
    
    def __init__(self):
        self.stations: Dict[int, Station] = {}
        self.minibus: Dict[int, Minibus] = {}
        self.reservations: List[Reservation] = []
        self.distance_matrix: List[List[float]] = []
        self.time_matrix: List[List[float]] = []
        self.station_id_to_index: Dict[int, int] = {}
        
        # Paramètres de l'AG
        self.population_size = settings.GA_POPULATION_SIZE
        self.max_generations = settings.GA_MAX_GENERATIONS
        self.mutation_rate = settings.GA_MUTATION_RATE
        self.crossover_rate = settings.GA_CROSSOVER_RATE
        self.elitism_rate = settings.GA_ELITISM_RATE
        self.tournament_size = settings.GA_TOURNAMENT_SIZE
        self.convergence_threshold = settings.GA_CONVERGENCE_THRESHOLD
        
    def load_data(self):
        """Charge les données depuis PostgreSQL"""
        conn = db.get_connection()
        try:
            cursor = conn.cursor()
            
            # Charger les stations
            cursor.execute("SELECT id, name, latitude, longitude FROM stations ORDER BY id")
            for row in cursor.fetchall():
                station = Station(id=row[0], name=row[1], latitude=row[2], longitude=row[3])
                self.stations[station.id] = station
            
            # Charger les minibus
            cursor.execute("SELECT id, capacity, license_plate FROM minibus WHERE status='available' ORDER BY id")
            for row in cursor.fetchall():
                bus = Minibus(id=row[0], capacity=row[1], license_plate=row[2])
                self.minibus[bus.id] = bus
            
            # Charger les réservations
            cursor.execute("""
                SELECT id, client_id, pickup_station_id, dropoff_station_id, 
                       number_of_people, desired_time 
                FROM reservations 
                WHERE status='pending'
                ORDER BY id
            """)
            for row in cursor.fetchall():
                reservation = Reservation(
                    id=row[0], client_id=row[1], pickup_station_id=row[2],
                    dropoff_station_id=row[3], number_of_people=row[4], desired_time=row[5]
                )
                self.reservations.append(reservation)
            
            cursor.close()
            logger.info(f"✓ Données chargées: {len(self.stations)} stations, "
                       f"{len(self.minibus)} minibus, {len(self.reservations)} réservations")
            
        finally:
            db.release_connection(conn)
    
    def build_cost_matrices(self):
        """Construit les matrices de distance et temps via OSRM"""
        # Préparer les points (lon, lat) pour OSRM
        points = [(s.longitude, s.latitude) for s in self.stations.values()]
        
        # Créer un mapping station_id -> index
        for idx, station_id in enumerate(self.stations.keys()):
            self.station_id_to_index[station_id] = idx
        
        # Obtenir les matrices
        time_matrix, distance_matrix = get_cost_matrices(points)
        
        if time_matrix is None or distance_matrix is None:
            raise Exception("Impossible d'obtenir les matrices de coût depuis OSRM")
        
        self.time_matrix = time_matrix
        # Convertir distances de mètres en km
        self.distance_matrix = [[d / 1000.0 for d in row] for row in distance_matrix]
        
        logger.info(f"✓ Matrices de coût créées: {len(self.distance_matrix)}x{len(self.distance_matrix)}")
    
    def get_distance(self, station_id1: int, station_id2: int) -> float:
        """Retourne la distance entre deux stations"""
        idx1 = self.station_id_to_index[station_id1]
        idx2 = self.station_id_to_index[station_id2]
        return self.distance_matrix[idx1][idx2]
    
    def create_random_individual(self) -> Individual:
        """Crée un individu aléatoire"""
        # Créer une liste de toutes les réservations
        reservations_copy = self.reservations.copy()
        random.shuffle(reservations_copy)
        
        # Répartir les réservations entre les minibus
        minibus_routes = {bus_id: [] for bus_id in self.minibus.keys()}
        minibus_list = list(self.minibus.keys())
        
        for reservation in reservations_copy:
            # Choisir un minibus aléatoire
            bus_id = random.choice(minibus_list)
            
            # Ajouter pickup et dropoff
            minibus_routes[bus_id].append(StopPoint(
                station_id=reservation.pickup_station_id,
                type='PICKUP',
                reservation_id=reservation.id,
                passengers=reservation.number_of_people
            ))
            minibus_routes[bus_id].append(StopPoint(
                station_id=reservation.dropoff_station_id,
                type='DROPOFF',
                reservation_id=reservation.id,
                passengers=reservation.number_of_people
            ))
        
        return Individual(minibus_routes)
    
    def calculate_fitness(self, individual: Individual) -> float:
        """Calcule le fitness (distance totale + pénalités)"""
        total_distance = 0.0
        violations = 0
        
        for bus_id, route in individual.minibus_routes.items():
            if not route:
                continue
            
            bus_capacity = self.minibus[bus_id].capacity
            current_passengers = 0
            
            # Ajouter distance du premier arrêt (depuis dépôt fictif - station 1)
            if route:
                first_station = route[0].station_id
                total_distance += self.get_distance(1, first_station)
            
            # Calculer distance et vérifier capacité
            for i, stop in enumerate(route):
                if stop.type == 'PICKUP':
                    current_passengers += stop.passengers
                elif stop.type == 'DROPOFF':
                    current_passengers -= stop.passengers
                
                # Vérifier violation de capacité
                if current_passengers > bus_capacity:
                    violations += 1
                
                # Distance vers le prochain arrêt
                if i < len(route) - 1:
                    current_station = stop.station_id
                    next_station = route[i + 1].station_id
                    total_distance += self.get_distance(current_station, next_station)
            
            # Retour au dépôt
            if route:
                last_station = route[-1].station_id
                total_distance += self.get_distance(last_station, 1)
        
        # Fitness = distance + pénalités
        fitness = total_distance + (violations * settings.CAPACITY_VIOLATION_PENALTY)
        
        individual.fitness = fitness
        individual.total_distance = total_distance
        individual.violations = violations
        
        return fitness
    
    def tournament_selection(self, population: List[Individual]) -> Individual:
        """Sélection par tournoi"""
        tournament = random.sample(population, self.tournament_size)
        return min(tournament, key=lambda ind: ind.fitness)
    
    def crossover(self, parent1: Individual, parent2: Individual) -> Individual:
        """Croisement de deux parents"""
        if random.random() > self.crossover_rate:
            return copy.deepcopy(parent1)
        
        child_routes = {}
        
        for bus_id in self.minibus.keys():
            # Choisir aléatoirement entre les routes des deux parents
            if random.random() < 0.5:
                child_routes[bus_id] = copy.deepcopy(parent1.minibus_routes[bus_id])
            else:
                child_routes[bus_id] = copy.deepcopy(parent2.minibus_routes[bus_id])
        
        return Individual(child_routes)
    
    def mutate(self, individual: Individual):
        """Mutation d'un individu"""
        if random.random() > self.mutation_rate:
            return
        
        mutation_type = random.choice(['swap', 'move', 'reverse'])
        
        # Choisir un minibus aléatoire non vide
        non_empty_buses = [bus_id for bus_id, route in individual.minibus_routes.items() if route]
        if not non_empty_buses:
            return
        
        bus_id = random.choice(non_empty_buses)
        route = individual.minibus_routes[bus_id]
        
        if len(route) < 2:
            return
        
        if mutation_type == 'swap':
            # Échanger deux arrêts
            i, j = random.sample(range(len(route)), 2)
            route[i], route[j] = route[j], route[i]
        
        elif mutation_type == 'move':
            # Déplacer une réservation vers un autre minibus
            other_buses = [bid for bid in self.minibus.keys() if bid != bus_id]
            if other_buses:
                target_bus = random.choice(other_buses)
                # Trouver une réservation complète (pickup + dropoff)
                reservation_ids = list(set(stop.reservation_id for stop in route))
                if reservation_ids:
                    res_id = random.choice(reservation_ids)
                    stops_to_move = [s for s in route if s.reservation_id == res_id]
                    individual.minibus_routes[bus_id] = [s for s in route if s.reservation_id != res_id]
                    individual.minibus_routes[target_bus].extend(stops_to_move)
        
        elif mutation_type == 'reverse':
            # Inverser une portion de la route
            i, j = sorted(random.sample(range(len(route)), 2))
            route[i:j+1] = reversed(route[i:j+1])
    
    def optimize(self) -> Individual:
        """Exécute l'algorithme génétique"""
        logger.info("Démarrage de l'optimisation...")
        
        # Initialiser la population
        population = [self.create_random_individual() for _ in range(self.population_size)]
        
        # Évaluer la population initiale
        for individual in population:
            self.calculate_fitness(individual)
        
        best_individual = min(population, key=lambda ind: ind.fitness)
        generations_without_improvement = 0
        
        for generation in range(self.max_generations):
            # Tri de la population
            population.sort(key=lambda ind: ind.fitness)
            
            # Vérifier amélioration
            if population[0].fitness < best_individual.fitness:
                best_individual = copy.deepcopy(population[0])
                generations_without_improvement = 0
                logger.info(f"Génération {generation}: Meilleure fitness = {best_individual.fitness:.2f} km "
                           f"(violations: {best_individual.violations})")
            else:
                generations_without_improvement += 1
            
            # Critère de convergence
            if generations_without_improvement >= self.convergence_threshold:
                logger.info(f"Convergence atteinte après {generation} générations")
                break
            
            # Élitisme
            elite_size = int(self.population_size * self.elitism_rate)
            new_population = population[:elite_size]
            
            # Créer nouvelle génération
            while len(new_population) < self.population_size:
                parent1 = self.tournament_selection(population)
                parent2 = self.tournament_selection(population)
                
                child = self.crossover(parent1, parent2)
                self.mutate(child)
                self.calculate_fitness(child)
                
                new_population.append(child)
            
            population = new_population
        
        logger.info(f"✓ Optimisation terminée - Distance totale: {best_individual.total_distance:.2f} km")
        return best_individual
    
    def format_solution(self, individual: Individual) -> Dict:
        """Formate la solution pour l'affichage"""
        solution = {}
        
        for bus_id, route in individual.minibus_routes.items():
            if not route:
                continue
            
            bus = self.minibus[bus_id]
            itinerary = []
            current_passengers = 0
            total_distance = 0.0
            
            # Point de départ
            itinerary.append({
                'station': 'Dépôt',
                'type': 'DEPART',
                'distance_depuis_precedent': 0.0,
                'passagers_a_bord': 0,
                'capacite_restante': bus.capacity
            })
            
            # Premier arrêt
            if route:
                first_dist = self.get_distance(1, route[0].station_id)
                total_distance += first_dist
            
            # Parcourir la route
            for i, stop in enumerate(route):
                station = self.stations[stop.station_id]
                
                if stop.type == 'PICKUP':
                    current_passengers += stop.passengers
                elif stop.type == 'DROPOFF':
                    current_passengers -= stop.passengers
                
                dist_from_prev = 0.0
                if i == 0:
                    dist_from_prev = self.get_distance(1, stop.station_id)
                else:
                    prev_station = route[i-1].station_id
                    dist_from_prev = self.get_distance(prev_station, stop.station_id)
                    total_distance += dist_from_prev
                
                itinerary.append({
                    'station': station.name,
                    'type': stop.type,
                    'distance_depuis_precedent': round(dist_from_prev, 2),
                    'passagers_a_bord': current_passengers,
                    'capacite_restante': bus.capacity - current_passengers,
                    'reservation_id': stop.reservation_id
                })
            
            # Retour au dépôt
            if route:
                last_dist = self.get_distance(route[-1].station_id, 1)
                total_distance += last_dist
                itinerary.append({
                    'station': 'Dépôt',
                    'type': 'RETOUR',
                    'distance_depuis_precedent': round(last_dist, 2),
                    'passagers_a_bord': 0,
                    'capacite_restante': bus.capacity
                })
            
            solution[f'minibus_{bus_id}'] = {
                'license_plate': bus.license_plate,
                'capacity': bus.capacity,
                'itinerary': itinerary,
                'distance_totale': round(total_distance, 2),
                'nombre_arrets': len(itinerary)
            }
        
        return solution