# database/connection.py
import psycopg2
from psycopg2 import pool
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseConnection:
    def __init__(self):
        self.pool = None
        self._initialize_connection()
    
    def _initialize_connection(self):
        """Initialise la connexion à la base PostgreSQL"""
        try:
            self.pool = psycopg2.pool.SimpleConnectionPool(
                1,  # min connections
                20, # max connections
                # --- NOUVEAUX PARAMÈTRES CORRIGÉS ---
                # Nom d'utilisateur défini dans docker-compose
                user="minibus_user", 
                # Mot de passe défini dans docker-compose
                password="minibus_user", 
                # Nom du service Docker Compose (le conteneur DB)
                host="localhost",               
                # Port interne (standard pour PostgreSQL)
                port="5432", 
                # Nom de la base de données
                database="minibus_db",   
                # ------------------------------------
               
                #user="postgres",
                #password="imanati20",  
                #host="localhost",
                #port="5432",
                #database="transport_db",
                
                client_encoding='utf-8'
            )
            logger.info(" Connexion à PostgreSQL réussie")
        except Exception as e:
            logger.error(f" Erreur de connexion à PostgreSQL : {e}")
            raise

    def get_connection(self):
        """Obtient une connexion du pool"""
        if self.pool:
            return self.pool.getconn()
        else:
            raise Exception("Pool de connexion non initialisé")
    
    def release_connection(self, connection):
        """Libère une connexion dans le pool"""
        if self.pool and connection:
            self.pool.putconn(connection)
    
    def close_all_connections(self):
        """Ferme toutes les connexions du pool"""
        if self.pool:
            self.pool.closeall()
            logger.info(" Toutes les connexions fermées")
    
    def test_connection(self):
        """Teste la connexion à la base"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            cursor.close()
            self.release_connection(conn)
            logger.info(f" Test connexion réussi - PostgreSQL: {version[0]}")
            return True
        except Exception as e:
            logger.error(f" Test connexion échoué: {e}")
            return False

# Instance globale de la base de données
db = DatabaseConnection()