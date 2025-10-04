from pathlib import Path
from models import init_database

def setup_database():
    # Pfad zur DB-Datei (relative to project root)
    project_root = Path(__file__).parent.parent.parent
    db_path = project_root / "database" / "fomo-bot-DB.sqlite"
    db_path.parent.mkdir(parents=True, exist_ok=True)  # falls Ordner noch nicht existiert

    # Bestätigung vor dem Löschen aller Tabellen
    print("WARNING: This will delete ALL existing tables and data in the database!")
    print("Tables to be deleted: postmortems, reports, chart_analyses, news_analyses,")
    print("news_items, event_analyses, economic_events, markets, config")
    print()
    
    while True:
        response = input("Do you want to continue? (yes/no): ").lower().strip()
        if response in ['yes', 'y']:
            break
        elif response in ['no', 'n']:
            print("Database setup cancelled.")
            return
        else:
            print("Please enter 'yes' or 'no'.")

    # Initialize database using SQLAlchemy
    engine = init_database()
    print(f"SQLite DB created/updated at: {db_path}")

if __name__ == "__main__":
    setup_database()