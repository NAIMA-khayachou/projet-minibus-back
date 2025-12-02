# app/database/simple_graphs.py
import matplotlib.pyplot as plt
import pandas as pd
import sys
import os

# Configuration du chemin
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_all_stations, get_all_reservations, get_all_minibus

def create_graphs():
    """Crée des graphiques simples sans erreurs"""
    
    print("📊 Génération des graphiques...")
    
    try:
        # 1. GRAPHIQUE BARRES - Capacité des minibus
        minibus = get_all_minibus()
        df_bus = pd.DataFrame(minibus, columns=['id', 'capacity', 'plate', 'passengers', 'status', 'maintenance'])
        
        plt.figure(figsize=(10, 6))
        bars = plt.bar(range(len(df_bus)), df_bus['capacity'], color=['red', 'blue', 'green', 'orange', 'purple'])
        plt.title('CAPACITE DES MINIBUS', fontsize=14, fontweight='bold')
        plt.xlabel('Minibus')
        plt.ylabel('Nombre de places')
        plt.xticks(range(len(df_bus)), df_bus['plate'], rotation=45)
        plt.grid(axis='y', alpha=0.3)
        
        # Ajouter les valeurs sur les barres
        for i, bar in enumerate(bars):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                    f'{df_bus["capacity"][i]}', ha='center', va='bottom')
        
        plt.tight_layout()
        plt.show()

        # 2. GRAPHIQUE CAMEMBERT - Répartition des capacités
        plt.figure(figsize=(8, 8))
        capacity_counts = df_bus['capacity'].value_counts()
        plt.pie(capacity_counts.values, labels=[f'{cap} places' for cap in capacity_counts.index], 
                autopct='%1.1f%%', startangle=90)
        plt.title('REPARTITION DES CAPACITES', fontsize=14, fontweight='bold')
        plt.show()

        # 3. GRAPHIQUE SIMPLE - Réservations (sans conversion d'heure)
        reservations = get_all_reservations()
        df_res = pd.DataFrame(reservations, columns=['id', 'client_id', 'pickup', 'dropoff', 'people', 'time', 'status'])
        
        # Compter par nombre de personnes
        people_counts = df_res['people'].value_counts().sort_index()
        
        plt.figure(figsize=(10, 6))
        plt.bar(people_counts.index, people_counts.values, color='lightblue')
        plt.title('RESERVATIONS PAR NOMBRE DE PERSONNES', fontsize=14, fontweight='bold')
        plt.xlabel('Nombre de personnes')
        plt.ylabel('Nombre de réservations')
        plt.grid(axis='y', alpha=0.3)
        plt.tight_layout()
        plt.show()

        # 4. GRAPHIQUE STATISTIQUES SIMPLES
        stats_data = {
            'Type': ['Stations', 'Minibus', 'Reservations'],
            'Nombre': [len(get_all_stations()), len(get_all_minibus()), len(get_all_reservations())]
        }
        
        plt.figure(figsize=(8, 6))
        plt.bar(stats_data['Type'], stats_data['Nombre'], color=['red', 'blue', 'green'])
        plt.title('STATISTIQUES DE LA BASE', fontsize=14, fontweight='bold')
        plt.ylabel('Quantite')
        plt.grid(axis='y', alpha=0.3)
        
        # Ajouter les valeurs
        for i, v in enumerate(stats_data['Nombre']):
            plt.text(i, v + 0.1, str(v), ha='center', va='bottom')
        
        plt.tight_layout()
        plt.show()
        
        print("✅ Tous les graphiques generes avec succes!")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    create_graphs()