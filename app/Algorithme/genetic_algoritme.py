# app/algorithms/genetic_algorithm.py - VERSION CORRIGÉE

import random
import logging
from typing import List, Tuple
from .solution import Solution
from .fitness import FitnessCalculator
from .operateur import GeneticOperators
from .solution_builder import SolutionBuilder

logger = logging.getLogger(__name__)

class GeneticAlgorithm:
    def __init__(
        self,
        reservations,
        minibus,
        stations_dict,
        matrice_distances,
        matrice_durees,
        depot_station_id=None,      # ✅ AJOUTÉ
        use_osrm=True,               # ✅ AJOUTÉ
        population_size: int = 50,   # ✅ AUGMENTÉ (était 10)
        generations: int = 100,      # ✅ AUGMENTÉ (était 10)
        prob_croisement: float = 0.8,
        prob_mutation: float = 0.2,  # ✅ AUGMENTÉ (était 0.15)
        tournament_size: int = 3
    ):
        self.reservations = reservations
        self.minibus = minibus
        self.stations_dict = stations_dict
        self.matrice_distances = matrice_distances
        self.matrice_durees = matrice_durees
        self.use_osrm = use_osrm
        self.population_size = population_size
        self.generations = generations
        self.prob_croisement = prob_croisement
        self.prob_mutation = prob_mutation
        self.tournament_size = tournament_size

        # ✅ CORRECTION 1: Passer depot_station_id au SolutionBuilder
        self.solution_builder = SolutionBuilder(
            matrice_distances, 
            matrice_durees, 
            stations_dict,
            depot_station_id=depot_station_id  # ✅ AJOUTÉ
        )
        
        self.operators = GeneticOperators(matrice_distances, stations_dict)
        
        # ✅ CORRECTION 2: Passer use_osrm au FitnessCalculator
        self.fitness_calculator = FitnessCalculator(
            matrice_distances, 
            matrice_durees, 
            stations_dict,
            use_osrm=use_osrm  # ✅ AJOUTÉ
        )
        
        logger.info(f"✅ GeneticAlgorithm initialisé:")
        logger.info(f"   - Population: {population_size}")
        logger.info(f"   - Générations: {generations}")
        logger.info(f"   - Prob mutation: {prob_mutation}")
        logger.info(f"   - OSRM: {use_osrm}")

    def run(self) -> Tuple[Solution, dict]:
        """Exécute l'algorithme génétique et retourne la meilleure solution"""
        
        logger.info("🧬 Démarrage de l'algorithme génétique...")
        
        # 1️⃣ Générer population initiale
        population: List[Solution] = self.solution_builder.generer_population_initiale(
            self.reservations, self.minibus, self.population_size
        )
        
        if not population:
            logger.error("❌ Échec de génération de la population initiale")
            return None, {}

        best_solution = None
        best_fitness = float('inf')
        best_details = {}
        
        # ✅ CORRECTION 3: Suivre la stagnation pour détecter convergence prématurée
        generations_sans_amelioration = 0
        seuil_stagnation = 20  # Arrêter si pas d'amélioration pendant 20 générations

        # 2️⃣ Boucle sur les générations
        for gen in range(self.generations):
            # Calculer le fitness de chaque solution
            fitness_scores = []
            fitness_ameliore = False
            
            for sol in population:
                fitness, details = self.fitness_calculator.calculer_fitness(sol)
                fitness_scores.append(fitness)

                # Mettre à jour la meilleure solution globale
                if fitness < best_fitness:
                    best_fitness = fitness
                    best_solution = sol.copy()  # ✅ ASSUREZ-VOUS QUE copy() est bien implémenté
                    best_details = details
                    fitness_ameliore = True
                    generations_sans_amelioration = 0
            
            # ✅ CORRECTION 4: Compteur de stagnation
            if not fitness_ameliore:
                generations_sans_amelioration += 1
            
            # ✅ CORRECTION 5: Affichage détaillé
            fitness_moyen = sum(fitness_scores) / len(fitness_scores) if fitness_scores else 0
            fitness_min = min(fitness_scores) if fitness_scores else 0
            fitness_max = max(fitness_scores) if fitness_scores else 0
            
            logger.info(
                f"Génération {gen+1}/{self.generations} | "
                f"Meilleur: {best_fitness:.2f} | "
                f"Moy: {fitness_moyen:.2f} | "
                f"Min: {fitness_min:.2f} | "
                f"Max: {fitness_max:.2f}"
            )
            
            # ✅ CORRECTION 6: Arrêt précoce si stagnation
            if generations_sans_amelioration >= seuil_stagnation:
                logger.warning(f"⚠️ Arrêt précoce: stagnation depuis {seuil_stagnation} générations")
                break

            # ✅ CORRECTION 7: Élitisme - garder les meilleurs
            elite_count = max(2, self.population_size // 10)  # 10% de la population
            
            # Trier par fitness (croissant)
            population_avec_fitness = list(zip(population, fitness_scores))
            population_avec_fitness.sort(key=lambda x: x[1])
            
            # Garder l'élite
            elite = [sol.copy() for sol, _ in population_avec_fitness[:elite_count]]
            
            # Créer une nouvelle population
            nouvelle_population = elite.copy()

            while len(nouvelle_population) < self.population_size:
                # Sélection par tournoi
                parent1 = self.operators.selection_tournoi(
                    population, fitness_scores, self.tournament_size
                )
                parent2 = self.operators.selection_tournoi(
                    population, fitness_scores, self.tournament_size
                )

                # Croisement
                enfant1, enfant2 = self.operators.croisement_ordonne(
                    parent1, parent2, self.prob_croisement
                )

                # Mutation
                enfant1 = self.operators.mutation(enfant1, self.prob_mutation)
                enfant2 = self.operators.mutation(enfant2, self.prob_mutation)
                
                # ✅ CORRECTION 8: Reconstruire les itinéraires après mutation
                self.solution_builder.construire_itineraires(enfant1)
                self.solution_builder.construire_itineraires(enfant2)
                
                # ✅ CORRECTION 9: Réparer les solutions
                self.solution_builder.reparer_solution(enfant1)
                self.solution_builder.reparer_solution(enfant2)

                # Ajouter à la nouvelle population
                nouvelle_population.extend([enfant1, enfant2])

            # Remplacer l'ancienne population (en gardant la taille exacte)
            population = nouvelle_population[:self.population_size]

        # ✅ CORRECTION 10: Affichage final détaillé
        logger.info("\n" + "="*60)
        logger.info("🏆 ALGORITHME TERMINÉ")
        logger.info("="*60)
        logger.info(f"Meilleur fitness: {best_fitness:.2f}")
        logger.info(f"Distance totale: {best_details.get('distance_totale', 0):.2f} km")
        logger.info(f"Durée totale: {best_details.get('duree_totale', 0):.1f} min")
        logger.info(f"Minibus utilisés: {best_details.get('minibus_utilises', 0)}")
        logger.info(f"Violations: {best_details.get('violations_capacite', 0) + best_details.get('violations_ordre', 0)}")
        logger.info("="*60)

        return best_solution, best_details