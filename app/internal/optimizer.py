from app.database.crud import get_all_stations

station = get_all_stations()
print("Nombre de minibus :", len(station))
print(station)
