# app/models/reservation.py

from ..database.connection import db 
import psycopg2
import datetime

class Reservation:
    """Gère l'insertion d'un nouveau client et de sa réservation."""

    @staticmethod
    def create(data):
        """Insère un nouveau client et sa réservation, puis retourne l'ID de la réservation."""
        conn = None
        cursor = None
        reservation_id = None
        
        # Données nécessaires du frontend React
        phone = data.get('phone', None)
        email = data['email']
        first_name = data['first_name']
        last_name = data['last_name']
        
        try:
            conn = db.get_connection()
            cursor = conn.cursor()

            # --- VALIDATION 1: Vérifier si le téléphone existe déjà ---
            if phone:  # Si un téléphone est fourni
                cursor.execute(
                    "SELECT id, email, first_name, last_name FROM clients WHERE phone = %s",
                    (phone,)
                )
                existing_phone_client = cursor.fetchone()
                
                if existing_phone_client:
                    existing_id, existing_email, existing_first_name, existing_last_name = existing_phone_client
                    
                    # Si le téléphone existe avec un email différent
                    if existing_email != email:
                        raise ValueError(
                            f"Ce numéro de téléphone ({phone}) est déjà associé au compte de "
                            f"{existing_first_name} {existing_last_name} ({existing_email}). "
                            f"Veuillez utiliser un numéro différent ou contacter le support."
                        )

            # --- VALIDATION 2: Vérifier si l'email existe déjà ---
            cursor.execute(
                "SELECT id, phone, first_name, last_name FROM clients WHERE email = %s",
                (email,)
            )
            existing_email_client = cursor.fetchone()
            
            if existing_email_client:
                existing_id, existing_phone, existing_first_name, existing_last_name = existing_email_client
                
                # Si l'email existe avec un téléphone différent et non vide
                if phone and existing_phone and existing_phone != phone:
                    raise ValueError(
                        f"Cet email ({email}) est déjà associé à un autre numéro de téléphone "
                        f"({existing_phone}). Si c'est votre compte, utilisez le même numéro de téléphone."
                    )
                
                # Si c'est exactement le même client (même email ET même téléphone)
                # On réutilise cet ID client
                client_id = existing_id
                print(f"✅ Client existant réutilisé: ID {client_id}")
            else:
                # --- Insertion d'un nouveau Client UNIQUEMENT s'il n'existe pas ---
                sql_client = """
                INSERT INTO public.clients (first_name, last_name, email, phone, created_at) 
                VALUES (%s, %s, %s, %s, %s) RETURNING id;
                """
                client_data = (first_name, last_name, email, phone, datetime.datetime.now())
                cursor.execute(sql_client, client_data)
                client_id = cursor.fetchone()[0]
                print(f"✅ Nouveau client créé: ID {client_id}")

            # --- 2. Insertion de la Réservation ---
            sql_reservation = """
            INSERT INTO public.reservations (
                client_id, pickup_station_id, dropoff_station_id, 
                number_of_people, desired_time, status
            ) VALUES (%s, %s, %s, %s, %s, 'pending') RETURNING id;
            """
            
            params_reservation = (
                client_id,
                int(data['pickup_station_id']),
                int(data['dropoff_station_id']),
                int(data['number_of_people']),
                data['desired_time']
            )

            cursor.execute(sql_reservation, params_reservation)
            reservation_id = cursor.fetchone()[0]
            
            # 3. Validation et Commit
            conn.commit()
            
            print(f"✅ Réservation créée avec succès: ID {reservation_id} pour le client {client_id}")
            return reservation_id

        except ValueError as ve:
            # Erreur de validation métier
            if conn:
                conn.rollback()
            print(f"⚠️ Validation échouée: {ve}")
            raise
            
        except psycopg2.IntegrityError as ie:
            # Erreur de contrainte de base de données
            if conn:
                conn.rollback()
            print(f"🔴 Erreur d'intégrité: {ie}")
            
            if 'clients_email_key' in str(ie):
                raise ValueError(f"Cet email ({email}) est déjà utilisé dans notre système.")
            elif 'clients_phone_key' in str(ie):
                raise ValueError(f"Ce numéro de téléphone ({phone}) est déjà utilisé dans notre système.")
            else:
                raise ValueError("Une erreur de duplication s'est produite.")
                
        except Exception as e:
            # Erreur inattendue
            if conn:
                conn.rollback()
            print(f"🔴 Erreur inattendue: {type(e).__name__}: {e}")
            raise
            
        finally:
            if cursor:
                cursor.close()
            if conn:
                db.release_connection(conn)