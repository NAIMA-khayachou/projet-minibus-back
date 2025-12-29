from app.database.connection import db
import bcrypt
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_chauffeur():
    """Crée un utilisateur chauffeur pour le test"""
    
    email = "chauffeur@test.com"
    password = "chauffeur123"
    
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Vérifier si l'utilisateur existe déjà
        cursor.execute("SELECT id FROM users WHERE email = %s;", (email,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            logger.info(f"✅ L'utilisateur {email} existe déjà (ID: {existing_user[0]})")
            return

        # Hasher le mot de passe
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Insérer l'utilisateur
        cursor.execute("""
            INSERT INTO users (email, password, role, nom, prenom) 
            VALUES (%s, %s, 'chauffeur', 'Chauffeur', 'Test') 
            RETURNING id;
        """, (email, hashed_password))
        
        user_id = cursor.fetchone()[0]
        conn.commit()
        
        logger.info(f"✅ Utilisateur chauffeur créé avec succès!")
        logger.info(f"📧 Email: {email}")
        logger.info(f"🔑 Mot de passe: {password}")
        logger.info(f"🆔 ID: {user_id}")
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la création du chauffeur: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            db.release_connection(conn)

if __name__ == "__main__":
    seed_chauffeur()
