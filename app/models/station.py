import psycopg2
from sqlalchemy import create_all_engines, create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
import logging

# Configuration de la base de données
DB_URL = "postgresql://minibus_user:minibus_user@localhost/minibus_db"

class Database:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # 1. Pour l'autre partie (SQLAlchemy / Relationnel)
        self.engine = create_engine(DB_URL)
        self.SessionLocal = scoped_session(sessionmaker(bind=self.engine))
        
    # 2. Ta partie (Connexion brute pour l'IA)
    def get_connection(self):
        """Ta méthode pour l'IA et les dataframes"""
        try:
            return psycopg2.connect("dbname=minibus_db user=minibus_user password=minibus_user host=localhost")
        except Exception as e:
            self.logger.error(f"Erreur connexion Psycopg2: {e}")
            return None

    def test_connection(self):
        """Vérifie si la DB répond"""
        try:
            conn = self.get_connection()
            if conn:
                conn.close()
                return True
            return False
        except:
            return False

    def close_all_connections(self):
        self.engine.dispose()

db = Database()