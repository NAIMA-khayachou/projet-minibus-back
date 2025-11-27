"""
Algorithme Génétique pour l'optimisation des trajets de minibus
Résout le problème de Vehicle Routing Problem (VRP) avec contraintes
"""

import random
import math
import json
from copy import deepcopy
from flask import Flask, request, jsonify
import sys
sys.stdout.reconfigure(encoding='utf-8')

app = Flask(__name__)

# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================

def distance_haversine(coord1, coord2):
    """
    Calcule la distance entre deux points GPS en km (formule de Haversine)
    
    Args:
        coord1: {"lat": float, "lon": float}
        coord2: {"lat": float, "lon": float}
    
    Returns:
        Distance en kilomètres
    """
    R = 6371  # Rayon de la Terre en km
    
    lat1, lon1 = math.radians(coord1['lat']), math.radians(coord1['lon'])
    lat2, lon2 = math.radians(coord2['lat']), math.radians(coord2['lon'])
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c

def calculer_temps_trajet(distance_km, vitesse_moyenne=30):
    """Estime le temps de trajet en minutes (vitesse moyenne en km/h)"""
    return (distance_km / vitesse_moyenne) * 60

# ============================================================================
# CLASSE SOLUTION (Chromosome)
# ============================================================================

class Solution:
    """
    Représente une solution au problème (un chromosome)
    Structure: liste de trajets, un par bus
    """
    
    def __init__(self, demandes, bus):
        self.demandes = demandes
        self.bus = bus
        self.trajets = [[] for _ in bus]  # Liste de listes (un trajet par bus)
        self.fitness = None
    
    def calculer_fitness(self):
        """
        Évalue la qualité de la solution
        Objectifs: minimiser distance totale + pénalités pour contraintes violées
        """
        distance_totale = 0
        penalites = 0
        
        for bus_id, trajet in enumerate(self.trajets):
            if not trajet:
                continue
            
            bus = self.bus[bus_id]
            capacite = bus['capacite']
            position = bus['position_initiale']
            charge_actuelle = 0
            
            for demande_id in trajet:
                demande = self.demandes[demande_id]
                
                # Distance vers le point de départ
                dist_depart = distance_haversine(position, demande['depart'])
                distance_totale += dist_depart
                
                # Distance du trajet du passager
                dist_trajet = distance_haversine(demande['depart'], demande['arrivee'])
                distance_totale += dist_trajet
                
                # Vérifier capacité
                charge_actuelle += demande['nb_passagers']
                if charge_actuelle > capacite:
                    penalites += 1000  # Grosse pénalité pour dépassement capacité
                
                # Mettre à jour position
                position = demande['arrivee']
        
        # Pénalité pour demandes non assignées
        demandes_assignees = set()
        for trajet in self.trajets:
            demandes_assignees.update(trajet)
        
        demandes_non_assignees = len(self.demandes) - len(demandes_assignees)
        penalites += demandes_non_assignees * 5000
        
        self.fitness = distance_totale + penalites
        return self.fitness
    
    def est_valide(self):
        """Vérifie si la solution respecte les contraintes basiques"""
        # Vérifier que chaque demande est assignée une seule fois
        toutes_demandes = []
        for trajet in self.trajets:
            toutes_demandes.extend(trajet)
        
        return len(toutes_demandes) == len(set(toutes_demandes))

# ============================================================================
# CLASSE ALGORITHME GÉNÉTIQUE
# ============================================================================

class AlgorithmeGenetique:
    """
    Implémentation de l'algorithme génétique pour optimisation de trajets
    """
    
    def __init__(self, taille_population=50, nb_generations=100, 
                 taux_mutation=0.15, taux_croisement=0.8):
        self.taille_population = taille_population
        self.nb_generations = nb_generations
        self.taux_mutation = taux_mutation
        self.taux_croisement = taux_croisement
        self.meilleure_solution = None
        self.historique_fitness = []
    
    def generer_population_initiale(self, demandes, bus):
        """Crée une population initiale de solutions aléatoires"""
        population = []
        
        for _ in range(self.taille_population):
            solution = Solution(demandes, bus)
            
            # Assigner aléatoirement les demandes aux bus
            demandes_melangees = list(range(len(demandes)))
            random.shuffle(demandes_melangees)
            
            for demande_id in demandes_melangees:
                bus_id = random.randint(0, len(bus) - 1)
                solution.trajets[bus_id].append(demande_id)
            
            solution.calculer_fitness()
            population.append(solution)
        
        return population
    
    def selection_tournoi(self, population, taille_tournoi=3):
        """Sélectionne un individu par tournoi"""
        participants = random.sample(population, taille_tournoi)
        return min(participants, key=lambda x: x.fitness)
    
    def croisement(self, parent1, parent2):
        """
        Croisement entre deux solutions (Order Crossover adapté)
        """
        if random.random() > self.taux_croisement:
            return deepcopy(parent1)
        
        enfant = Solution(parent1.demandes, parent1.bus)
        
        # Pour chaque bus, mélanger les trajets des parents
        for bus_id in range(len(parent1.bus)):
            trajet1 = parent1.trajets[bus_id]
            trajet2 = parent2.trajets[bus_id]
            
            if not trajet1 and not trajet2:
                continue
            
            # Prendre aléatoirement du parent 1 ou 2
            if random.random() < 0.5 and trajet1:
                enfant.trajets[bus_id] = trajet1.copy()
            elif trajet2:
                enfant.trajets[bus_id] = trajet2.copy()
        
        # S'assurer que toutes les demandes sont assignées une seule fois
        enfant = self.reparer_solution(enfant)
        return enfant
    
    def mutation(self, solution):
        """
        Mutation: échange de demandes entre bus ou réordonnancement
        """
        if random.random() > self.taux_mutation:
            return solution
        
        type_mutation = random.choice(['swap_bus', 'swap_ordre', 'reassign'])
        
        if type_mutation == 'swap_bus' and len(solution.bus) > 1:
            # Échanger une demande entre deux bus
            bus1, bus2 = random.sample(range(len(solution.bus)), 2)
            if solution.trajets[bus1] and solution.trajets[bus2]:
                idx1 = random.randint(0, len(solution.trajets[bus1]) - 1)
                idx2 = random.randint(0, len(solution.trajets[bus2]) - 1)
                
                solution.trajets[bus1][idx1], solution.trajets[bus2][idx2] = \
                    solution.trajets[bus2][idx2], solution.trajets[bus1][idx1]
        
        elif type_mutation == 'swap_ordre':
            # Inverser l'ordre de deux demandes dans un même bus
            bus_id = random.randint(0, len(solution.bus) - 1)
            if len(solution.trajets[bus_id]) > 1:
                idx1, idx2 = random.sample(range(len(solution.trajets[bus_id])), 2)
                solution.trajets[bus_id][idx1], solution.trajets[bus_id][idx2] = \
                    solution.trajets[bus_id][idx2], solution.trajets[bus_id][idx1]
        
        elif type_mutation == 'reassign':
            # Réassigner une demande à un autre bus
            bus_depart = random.randint(0, len(solution.bus) - 1)
            if solution.trajets[bus_depart]:
                bus_arrivee = random.randint(0, len(solution.bus) - 1)
                idx = random.randint(0, len(solution.trajets[bus_depart]) - 1)
                demande = solution.trajets[bus_depart].pop(idx)
                solution.trajets[bus_arrivee].append(demande)
        
        return solution
    
    def reparer_solution(self, solution):
        """Répare une solution invalide (demandes dupliquées ou manquantes)"""
        # Collecter toutes les demandes assignées
        assignees = set()
        for trajet in solution.trajets:
            assignees.update(trajet)
        
        # Trouver les demandes manquantes
        toutes_demandes = set(range(len(solution.demandes)))
        manquantes = toutes_demandes - assignees
        
        # Assigner les demandes manquantes aléatoirement
        for demande_id in manquantes:
            bus_id = random.randint(0, len(solution.bus) - 1)
            solution.trajets[bus_id].append(demande_id)
        
        # Enlever les doublons
        for bus_id in range(len(solution.trajets)):
            solution.trajets[bus_id] = list(set(solution.trajets[bus_id]))
        
        return solution
    
    def optimiser(self, demandes, bus, verbose=True):
        """
        Boucle principale de l'algorithme génétique
        
        Returns:
            Meilleure solution trouvée
        """
        if verbose:
            print(f"🧬 Démarrage AG: {len(demandes)} demandes, {len(bus)} bus")
            print(f"   Population: {self.taille_population}, Générations: {self.nb_generations}")
        
        # Générer population initiale
        population = self.generer_population_initiale(demandes, bus)
        
        # Évolution
        for generation in range(self.nb_generations):
            # Trier par fitness
            population.sort(key=lambda x: x.fitness)
            
            # Enregistrer la meilleure solution
            if self.meilleure_solution is None or population[0].fitness < self.meilleure_solution.fitness:
                self.meilleure_solution = deepcopy(population[0])
            
            self.historique_fitness.append(population[0].fitness)
            
            if verbose and generation % 10 == 0:
                print(f"   Génération {generation}: Fitness = {population[0].fitness:.2f}")
            
            # Créer nouvelle génération
            nouvelle_population = []
            
            # Élitisme: garder les 10% meilleurs
            elite_size = max(1, self.taille_population // 10)
            nouvelle_population.extend(deepcopy(population[:elite_size]))
            
            # Remplir le reste avec croisement et mutation
            while len(nouvelle_population) < self.taille_population:
                parent1 = self.selection_tournoi(population)
                parent2 = self.selection_tournoi(population)
                
                enfant = self.croisement(parent1, parent2)
                enfant = self.mutation(enfant)
                enfant.calculer_fitness()
                
                nouvelle_population.append(enfant)
            
            population = nouvelle_population
        
        if verbose:
            print(f"✅ Optimisation terminée!")
            print(f"   Meilleur fitness: {self.meilleure_solution.fitness:.2f}")
        
        return self.meilleure_solution
    
    def formater_resultat(self, solution):
        """Formate la solution pour l'API (JSON)"""
        resultat = {
            "fitness": solution.fitness,
            "distance_totale_km": 0,
            "trajets": []
        }
        
        for bus_id, trajet in enumerate(solution.trajets):
            if not trajet:
                continue
            
            bus = solution.bus[bus_id]
            arrets = []
            position = bus['position_initiale']
            distance_trajet = 0
            
            for demande_id in trajet:
                demande = solution.demandes[demande_id]
                
                # Point de départ
                dist = distance_haversine(position, demande['depart'])
                distance_trajet += dist
                
                arrets.append({
                    "type": "pickup",
                    "demande_id": demande['id'],
                    "position": demande['depart'],
                    "nb_passagers": demande['nb_passagers']
                })
                
                # Point d'arrivée
                dist = distance_haversine(demande['depart'], demande['arrivee'])
                distance_trajet += dist
                
                arrets.append({
                    "type": "dropoff",
                    "demande_id": demande['id'],
                    "position": demande['arrivee'],
                    "nb_passagers": demande['nb_passagers']
                })
                
                position = demande['arrivee']
            
            resultat["trajets"].append({
                "bus_id": bus['id'],
                "capacite": bus['capacite'],
                "arrets": arrets,
                "distance_km": round(distance_trajet, 2),
                "temps_estime_min": round(calculer_temps_trajet(distance_trajet), 0)
            })
            
            resultat["distance_totale_km"] += distance_trajet
        
        resultat["distance_totale_km"] = round(resultat["distance_totale_km"], 2)
        return resultat

# ============================================================================
# API FLASK
# ============================================================================

@app.route('/optimize', methods=['POST'])
def optimize():
    """
    Endpoint principal pour l'optimisation
    
    Input JSON:
    {
        "demandes": [...],
        "bus": [...],
        "parametres": {
            "taille_population": 50,
            "nb_generations": 100
        }
    }
    """
    try:
        data = request.json
        
        demandes = data.get('demandes', [])
        bus = data.get('bus', [])
        parametres = data.get('parametres', {})
        
        if not demandes or not bus:
            return jsonify({"error": "Demandes et bus requis"}), 400
        
        # Créer et lancer l'AG
        ag = AlgorithmeGenetique(
            taille_population=parametres.get('taille_population', 50),
            nb_generations=parametres.get('nb_generations', 100),
            taux_mutation=parametres.get('taux_mutation', 0.15),
            taux_croisement=parametres.get('taux_croisement', 0.8)
        )
        
        solution = ag.optimiser(demandes, bus, verbose=False)
        resultat = ag.formater_resultat(solution)
        
        return jsonify({
            "success": True,
            "resultat": resultat,
            "historique_fitness": ag.historique_fitness
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Endpoint de santé pour vérifier que l'API fonctionne"""
    return jsonify({"status": "ok", "service": "AG Optimisation"})

# ============================================================================
# TEST LOCAL
# ============================================================================

if __name__ == "__main__":
    # Test avec données simulées
    print("🧪 Test de l'algorithme génétique...\n")
    
    # Charger ou créer des données de test
    try:
        with open('test_data_petit.json', 'r') as f:
            data = json.load(f)
            demandes = data['demandes']
            bus = data['bus']
    except:
        print("⚠️  Fichier test_data_petit.json non trouvé")
        print("   Exécutez d'abord data_simulation.py\n")
        
        # Créer des données minimales pour le test
        demandes = [
            {"id": 1, "depart": {"lat": 33.5731, "lon": -7.5898}, 
             "arrivee": {"lat": 33.5891, "lon": -7.6031}, "nb_passagers": 2},
            {"id": 2, "depart": {"lat": 33.5800, "lon": -7.5950}, 
             "arrivee": {"lat": 33.5950, "lon": -7.6100}, "nb_passagers": 1},
        ]
        bus = [
            {"id": 1, "capacite": 8, "position_initiale": {"lat": 33.5731, "lon": -7.5898}}
        ]
    
    # Créer et exécuter l'AG
    ag = AlgorithmeGenetique(taille_population=30, nb_generations=50)
    solution = ag.optimiser(demandes, bus)
    
    # Afficher les résultats
    resultat = ag.formater_resultat(solution)
    print("\n📊 Résultats:")
    print(json.dumps(resultat, indent=2, ensure_ascii=False))
    
    print("\n🚀 Pour lancer l'API Flask:")
    print("   python ag.py --api")
    
    # Lancer l'API si demandé
    import sys
    if '--api' in sys.argv:
        print("\n🌐 Lancement de l'API sur http://localhost:5000")
        app.run(debug=True, port=5000)