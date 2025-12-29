from app.database.connection import db
import bcrypt
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_users():
    """Crée un utilisateur admin par défaut pour le développement"""
    
    admin_email = "admin@test.com"
    admin_password = "admin123"
    
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Vérifier si l'utilisateur existe déjà
        cursor.execute("SELECT id FROM users WHERE email = %s;", (admin_email,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            logger.info(f"✅ L'utilisateur {admin_email} existe déjà (ID: {existing_user[0]})")
            return

        # Hasher le mot de passe
        hashed_password = bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Insérer l'utilisateur
        cursor.execute("""
            INSERT INTO users (email, password, role, nom, prenom) 
            VALUES (%s, %s, 'admin', 'Admin', 'System') 
            RETURNING id;
        """, (admin_email, hashed_password))
        
        user_id = cursor.fetchone()[0]
        conn.commit()
        
        logger.info(f"✅ Utilisateur admin créé avec succès!")
        logger.info(f"📧 Email: {admin_email}")
        logger.info(f"🔑 Mot de passe: {admin_password}")
        logger.info(f"🆔 ID: {user_id}")
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la création de l'utilisateur: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            db.release_connection(conn)

if __name__ == "__main__":
    seed_users()
