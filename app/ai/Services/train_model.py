import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error
import psycopg2
import joblib

# 1️⃣ Connexion à PostgreSQL
DB_STRING = "dbname=minibus_db user=minibus_user password=minibus_user host=localhost"

try:
    conn = psycopg2.connect(DB_STRING)
    query = """
    SELECT from_station_id, to_station_id, hour_of_day, day_of_week, 
           passenger_count, distance_km, actual_duration_seconds
    FROM trip_logs
    WHERE actual_duration_seconds IS NOT NULL;
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    print(f" {len(df)} lignes chargées depuis la base de données.")
except Exception as e:
    print(f" Erreur de connexion : {e}")
    exit()

# 2 Feature Engineering : Aider l'IA à comprendre la nuit
# On crée une colonne binaire : 1 si c'est la nuit (trafic fluide), 0 sinon
df['is_night'] = df['hour_of_day'].apply(lambda x: 1 if (x >= 23 or x <= 6) else 0)

# 3 Préparer les features (X) et la cible (y)
features = ['from_station_id', 'to_station_id', 'hour_of_day', 'day_of_week', 
            'passenger_count', 'distance_km', 'is_night']
X = df[features]
y = df['actual_duration_seconds']

# 4 Séparer en train/test
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 5 Créer le modèle avec les hyperparamètres de précision
model = RandomForestRegressor(
    n_estimators=1000,    # Plus d'arbres pour stabiliser les prédictions
    max_depth=None,       # Pas de limite pour capter les cas comme 0km
    min_samples_split=2,  # Correction technique (minimum 2)
    min_samples_leaf=1,   # Pour coller aux données réelles de nuit
    random_state=42,
    n_jobs=-1             # Utilise tout le CPU
)

print("⏳ Entraînement en cours...")
model.fit(X_train, y_train)

# 6 Évaluation et Importance des variables
y_pred = model.predict(X_test)
mae = mean_absolute_error(y_test, y_pred)
print(f" Erreur moyenne (MAE): {mae/60:.2f} minutes")

# Afficher ce que l'IA considère comme important
importances = pd.Series(model.feature_importances_, index=features)
print("\n Importance des variables :")
print(importances.sort_values(ascending=False))

# 7 Sauvegarde
joblib.dump(model, 'eta_model.pkl')
print("\n Modèle sauvegardé dans 'eta_model.pkl'")

# --- AJOUTE CECI À LA FIN DE TON CODE ---
print("\ntest de prédiction pour FST -> ENSA (0.5 km) :")
# [from_id, to_id, hour, day, passengers, dist, is_night]
test_fst_ensa = pd.DataFrame([[9, 10, 10, 1, 5, 0.5, 0]], columns=features)
prediction = model.predict(test_fst_ensa)
print(f" Résultat : {prediction[0]/60:.2f} minutes")