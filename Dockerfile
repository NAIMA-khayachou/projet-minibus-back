# Utilise l'image PostgreSQL comme base
FROM postgres:16-alpine

# Copie le script SQL de votre PC (hote) dans l'emplacement 
# d'initialisation de l'image Docker (conteneur).
COPY ./database/transport_db.sql /docker-entrypoint-initdb.d/transport_db.sql