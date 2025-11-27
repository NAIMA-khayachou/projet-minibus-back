# database/init_database.py
from .connection import db
import os

def init_database():
    """Crée toutes les tables à partir du fichier SQL"""
    
    # Chemin vers votre fichier SQL
    sql_file_path = os.path.join(os.path.dirname(__file__), 'transport_db.sql')
    
    try:
        # Lire le fichier SQL
        with open(sql_file_path, 'r', encoding='utf-8') as file:
            sql_script = file.read()
        
        # Exécuter le script
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute(sql_script)
        conn.commit()
        cursor.close()
        db.release_connection(conn)
        
        print(" Base de données initialisée avec succès!")
        print(" Tables créées: stations, minibus, clients, reservations, optimized_routes")
        return True
        
    except FileNotFoundError:
        print(f" Fichier SQL non trouvé: {sql_file_path}")
        return False
    except Exception as e:
        print(f" Erreur lors de l'initialisation: {e}")
        return False

if __name__ == "__main__":
    init_database()