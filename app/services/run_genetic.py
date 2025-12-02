#!/usr/bin/env python3
"""
Script d'exécution pour l'algorithme génétique.
Usage (depuis la racine du projet) :
    python -m app.services.run_genetic
ou
    python -u -m app.services.run_genetic

Ce script :
- créé une instance de `GeneticAlgorithm`
- charge les données depuis la DB
- construit les matrices de coûts via OSRM
- lance l'optimisation et affiche la solution
"""
import logging
import json
import sys
from typing import Any

from app.core.config import settings
from app.services.genetic_algorithm import GeneticAlgorithm

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main() -> int:
    logger.info("Démarrage du script d'optimisation génétique")

    ga = GeneticAlgorithm()

    try:
        logger.info("Chargement des données depuis la base...")
        ga.load_data()

        logger.info("Construction des matrices de coûts via OSRM...")
        ga.build_cost_matrices()

        logger.info("Lancement de l'optimisation...")
        best = ga.optimize()

        logger.info("Formatage de la solution finale...")
        solution = ga.format_solution(best)

        # Afficher la solution en JSON lisible
        print(json.dumps(solution, ensure_ascii=False, indent=2))

        logger.info("Script terminé avec succès")
        return 0

    except Exception as exc:
        logger.exception("Erreur lors de l'exécution de l'algorithme génétique: %s", exc)
        return 1


if __name__ == '__main__':
    sys.exit(main())
