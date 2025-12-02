# app/algorithms/genetic_algorithm.py

import random
from typing import List, Tuple
from .solution import Solution
from .fitness import FitnessCalculator
from .operateur import GeneticOperators
from .solution_builder import SolutionBuilder
from ..internal.osrm_engine import  get_cost_matrices
from ..database.crud import get_all_minibus,get_all_reservations,get_all_stations

class GeneticAlgorithm:
    def __init__(
        self,
        reservations,
        minibus,
        stations_dict,
        matrice_distances,
        matrice_durees,
        population_size: int = 10,
        generations: int = 10,
        prob_croisement: float = 0.8,
        prob_mutation: float = 0.15,
        tournament_size: int = 3
    ):
        self.reservations = reservations
        self.minibus = minibus
        self.stations_dict = stations_dict
        self.matrice_distances = matrice_distances
        self.matrice_durees = matrice_durees
        self.population_size = population_size
        self.generations = generations
        self.prob_croisement = prob_croisement
        self.prob_mutation = prob_mutation
        self.tournament_size = tournament_size

        self.solution_builder = SolutionBuilder(
            matrice_distances, matrice_durees, stations_dict
        )
        self.operators = GeneticOperators(matrice_distances)
        self.fitness_calculator = FitnessCalculator(
            matrice_distances, matrice_durees, stations_dict
        )

    def run(self) -> Tuple[Solution, dict]:
        """Exécute l'algorithme génétique et retourne la meilleure solution"""
        # 1️⃣ Générer population initiale
        population: List[Solution] = self.solution_builder.generer_population_initiale(
            self.reservations, self.minibus, self.population_size
        )

        best_solution = None
        best_fitness = float('inf')
        best_details = {}

        # 2️⃣ Boucle sur les générations
        for gen in range(self.generations):
            # Calculer le fitness de chaque solution
            fitness_scores = []
            for sol in population:
                fitness, _ = self.fitness_calculator.calculer_fitness(sol)
                fitness_scores.append(fitness)

                # Mettre à jour la meilleure solution globale
                if fitness < best_fitness:
                    best_fitness = fitness
                    best_solution = sol.copy()
                    best_details = _

            # Créer une nouvelle population
            nouvelle_population = []

            while len(nouvelle_population) < self.population_size:
                # Sélection par tournoi
                parent1 = self.operators.selection_tournoi(population, fitness_scores, self.tournament_size)
                parent2 = self.operators.selection_tournoi(population, fitness_scores, self.tournament_size)

                # Croisement
                enfant1, enfant2 = self.operators.croisement_ordonne(parent1, parent2, self.prob_croisement)

                # Mutation
                enfant1 = self.operators.mutation(enfant1, self.prob_mutation)
                enfant2 = self.operators.mutation(enfant2, self.prob_mutation)

                # Ajouter à la nouvelle population
                nouvelle_population.extend([enfant1, enfant2])

            # Remplacer l'ancienne population
            population = nouvelle_population[:self.population_size]

            print(f"Generation {gen+1}/{self.generations} - Meilleur fitness: {best_fitness}")

        return best_solution, best_details
