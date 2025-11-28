import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
app_dir = os.path.dirname(current_dir)  
project_root = os.path.dirname(app_dir)  
sys.path.insert(0, project_root)
sys.path.insert(0, app_dir)

from app.utils.geo import MapVisualizer

def main():
    print("🗺️  Génération de la carte...")
    
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        engine = create_engine('postgresql://admin:admin@localhost:5432/projet_minibus')
        Session = sessionmaker(bind=engine)
        db_session = Session()
        
        visualizer = MapVisualizer()
        visualizer.create_base_map()
        visualizer.visualize_all_stations(db_session)
        
        output_file = "carte_stations.html"
        if visualizer.save_map(output_file):
            print(f"✅ Carte générée: {output_file}")
            import webbrowser
            webbrowser.open(f'file://{os.path.abspath(output_file)}')
            print("🌐 Ouverture dans le navigateur...")
        
        db_session.close()
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        print("💡 Vérifiez:")
        print("   - Que PostgreSQL est démarré")
        print("   - Que la base 'transport_db' existe")
        print("   - Que les tables sont créées")

if __name__ == '__main__':
    main()