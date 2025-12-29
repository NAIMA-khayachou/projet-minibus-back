from app.database.connection import db
import bcrypt
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_password_hash(password):
    # Génère un salt et hache le mot de passe
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def init_users():
    """Crée la table users et ajoute les utilisateurs par défaut"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # 0. Nettoyage (DROP) pour être sûr du schéma
        logger.info("🗑️ Suppression de l'ancienne table users...")
        cursor.execute("DROP TABLE IF EXISTS users CASCADE;")
        
        # 1. Création de la table users
        logger.info("🛠️ Création de la table users...")
        cursor.execute("""
            CREATE TABLE users (
                id SERIAL PRIMARY KEY,
                email VARCHAR(100) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                role VARCHAR(20) NOT NULL,
                nom VARCHAR(50),
                prenom VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # 2. Préparation des utilisateurs de test
        admin_pass = get_password_hash("admin123")
        chauffeur_pass = get_password_hash("chauffeur123")
        
        users = [
            ("admin@test.com", admin_pass, "admin", "Maroua", "maroua"),
            ("chauffeur@test.com", chauffeur_pass, "chauffeur", "Chauffeur", "Chauffeur")
        ]
        
        # 3. Insertion des utilisateurs
        logger.info("👤 Ajout des utilisateurs par défaut...")
        for email, pwd, role, nom, prenom in users:
            cursor.execute("""
                INSERT INTO users (email, password, role, nom, prenom)
                VALUES (%s, %s, %s, %s, %s);
            """, (email, pwd, role, nom, prenom))
            logger.info(f"✅ Utilisateur ajouté: {email}")
        
        conn.commit()
        cursor.close()
        db.release_connection(conn)
        logger.info("✨ Initialisation des utilisateurs terminée avec succès!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'initialisation des utilisateurs: {e}")
        return False

if __name__ == "__main__":
    init_users()
