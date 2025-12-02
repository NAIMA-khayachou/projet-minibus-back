"""
Algorithme Génétique pour l'optimisation des trajets de minibus - Marrakech
Intégration avec OSRM pour calcul de distances réelles
Adapté à la structure de la BD (reservations, minibus, stations)
"""

import random
import math
import json
import requests
from copy import deepcopy
from typing import List, Tuple, Optional
from flask import Flask, request, jsonify
import sys
sys.stdout.reconfigure(encoding='utf-8')

app = Flask(__name__)

# ============================================================================
# CONFIGURATION OSRM
# ============================================================================

OSRM_BASE_URL = "http://localhost:5000"  # À adapter selon votre config
OSRM_TIMEOUT = 10
OSRM_PROFILE = "driving"

# ============================================================================
# FONCTIONS OSRM - CALCUL DE DISTANCES RÉELLES
# ============================================================================

def get_cost_matrices(points: List[Tuple[float, float]]) -> Tuple[Optional[List[List[float]]], Optional[List[List[float]]]]:
    """
    Génère les matrices de temps et distance via OSRM
    
    Args:
        points: Liste de coordonnées [(lon, lat), ...]
        
    Returns:
        Tuple (matrice_temps_secondes, matrice_distance_metres) ou (None, None)
    """
    if not points:
        return ([], [])
    
    # Format OSRM : lon,lat;lon,lat;...
    coordinates_str = ";".join([f"{lon},{lat}" for lon, lat in points])
    url = f"{OSRM_BASE_URL}/table/v1/{OSRM_PROFILE}/{coordinates_str}?annotations=duration,distance"
    
    try:
        response = requests.get(url, timeout=OSRM_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        
        matrice_temps = data.get('durations')
        matrice_distance = data.get('distances')
        
        if matrice_temps and matrice_distance:
            return (matrice_temps, matrice_distance)
        else:
            print(f"⚠️  OSRM: Matrices manquantes. Code: {data.get('code')}")
            return (None, None)
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur OSRM: {e}")
        return (None, None)

def distance_haversine(coord1, coord2):
    """
    Calcul de distance Haversine (fallback si OSRM indisponible)
    
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
    """Estime le temps de trajet en minutes"""
    return (distance_km / vitesse_moyenne) * 60

# ============================================================================
# CLASSE SOLUTION (Chromosome)
# ============================================================================

class Solution:
    """
    Représente une solution au problème (un chromosome)
    Adapté à la structure BD: reservations + minibus
    """
    
    def __init__(self, reservations, minibus, use_osrm=True):
        self.reservations = reservations
        self.minibus = minibus
        self.trajets = [[] for _ in minibus]  # Liste de trajets par bus
        self.fitness = None
        self.use_osrm = use_osrm
        self.matrice_distance = None
        self.matrice_temps = None
    
    def preparer_matrices_osrm(self):
        """
        Prépare les matrices de distance/temps via OSRM
        Collecte tous les points uniques (pickup + dropoff)
        """
        if not self.use_osrm:
            return
        
        # Collecter tous les points uniques
        points_dict = {}  # {station_id: (lon, lat)}
        
        for res in self.reservations:
            pickup_id = res['pickup_station_id']
            dropoff_id = res['dropoff_station_id']
            
            if pickup_id not in points_dict:
                points_dict[pickup_id] = (
                    res['pickup_location']['lon'],
                    res['pickup_location']['lat']
                )
            
            if dropoff_id not in points_dict:
                points_dict[dropoff_id] = (
                    res['dropoff_location']['lon'],
                    res['dropoff_location']['lat']
                )
        
        # Ajouter positions initiales des bus
        for bus in self.minibus:
            bus_id = f"bus_{bus['id']}"
            if bus_id not in points_dict:
                points_dict[bus_id] = (
                    bus['position_initiale']['lon'],
                    bus['position_initiale']['lat']
                )
        
        # Créer la liste de points ordonnée
        self.station_ids = list(points_dict.keys())
        points_list = [points_dict[sid] for sid in self.station_ids]
        
        # Appeler OSRM
        matrice_temps, matrice_distance = get_cost_matrices(points_list)
        
        if matrice_temps and matrice_distance:
            # Convertir secondes -> minutes, mètres -> km
            self.matrice_temps = [[t/60 for t in row] for row in matrice_temps]
            self.matrice_distance = [[d/1000 for d in row] for row in matrice_distance]
        else:
            print("⚠️  OSRM non disponible, utilisation de Haversine")
            self.use_osrm = False
    
    def get_distance(self, coord1, coord2):
        """Obtient la distance entre deux coordonnées (OSRM ou Haversine)"""
        if self.use_osrm and self.matrice_distance:
            # Trouver les indices dans la matrice
            # (Implémentation simplifiée, à améliorer pour production)
            return distance_haversine(coord1, coord2)
        else:
            return distance_haversine(coord1, coord2)
    
    def calculer_fitness(self):
        """
        Évalue la qualité de la solution
        Objectifs: minimiser distance + pénalités contraintes
        """
        distance_totale = 0
        penalites = 0
        
        for bus_id, trajet in enumerate(self.trajets):
            if not trajet:
                continue
            
            bus = self.minibus[bus_id]
            capacite = bus['capacity']
            position = bus['position_initiale']
            charge_actuelle = 0
            
            for reservation_id in trajet:
                reservation = self.reservations[reservation_id]
                
                # Distance vers le pickup
                dist_pickup = self.get_distance(position, reservation['pickup_location'])
                distance_totale += dist_pickup
                
                # Distance du trajet passager
                dist_trajet = self.get_distance(
                    reservation['pickup_location'],
                    reservation['dropoff_location']
                )
                distance_totale += dist_trajet
                
                # Vérifier capacité
                charge_actuelle += reservation['number_of_people']
                if charge_actuelle > capacite:
                    penalites += 2000  # Pénalité dépassement capacité
                
                # Mettre à jour position
                position = reservation['dropoff_location']
        
        # Pénalité pour réservations non assignées
        reservations_assignees = set()
        for trajet in self.trajets:
            reservations_assignees.update(trajet)
        
        non_assignees = len(self.reservations) - len(reservations_assignees)
        penalites += non_assignees * 10000
        
        self.fitness = distance_totale + penalites
        return self.fitness
    
    def est_valide(self):
        """Vérifie si la solution respecte les contraintes"""
        toutes_reservations = []
        for trajet in self.trajets:
            toutes_reservations.extend(trajet)
        
        return len(toutes_reservations) == len(set(toutes_reservations))

# ============================================================================
# CLASSE ALGORITHME GÉNÉTIQUE
# ============================================================================

class AlgorithmeGenetique:
    """
    Implémentation AG pour optimisation de trajets minibus Marrakech
    """
    
    def __init__(self, taille_population=50, nb_generations=100,
                 taux_mutation=0.15, taux_croisement=0.8, use_osrm=True):
        self.taille_population = taille_population
        self.nb_generations = nb_generations
        self.taux_mutation = taux_mutation
        self.taux_croisement = taux_croisement
        self.use_osrm = use_osrm
        self.meilleure_solution = None
        self.historique_fitness = []
    
    def generer_population_initiale(self, reservations, minibus):
        """Crée une population initiale de solutions aléatoires"""
        population = []
        
        for _ in range(self.taille_population):
            solution = Solution(reservations, minibus, self.use_osrm)
            
            # Préparer les matrices OSRM une seule fois
            if self.use_osrm and not solution.matrice_distance:
                solution.preparer_matrices_osrm()
            
            # Assigner aléatoirement les réservations aux bus
            reservations_melangees = list(range(len(reservations)))
            random.shuffle(reservations_melangees)
            
            for res_id in reservations_melangees:
                bus_id = random.randint(0, len(minibus) - 1)
                solution.trajets[bus_id].append(res_id)
            
            solution.calculer_fitness()
            population.append(solution)
        
        return population
    
    def selection_tournoi(self, population, taille_tournoi=3):
        """Sélectionne un individu par tournoi"""
        participants = random.sample(population, taille_tournoi)
        return min(participants, key=lambda x: x.fitness)
    
    def croisement(self, parent1, parent2):
        """Croisement entre deux solutions"""
        if random.random() > self.taux_croisement:
            return deepcopy(parent1)
        
        enfant = Solution(parent1.reservations, parent1.minibus, self.use_osrm)
        enfant.matrice_distance = parent1.matrice_distance
        enfant.matrice_temps = parent1.matrice_temps
        
        # Pour chaque bus, mélanger les trajets des parents
        for bus_id in range(len(parent1.minibus)):
            trajet1 = parent1.trajets[bus_id]
            trajet2 = parent2.trajets[bus_id]
            
            if random.random() < 0.5 and trajet1:
                enfant.trajets[bus_id] = trajet1.copy()
            elif trajet2:
                enfant.trajets[bus_id] = trajet2.copy()
        
        enfant = self.reparer_solution(enfant)
        return enfant
    
    def mutation(self, solution):
        """Mutation: échange de réservations entre bus"""
        if random.random() > self.taux_mutation:
            return solution
        
        type_mutation = random.choice(['swap_bus', 'swap_ordre', 'reassign'])
        
        if type_mutation == 'swap_bus' and len(solution.minibus) > 1:
            bus1, bus2 = random.sample(range(len(solution.minibus)), 2)
            if solution.trajets[bus1] and solution.trajets[bus2]:
                idx1 = random.randint(0, len(solution.trajets[bus1]) - 1)
                idx2 = random.randint(0, len(solution.trajets[bus2]) - 1)
                
                solution.trajets[bus1][idx1], solution.trajets[bus2][idx2] = \
                    solution.trajets[bus2][idx2], solution.trajets[bus1][idx1]
        
        elif type_mutation == 'swap_ordre':
            bus_id = random.randint(0, len(solution.minibus) - 1)
            if len(solution.trajets[bus_id]) > 1:
                idx1, idx2 = random.sample(range(len(solution.trajets[bus_id])), 2)
                solution.trajets[bus_id][idx1], solution.trajets[bus_id][idx2] = \
                    solution.trajets[bus_id][idx2], solution.trajets[bus_id][idx1]
        
        elif type_mutation == 'reassign':
            bus_depart = random.randint(0, len(solution.minibus) - 1)
            if solution.trajets[bus_depart]:
                bus_arrivee = random.randint(0, len(solution.minibus) - 1)
                idx = random.randint(0, len(solution.trajets[bus_depart]) - 1)
                reservation = solution.trajets[bus_depart].pop(idx)
                solution.trajets[bus_arrivee].append(reservation)
        
        return solution
    
    def reparer_solution(self, solution):
        """Répare une solution invalide"""
        assignees = set()
        for trajet in solution.trajets:
            assignees.update(trajet)
        
        toutes_reservations = set(range(len(solution.reservations)))
        manquantes = toutes_reservations - assignees
        
        for res_id in manquantes:
            bus_id = random.randint(0, len(solution.minibus) - 1)
            solution.trajets[bus_id].append(res_id)
        
        for bus_id in range(len(solution.trajets)):
            solution.trajets[bus_id] = list(set(solution.trajets[bus_id]))
        
        return solution
    
    def optimiser(self, reservations, minibus, verbose=True):
        """Boucle principale de l'algorithme génétique"""
        if verbose:
            print(f"🧬 Démarrage AG - Marrakech")
            print(f"   {len(reservations)} réservations, {len(minibus)} minibus")
            print(f"   Population: {self.taille_population}, Générations: {self.nb_generations}")
            print(f"   OSRM: {'Activé' if self.use_osrm else 'Désactivé (Haversine)'}")
        
        population = self.generer_population_initiale(reservations, minibus)
        
        for generation in range(self.nb_generations):
            population.sort(key=lambda x: x.fitness)
            
            if self.meilleure_solution is None or population[0].fitness < self.meilleure_solution.fitness:
                self.meilleure_solution = deepcopy(population[0])
            
            self.historique_fitness.append(population[0].fitness)
            
            if verbose and generation % 10 == 0:
                print(f"   Gen {generation}: Fitness = {population[0].fitness:.2f}")
            
            nouvelle_population = []
            elite_size = max(1, self.taille_population // 10)
            nouvelle_population.extend(deepcopy(population[:elite_size]))
            
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
        """Formate la solution pour l'API (compatible avec la BD)"""
        resultat = {
            "fitness": round(solution.fitness, 2),
            "distance_totale_km": 0,
            "temps_total_min": 0,
            "nb_bus_utilises": 0,
            "trajets": []
        }
        
        for bus_id, trajet in enumerate(solution.trajets):
            if not trajet:
                continue
            
            resultat["nb_bus_utilises"] += 1
            bus = solution.minibus[bus_id]
            arrets = []
            position = bus['position_initiale']
            distance_trajet = 0
            temps_trajet = 0
            charge_actuelle = 0
            
            for res_id in trajet:
                reservation = solution.reservations[res_id]
                
                # Pickup
                dist = solution.get_distance(position, reservation['pickup_location'])
                distance_trajet += dist
                temps_trajet += calculer_temps_trajet(dist)
                charge_actuelle += reservation['number_of_people']
                
                arrets.append({
                    "ordre": len(arrets) + 1,
                    "type": "pickup",
                    "reservation_id": reservation['id'],
                    "station_id": reservation['pickup_station_id'],
                    "station_name": reservation['pickup_station_name'],
                    "position": reservation['pickup_location'],
                    "nb_passagers": reservation['number_of_people'],
                    "charge_bus_apres": charge_actuelle
                })
                
                # Dropoff
                dist = solution.get_distance(reservation['pickup_location'], reservation['dropoff_location'])
                distance_trajet += dist
                temps_trajet += calculer_temps_trajet(dist)
                charge_actuelle -= reservation['number_of_people']
                
                arrets.append({
                    "ordre": len(arrets) + 1,
                    "type": "dropoff",
                    "reservation_id": reservation['id'],
                    "station_id": reservation['dropoff_station_id'],
                    "station_name": reservation['dropoff_station_name'],
                    "position": reservation['dropoff_location'],
                    "nb_passagers": reservation['number_of_people'],
                    "charge_bus_apres": charge_actuelle
                })
                
                position = reservation['dropoff_location']
            
            resultat["trajets"].append({
                "bus_id": bus['id'],
                "license_plate": bus['license_plate'],
                "capacite": bus['capacity'],
                "nb_arrets": len(arrets),
                "arrets": arrets,
                "distance_km": round(distance_trajet, 2),
                "temps_estime_min": round(temps_trajet, 0)
            })
            
            resultat["distance_totale_km"] += distance_trajet
            resultat["temps_total_min"] += temps_trajet
        
        resultat["distance_totale_km"] = round(resultat["distance_totale_km"], 2)
        resultat["temps_total_min"] = round(resultat["temps_total_min"], 0)
        
        # Statistiques
        resultat["statistiques"] = {
            "reservations_traitees": sum(len(t) for t in solution.trajets),
            "reservations_totales": len(solution.reservations),
            "taux_satisfaction": round((sum(len(t) for t in solution.trajets) / len(solution.reservations)) * 100, 1) if solution.reservations else 0
        }
        
        return resultat

# ============================================================================
# API FLASK
# ============================================================================

@app.route('/optimize', methods=['POST'])
def optimize():
    """
    Endpoint principal pour l'optimisation
    Compatible avec la structure BD Marrakech
    """
    try:
        data = request.json
        
        reservations = data.get('reservations', [])
        minibus = data.get('minibus', [])
        parametres = data.get('parametres', {})
        
        if not reservations or not minibus:
            return jsonify({"error": "Réservations et minibus requis"}), 400
        
        ag = AlgorithmeGenetique(
            taille_population=parametres.get('taille_population', 50),
            nb_generations=parametres.get('nb_generations', 100),
            taux_mutation=parametres.get('taux_mutation', 0.15),
            taux_croisement=parametres.get('taux_croisement', 0.8),
            use_osrm=parametres.get('use_osrm', True)
        )
        
        solution = ag.optimiser(reservations, minibus, verbose=False)
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
    """Endpoint de santé"""
    return jsonify({
        "status": "ok",
        "service": "AG Optimisation Marrakech",
        "osrm_available": test_osrm_connection()
    })

def test_osrm_connection():
    """Test la connexion OSRM"""
    try:
        response = requests.get(f"{OSRM_BASE_URL}/health", timeout=2)
        return response.status_code == 200
    except:
        return False

# ============================================================================
# TEST LOCAL
# ============================================================================

if __name__ == "__main__":
    print("🧪 Test de l'algorithme génétique - Marrakech\n")
    
    # Charger données de test
    try:
        with open('test_data_bd_reelle.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            reservations = data['reservations']
            minibus = data['minibus']
            print(f"📂 Chargement: {len(reservations)} réservations, {len(minibus)} minibus")
    except FileNotFoundError:
        print("⚠️  Fichier test_data_bd_reelle.json non trouvé")
        print("   Exécutez d'abord: python data_simulation.py\n")
        exit(1)
    
    # Tester OSRM
    print(f"🔌 Test OSRM sur {OSRM_BASE_URL}...")
    use_osrm = test_osrm_connection()
    if use_osrm:
        print("   ✅ OSRM disponible")
    else:
        print("   ⚠️  OSRM non disponible, utilisation de Haversine")
    print()
    
    # Créer et exécuter l'AG
    ag = AlgorithmeGenetique(
        taille_population=30,
        nb_generations=50,
        use_osrm=use_osrm
    )
    solution = ag.optimiser(reservations, minibus)
    
    # Afficher résultats
    resultat = ag.formater_resultat(solution)
    print("\n" + "="*50)
    print("📊 RÉSULTATS:")
    print("="*50)
    print(json.dumps(resultat, indent=2, ensure_ascii=False))
    
    print("\n🚀 Pour lancer l'API Flask:")
    print("   python ag.py --api")
    
    # Lancer l'API si demandé
    import sys
    if '--api' in sys.argv:
        print(f"\n🌐 Lancement de l'API sur http://localhost:5001")
        app.run(debug=True, port=5001)