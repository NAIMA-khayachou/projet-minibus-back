import folium
from folium import PolyLine
import logging
from sqlalchemy import MetaData
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MapVisualizer:
    def __init__(self, center_lat: float = 31.6295, center_lon: float = -7.9811):
        self.center_lat = center_lat
        self.center_lon = center_lon
        self.map = None
        
        # Couleurs pour différencier les minibus
        self.minibus_colors = [
            'red', 'blue', 'green', 'purple', 'orange', 
            'darkred', 'lightred', 'beige', 'darkblue', 'darkgreen'
        ]
    
    def create_base_map(self, zoom_start: int = 12):
        """Crée la carte de base"""
        self.map = folium.Map(
            location=[self.center_lat, self.center_lon],
            zoom_start=zoom_start,
            tiles='OpenStreetMap'
        )
        return self.map
    
    def visualize_all_stations(self, db_session):
        """Affiche toutes les stations depuis la base de données"""
        if not self.map:
            self.create_base_map()
        
        
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
        
        logger.info(f"✅ Ajouté {len(stations)} stations")
        return len(stations)
    
    def visualize_solution(self, solution, stations_dict):
        """
        Affiche les itinéraires de tous les minibus d'une solution
        
        Args:
            solution: Objet Solution avec itinéraires
            stations_dict: Dict {station_id: {'name': str, 'latitude': float, 'longitude': float}}
        """
        if not self.map:
            self.create_base_map()
        
        minibus_count = 0
        
        for minibus_id, itineraire in solution.itineraires.items():
            # Ignorer les minibus sans arrêts
            if not itineraire.arrets or len(itineraire.arrets) <= 2:
                continue
            
            # Trouver le minibus correspondant
            minibus_obj = next((m for m in solution.minibus_list if m.id == minibus_id), None)
            if not minibus_obj:
                continue
            
            # Couleur pour ce minibus
            color = self.minibus_colors[minibus_count % len(self.minibus_colors)]
            minibus_count += 1
            
            # Tracer l'itinéraire
            self._draw_minibus_route(
                itineraire=itineraire,
                minibus_obj=minibus_obj,
                stations_dict=stations_dict,
                color=color,
                minibus_number=minibus_count
            )
        
        logger.info(f"✅ Tracé {minibus_count} itinéraires de minibus")
        return minibus_count
    
    def _draw_minibus_route(self, itineraire, minibus_obj, stations_dict, color, minibus_number):
        """
        Trace l'itinéraire d'un minibus spécifique
        
        Args:
            itineraire: ItineraireMinibus
            minibus_obj: Objet Minibus
            stations_dict: Dict des stations
            color: Couleur pour ce minibus
            minibus_number: Numéro du minibus (pour affichage)
        """
        # Construire la liste des coordonnées
        route_coords = []
        arrets_info = []
        
        for i, arret in enumerate(itineraire.arrets):
            station = stations_dict.get(arret.station_id)
            if not station:
                logger.warning(f"⚠️ Station {arret.station_id} introuvable")
                continue
            
            lat = station.get('latitude')
            lon = station.get('longitude')
            
            if lat is None or lon is None:
                continue
            
            route_coords.append([lat, lon])
            
            # Informations pour les marqueurs
            arrets_info.append({
                'order': i + 1,
                'lat': lat,
                'lon': lon,
                'station_name': arret.station_name,
                'type': arret.type,
                'passagers': getattr(arret, 'passagers_a_bord', 0),
                'reservation_id': getattr(arret, 'reservation_id', None)
            })
        
        if len(route_coords) < 2:
            logger.warning(f"⚠️ Itinéraire trop court pour minibus {minibus_obj.license_plate}")
            return
        
        # ✅ TRACER LA LIGNE DE L'ITINÉRAIRE
        folium.PolyLine(
            locations=route_coords,
            color=color,
            weight=4,
            opacity=0.7,
            popup=f"<b>Minibus {minibus_number}</b><br>"
                  f"Plaque: {minibus_obj.license_plate}<br>"
                  f"Distance: {itineraire.distance_totale:.2f} km<br>"
                  f"Durée: {itineraire.duree_totale:.1f} min<br>"
                  f"Charge max: {itineraire.charge_maximale}/{minibus_obj.capacity}"
        ).add_to(self.map)
        
        # ✅ AJOUTER DES MARQUEURS POUR CHAQUE ARRÊT
        for arret_info in arrets_info:
            # Icône selon le type d'arrêt
            if arret_info['type'] == 'DEPOT':
                icon_color = 'black'
                icon_name = 'home'
                prefix = 'glyphicon'
            elif arret_info['type'] == 'PICKUP':
                icon_color = 'green'
                icon_name = 'arrow-up'
                prefix = 'glyphicon'
            else:  # DROPOFF
                icon_color = 'red'
                icon_name = 'arrow-down'
                prefix = 'glyphicon'
            
            # Popup avec détails
            popup_html = f"""
            <div style='width: 200px'>
                <b>Arrêt #{arret_info['order']}</b><br>
                <b>Station:</b> {arret_info['station_name']}<br>
                <b>Type:</b> {arret_info['type']}<br>
                <b>Passagers à bord:</b> {arret_info['passagers']}<br>
            """
            
            if arret_info['reservation_id']:
                popup_html += f"<b>Réservation:</b> #{arret_info['reservation_id']}<br>"
            
            popup_html += f"<b>Minibus:</b> {minibus_obj.license_plate}</div>"
            
            # Créer le marqueur
            folium.Marker(
                location=[arret_info['lat'], arret_info['lon']],
                popup=popup_html,
                tooltip=f"#{arret_info['order']} - {arret_info['station_name']}",
                icon=folium.Icon(
                    color=icon_color,
                    icon=icon_name,
                    prefix=prefix
                )
            ).add_to(self.map)
            
            # Ajouter un label avec le numéro d'ordre
            folium.CircleMarker(
                location=[arret_info['lat'], arret_info['lon']],
                radius=15,
                color=color,
                fill=True,
                fillColor=color,
                fillOpacity=0.8,
                popup=f"Arrêt #{arret_info['order']}"
            ).add_to(self.map)
    
    def add_legend(self, minibus_list):
        """Ajoute une légende pour les minibus"""
        legend_html = '''
        <div style="position: fixed; 
                    top: 10px; right: 10px; 
                    width: 250px; height: auto; 
                    background-color: white; 
                    border:2px solid grey; 
                    z-index:9999; 
                    font-size:14px;
                    padding: 10px">
        <p style="margin:0; font-weight:bold;">Légende des Minibus</p>
        <hr style="margin: 5px 0;">
        '''
        
        for i, minibus in enumerate(minibus_list[:len(self.minibus_colors)]):
            color = self.minibus_colors[i]
            legend_html += f'''
            <p style="margin: 5px 0;">
                <span style="background-color:{color}; 
                             width: 20px; 
                             height: 10px; 
                             display: inline-block;
                             border: 1px solid black;">
                </span> 
                {minibus.license_plate}
            </p>
            '''
        
        legend_html += '''
        <hr style="margin: 5px 0;">
        <p style="margin: 5px 0;"><span style="color:green;">🟢</span> Pickup</p>
        <p style="margin: 5px 0;"><span style="color:red;">🔴</span> Dropoff</p>
        <p style="margin: 5px 0;"><span style="color:black;">🏢</span> Dépôt</p>
        </div>
        '''
        
        self.map.get_root().html.add_child(folium.Element(legend_html))
    
    def save_map(self, filename: str = 'map.html'):
        """Sauvegarde la carte dans un fichier HTML"""
        if not self.map:
            logger.error("❌ Aucune carte à sauvegarder")
            return False
        
        self.map.save(filename)
        logger.info(f"✅ Carte sauvegardée: {filename}")
        return True