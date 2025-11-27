import folium
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MapVisualizer:
    def __init__(self, center_lat: float = 31.6295, center_lon: float = -7.9811):
        self.center_lat = center_lat
        self.center_lon = center_lon
        self.map = None

    def create_base_map(self, zoom_start: int = 12):
        self.map = folium.Map(
            location=[self.center_lat, self.center_lon],
            zoom_start=zoom_start,
            tiles='OpenStreetMap'
        )
        return self.map

    def visualize_all_stations(self, db_session):#Affiche toutes les stations depuis la base de données en utilisant la réflexion"""
        if not self.map:
            self.create_base_map()
        from sqlalchemy import MetaData
        metadata = MetaData()
        metadata.reflect(bind=db_session.bind)
        stations_table = metadata.tables['stations']

        stations = db_session.query(stations_table).all()

        for station in stations:
            folium.Marker(
                location=[station.latitude, station.longitude],
                popup=f"<b>{station.name}</b><br>ID: {station.id}",
                tooltip=station.name,
                icon=folium.Icon(color='blue', icon='info-sign')
            ).add_to(self.map)

        logger.info(f"Ajouté {len(stations)} stations")

    def save_map(self, filename: str = 'map.html'):
        if not self.map:
            return False
        self.map.save(filename)
        logger.info(f"Carte sauvegardée: {filename}")
        return True