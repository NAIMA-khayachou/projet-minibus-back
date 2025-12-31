from app.database.connection import db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_data():
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        tables = ['stations', 'minibus', 'clients', 'users']
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table};")
            count = cursor.fetchone()[0]
            print(f"Table '{table}': {count} entrées")
            
        cursor.close()
        db.release_connection(conn)
    except Exception as e:
        print(f"Erreur: {e}")

if __name__ == "__main__":
    check_data()
