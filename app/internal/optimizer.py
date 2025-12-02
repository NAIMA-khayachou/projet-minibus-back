from app.database.crud import get_all_minibus

minibus = get_all_minibus()
print("Nombre de minibus :", len(minibus))
print(minibus)
