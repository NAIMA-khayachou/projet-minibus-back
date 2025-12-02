# database/crud.py
from .connection import db
import logging

logger = logging.getLogger(__name__)

# ==================== AUTHENTIFICATION (Users) ====================

def authenticate_user(email, password):
    """Authentifie un admin ou chauffeur"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, email, role, created_at, last_login
            FROM users 
            WHERE email = %s AND password = %s;
        """, (email, password))
        user = cursor.fetchone()
        
        if user:
            # Mettre à jour last_login
            cursor.execute("""
                UPDATE users 
                SET last_login = CURRENT_TIMESTAMP 
                WHERE id = %s;
            """, (user[0],))
            conn.commit()
            
            columns = ['id', 'email', 'role', 'created_at', 'last_login']
            user_dict = dict(zip(columns, user))
            
            cursor.close()
            db.release_connection(conn)
            logger.info(f" Utilisateur authentifié: {email} ({user_dict['role']})")
            return user_dict
        
        cursor.close()
        db.release_connection(conn)
        return None
    except Exception as e:
        logger.error(f" Erreur authenticate_user: {e}")
        return None

def create_user(email, password, role='chauffeur'):
    """Crée un nouvel utilisateur (admin ou chauffeur)"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (email, password, role) 
            VALUES (%s, %s, %s) RETURNING id;
        """, (email, password, role))
        user_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        db.release_connection(conn)
        logger.info(f" Utilisateur créé avec ID: {user_id}, rôle: {role}")
        return user_id
    except Exception as e:
        logger.error(f" Erreur create_user: {e}")
        return None

def get_user_by_email(email):
    """Récupère un utilisateur par son email"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, email, role, created_at, last_login
            FROM users 
            WHERE email = %s;
        """, (email,))
        user = cursor.fetchone()
        cursor.close()
        db.release_connection(conn)
        
        if user:
            columns = ['id', 'email', 'role', 'created_at', 'last_login']
            return dict(zip(columns, user))
        return None
    except Exception as e:
        logger.error(f" Erreur get_user_by_email: {e}")
        return None

def get_all_users():
    """Récupère tous les utilisateurs (admin et chauffeurs)"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, email, role, created_at, last_login
            FROM users 
            ORDER BY role, email;
        """)
        users = cursor.fetchall()
        cursor.close()
        db.release_connection(conn)
        
        columns = ['id', 'email', 'role', 'created_at', 'last_login']
        return [dict(zip(columns, user)) for user in users]
    except Exception as e:
        logger.error(f" Erreur get_all_users: {e}")
        return []

def get_users_by_role(role):
    """Récupère tous les utilisateurs d'un rôle spécifique"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, email, role, created_at, last_login
            FROM users 
            WHERE role = %s
            ORDER BY email;
        """, (role,))
        users = cursor.fetchall()
        cursor.close()
        db.release_connection(conn)
        
        columns = ['id', 'email', 'role', 'created_at', 'last_login']
        return [dict(zip(columns, user)) for user in users]
    except Exception as e:
        logger.error(f" Erreur get_users_by_role: {e}")
        return []

def update_user_role(user_id, new_role):
    """Met à jour le rôle d'un utilisateur"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users 
            SET role = %s 
            WHERE id = %s 
            RETURNING id, email, role;
        """, (new_role, user_id))
        result = cursor.fetchone()
        conn.commit()
        cursor.close()
        db.release_connection(conn)
        
        if result:
            columns = ['id', 'email', 'role']
            logger.info(f" Rôle mis à jour pour user ID: {user_id} -> {new_role}")
            return dict(zip(columns, result))
        return None
    except Exception as e:
        logger.error(f" Erreur update_user_role: {e}")
        return None

def update_user_password(user_id, new_password):
    """Met à jour le mot de passe d'un utilisateur"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users 
            SET password = %s 
            WHERE id = %s 
            RETURNING id;
        """, (new_password, user_id))
        result = cursor.fetchone()
        conn.commit()
        cursor.close()
        db.release_connection(conn)
        
        if result:
            logger.info(f" Mot de passe mis à jour pour user ID: {user_id}")
            return True
        return False
    except Exception as e:
        logger.error(f" Erreur update_user_password: {e}")
        return False

def delete_user(user_id):
    """Supprime un utilisateur"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = %s;", (user_id,))
        conn.commit()
        rows_deleted = cursor.rowcount
        cursor.close()
        db.release_connection(conn)
        
        logger.info(f" Utilisateur ID {user_id} supprimé")
        return rows_deleted > 0
    except Exception as e:
        logger.error(f" Erreur delete_user: {e}")
        return False

def initialize_default_users():
    """Initialise les utilisateurs par défaut (admin et chauffeur)"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Vérifier si l'admin existe déjà
        cursor.execute("SELECT id FROM users WHERE email = 'admin@test.com';")
        if not cursor.fetchone():
            # Créer l'admin
            cursor.execute("""
                INSERT INTO users (email, password, role) 
                VALUES ('admin@test.com', 'admin123', 'admin');
            """)
            logger.info(" Utilisateur admin créé")
        
        # Vérifier si le chauffeur existe déjà
        cursor.execute("SELECT id FROM users WHERE email = 'chauffeur@transport.com';")
        if not cursor.fetchone():
            # Créer un chauffeur
            cursor.execute("""
                INSERT INTO users (email, password, role) 
                VALUES ('chauffeur@transport.com', 'chauffeur123', 'chauffeur');
            """)
            logger.info(" Utilisateur chauffeur créé")
        
        conn.commit()
        cursor.close()
        db.release_connection(conn)
        return True
    except Exception as e:
        logger.error(f" Erreur initialize_default_users: {e}")
        return False

# ==================== STATIONS ====================
def get_all_stations():
    """Récupère toutes les stations"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, latitude, longitude FROM stations ORDER BY id;")
        stations = cursor.fetchall()
        cursor.close()
        db.release_connection(conn)
        logger.info(f" Récupéré {len(stations)} stations")
        return stations
    except Exception as e:
        logger.error(f" Erreur get_all_stations: {e}")
        return []

def get_station_by_id(station_id):
    """Récupère une station par son ID"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, latitude, longitude FROM stations WHERE id = %s;", (station_id,))
        station = cursor.fetchone()
        cursor.close()
        db.release_connection(conn)
        return station
    except Exception as e:
        logger.error(f" Erreur get_station_by_id: {e}")
        return None

# ==================== MINIBUS ====================
def get_all_minibus():
    """Récupère tous les minibus"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, capacity, license_plate, current_passengers, status, last_maintenance 
            FROM minibus ORDER BY id;
        """)
        minibus = cursor.fetchall()
        cursor.close()
        db.release_connection(conn)
        logger.info(f" Récupéré {len(minibus)} minibus")
        return minibus
    except Exception as e:
        logger.error(f" Erreur get_all_minibus: {e}")
        return []

def get_available_minibus():
    """Récupère les minibus disponibles"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, capacity, license_plate, current_passengers 
            FROM minibus 
            WHERE status = 'available' AND current_passengers < capacity
            ORDER BY capacity DESC;
        """)
        available_minibus = cursor.fetchall()
        cursor.close()
        db.release_connection(conn)
        return available_minibus
    except Exception as e:
        logger.error(f" Erreur get_available_minibus: {e}")
        return []

# ==================== CLIENTS ====================
def get_all_clients():
    """Récupère tous les clients"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, first_name, last_name, email, phone FROM clients ORDER BY id;")
        clients = cursor.fetchall()
        cursor.close()
        db.release_connection(conn)
        return clients
    except Exception as e:
        logger.error(f" Erreur get_all_clients: {e}")
        return []

def create_client(first_name, last_name, email=None, phone=None):
    """Crée un nouveau client"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO clients (first_name, last_name, email, phone) 
            VALUES (%s, %s, %s, %s) RETURNING id;
        """, (first_name, last_name, email, phone))
        client_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        db.release_connection(conn)
        logger.info(f" Client créé avec ID: {client_id}")
        return client_id
    except Exception as e:
        logger.error(f" Erreur create_client: {e}")
        return None

# ==================== RÉSERVATIONS ====================
def get_all_reservations():
    """Récupère toutes les réservations avec détails"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                r.id, 
                c.first_name || ' ' || c.last_name as client_name,
                s1.name as pickup_station, 
                s2.name as dropoff_station,
                r.number_of_people,
                r.desired_time,
                r.status
            FROM reservations r
            JOIN clients c ON r.client_id = c.id
            JOIN stations s1 ON r.pickup_station_id = s1.id
            JOIN stations s2 ON r.dropoff_station_id = s2.id
            ORDER BY r.desired_time;
        """)
        reservations = cursor.fetchall()
        cursor.close()
        db.release_connection(conn)
        logger.info(f" Récupéré {len(reservations)} réservations")
        return reservations
    except Exception as e:
        logger.error(f" Erreur get_all_reservations: {e}")
        return []

def create_reservation(client_id, pickup_station_id, dropoff_station_id, number_of_people, desired_time):
    """Crée une nouvelle réservation"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO reservations 
            (client_id, pickup_station_id, dropoff_station_id, number_of_people, desired_time) 
            VALUES (%s, %s, %s, %s, %s) RETURNING id;
        """, (client_id, pickup_station_id, dropoff_station_id, number_of_people, desired_time))
        reservation_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        db.release_connection(conn)
        logger.info(f" Réservation créée avec ID: {reservation_id}")
        return reservation_id
    except Exception as e:
        logger.error(f" Erreur create_reservation: {e}")
        return None

def get_pending_reservations():
    """Récupère les réservations en attente pour l'optimisation"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                r.id,
                r.client_id,
                r.pickup_station_id,
                r.dropoff_station_id,
                r.number_of_people,
                r.desired_time
            FROM reservations r
            WHERE r.status = 'pending'
            ORDER BY r.desired_time;
        """)
        pending_reservations = cursor.fetchall()
        cursor.close()
        db.release_connection(conn)
        return pending_reservations
    except Exception as e:
        logger.error(f" Erreur get_pending_reservations: {e}")
        return []

# ==================== OPTIMIZED ROUTES ====================
def save_optimized_route(minibus_id, station_sequence, total_distance, total_passengers):
    """Sauvegarde une route optimisée trouvée par l'algorithme"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # IMPORTANT: Conversion en JSON valide
        import json
        
        # Si c'est une liste Python, convertir en JSON
        if isinstance(station_sequence, list):
            station_sequence = json.dumps(station_sequence)
        # Si c'est un tableau PostgreSQL (detecté comme tuple), convertir en liste puis JSON
        elif isinstance(station_sequence, tuple):
            station_sequence = json.dumps(list(station_sequence))
        # Si c'est une chaîne avec des virgules, convertir en liste puis JSON
        elif isinstance(station_sequence, str) and ',' in station_sequence:
            # Nettoyer et convertir en liste d'entiers
            try:
                numbers = [int(num.strip()) for num in station_sequence.split(',')]
                station_sequence = json.dumps(numbers)
            except ValueError:
                # Si ce n'est pas des nombres, garder comme chaîne JSON
                station_sequence = json.dumps(station_sequence)
        # Si c'est une chaîne simple
        elif isinstance(station_sequence, str):
            # Vérifier si c'est déjà du JSON
            if not (station_sequence.startswith('[') and station_sequence.endswith(']')):
                station_sequence = json.dumps([station_sequence])
        
        # Debug: Afficher ce qui est envoyé
        logger.info(f" Envoi station_sequence: {station_sequence}")
        
        cursor.execute("""
            INSERT INTO optimized_routes 
            (minibus_id, station_sequence, total_distance, total_passengers) 
            VALUES (%s, %s, %s, %s) RETURNING id;
        """, (minibus_id, station_sequence, total_distance, total_passengers))
        
        route_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        db.release_connection(conn)
        logger.info(f" Route optimisée sauvegardée avec ID: {route_id}")
        return route_id
    except Exception as e:
        logger.error(f" Erreur save_optimized_route: {e}")
        return None
def get_optimized_routes():
    """Récupère toutes les routes optimisées"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                opt.id,
                m.license_plate,
                opt.station_sequence,
                opt.total_distance,
                opt.total_passengers,
                opt.calculation_time
            FROM optimized_routes opt
            JOIN minibus m ON opt.minibus_id = m.id
            ORDER BY opt.calculation_time DESC;
        """)
        routes = cursor.fetchall()
        cursor.close()
        db.release_connection(conn)
        return routes
    except Exception as e:
        logger.error(f" Erreur get_optimized_routes: {e}")
        return []

def authenticate_user(email, password):
    """Authentifie un admin ou chauffeur"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, email, role, created_at, last_login
            FROM users 
            WHERE email = %s AND password = %s;
        """, (email, password))
        user = cursor.fetchone()
        
        if user:
            # Mettre à jour last_login
            cursor.execute("""
                UPDATE users 
                SET last_login = CURRENT_TIMESTAMP 
                WHERE id = %s;
            """, (user[0],))
            conn.commit()
            
            columns = ['id', 'email', 'role', 'created_at', 'last_login']
            user_dict = dict(zip(columns, user))
            
            cursor.close()
            db.release_connection(conn)
            logger.info(f" Utilisateur authentifié: {email} ({user_dict['role']})")
            return user_dict
        
        cursor.close()
        db.release_connection(conn)
        return None
    except Exception as e:
        logger.error(f" Erreur authenticate_user: {e}")
        return None

def get_all_users():
    """Récupère tous les utilisateurs (admin et chauffeurs)"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, email, role, created_at, last_login
            FROM users 
            ORDER BY role, email;
        """)
        users = cursor.fetchall()
        cursor.close()
        db.release_connection(conn)
        
        columns = ['id', 'email', 'role', 'created_at', 'last_login']
        return [dict(zip(columns, user)) for user in users]
    except Exception as e:
        logger.error(f" Erreur get_all_users: {e}")
        return []

def get_user_by_email(email):
    """Récupère un utilisateur par son email"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, email, role, created_at, last_login
            FROM users 
            WHERE email = %s;
        """, (email,))
        user = cursor.fetchone()
        cursor.close()
        db.release_connection(conn)
        
        if user:
            columns = ['id', 'email', 'role', 'created_at', 'last_login']
            return dict(zip(columns, user))
        return None
    except Exception as e:
        logger.error(f" Erreur get_user_by_email: {e}")
        return None

def get_users_by_role(role):
    """Récupère tous les utilisateurs d'un rôle spécifique"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, email, role, created_at, last_login
            FROM users 
            WHERE role = %s
            ORDER BY email;
        """, (role,))
        users = cursor.fetchall()
        cursor.close()
        db.release_connection(conn)
        
        columns = ['id', 'email', 'role', 'created_at', 'last_login']
        return [dict(zip(columns, user)) for user in users]
    except Exception as e:
        logger.error(f" Erreur get_users_by_role: {e}")
        return []

def update_user_role(user_id, new_role):
    """Met à jour le rôle d'un utilisateur"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users 
            SET role = %s 
            WHERE id = %s 
            RETURNING id, email, role;
        """, (new_role, user_id))
        result = cursor.fetchone()
        conn.commit()
        cursor.close()
        db.release_connection(conn)
        
        if result:
            columns = ['id', 'email', 'role']
            logger.info(f" Rôle mis à jour pour user ID: {user_id} -> {new_role}")
            return dict(zip(columns, result))
        return None
    except Exception as e:
        logger.error(f" Erreur update_user_role: {e}")
        return None

def update_user_password(user_id, new_password):
    """Met à jour le mot de passe d'un utilisateur"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users 
            SET password = %s 
            WHERE id = %s 
            RETURNING id;
        """, (new_password, user_id))
        result = cursor.fetchone()
        conn.commit()
        cursor.close()
        db.release_connection(conn)
        
        if result:
            logger.info(f" Mot de passe mis à jour pour user ID: {user_id}")
            return True
        return False
    except Exception as e:
        logger.error(f" Erreur update_user_password: {e}")
        return False

def delete_user(user_id):
    """Supprime un utilisateur"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = %s;", (user_id,))
        conn.commit()
        rows_deleted = cursor.rowcount
        cursor.close()
        db.release_connection(conn)
        
        logger.info(f" Utilisateur ID {user_id} supprimé")
        return rows_deleted > 0
    except Exception as e:
        logger.error(f" Erreur delete_user: {e}")
        return False

def initialize_default_users():
    """Initialise les utilisateurs par défaut (admin et chauffeur)"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Vérifier si l'admin existe déjà
        cursor.execute("SELECT id FROM users WHERE email = 'admin@test.com';")
        if not cursor.fetchone():
            # Créer l'admin
            cursor.execute("""
                INSERT INTO users (email, password, role) 
                VALUES ('admin@test.com', 'admin123', 'admin');
            """)
            logger.info(" Utilisateur admin créé")
        
        # Vérifier si le chauffeur existe déjà
        cursor.execute("SELECT id FROM users WHERE email = 'chauffeur@transport.com';")
        if not cursor.fetchone():
            # Créer un chauffeur
            cursor.execute("""
                INSERT INTO users (email, password, role) 
                VALUES ('chauffeur@transport.com', 'chauffeur123', 'chauffeur');
            """)
            logger.info(" Utilisateur chauffeur créé")
        
        conn.commit()
        cursor.close()
        db.release_connection(conn)
        return True
    except Exception as e:
        logger.error(f" Erreur initialize_default_users: {e}")
        return False

# ==================== MISE À JOUR DES STATISTIQUES ====================

def get_database_stats():
    """Récupère les statistiques de la base"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        stats = {}
        
        # Nombre de stations
        cursor.execute("SELECT COUNT(*) FROM stations;")
        stats['stations_count'] = cursor.fetchone()[0]
        
        # Nombre de minibus
        cursor.execute("SELECT COUNT(*) FROM minibus;")
        stats['minibus_count'] = cursor.fetchone()[0]
        
        # Nombre de clients
        cursor.execute("SELECT COUNT(*) FROM clients;")
        stats['clients_count'] = cursor.fetchone()[0]
        
        # Nombre de réservations par statut
        cursor.execute("SELECT status, COUNT(*) FROM reservations GROUP BY status;")
        stats['reservations_by_status'] = dict(cursor.fetchall())
        
        # Nombre d'utilisateurs par rôle (nouveau)
        cursor.execute("SELECT role, COUNT(*) FROM users GROUP BY role;")
        stats['users_by_role'] = dict(cursor.fetchall())
        
        cursor.close()
        db.release_connection(conn)
        
        logger.info(" Statistiques récupérées")
        return stats
    except Exception as e:
        logger.error(f" Erreur get_database_stats: {e}")
        return {}