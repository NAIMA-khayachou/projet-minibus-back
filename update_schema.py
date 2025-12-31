from app.database.connection import db
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_schema():
    """Ajoute la colonne status à la table clients"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Vérifier si la colonne existe déjà
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='clients' AND column_name='status';
        """)
        
        if cursor.fetchone():
            logger.info("ℹ️ La colonne 'status' existe déjà dans la table 'clients'")
        else:
            logger.info("🛠 Ajout de la colonne 'status' à la table 'clients'...")
            cursor.execute("""
                ALTER TABLE clients 
                ADD COLUMN status VARCHAR(20) DEFAULT 'active';
            """)
            conn.commit()
            logger.info("✅ Colonne 'status' ajoutée avec succès")
            
        cursor.close()
        db.release_connection(conn)
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la mise à jour du schéma: {e}")

if __name__ == "__main__":
    update_schema()
