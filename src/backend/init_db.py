import sqlite3
from pathlib import Path

def setup_database():
    # Pfad zur DB-Datei
    db_path = Path("database/fomo-bot-DB.sqlite")
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

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Foreign Keys aktivieren
    cur.execute("PRAGMA foreign_keys = ON;")

    # Bestehende Tabellen löschen (damit Script wiederholbar ist)
    tables = [
        "postmortems", "reports", "chart_analyses", "news_analyses",
        "news_items", "event_analyses", "economic_events",
        "markets", "config"
    ]
    for t in tables:
        cur.execute(f"DROP TABLE IF EXISTS {t};")

    # Tabellen erzeugen
    cur.executescript("""
    CREATE TABLE markets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT NOT NULL UNIQUE,
        description TEXT
    );

    CREATE TABLE config (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        llm_api_key TEXT,
        news_sources TEXT,
        chart_folder TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE economic_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date DATE NOT NULL,
        market_id INTEGER,
        time TIME,
        currency TEXT,
        importance TEXT,
        event_name TEXT,
        actual TEXT,
        forecast TEXT,
        previous TEXT,
        source_url TEXT,
        FOREIGN KEY(market_id) REFERENCES markets(id)
    );

    CREATE TABLE event_analyses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id INTEGER,
        analysis_text TEXT,
        impact_score INTEGER,
        sentiment_summary TEXT,
        search_sources TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(event_id) REFERENCES economic_events(id)
    );

    CREATE TABLE news_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date DATE NOT NULL,
        market_id INTEGER,
        title TEXT,
        summary TEXT,
        url TEXT,
        source TEXT,
        FOREIGN KEY(market_id) REFERENCES markets(id)
    );

    CREATE TABLE news_analyses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        news_id INTEGER,
        analysis_text TEXT,
        sentiment TEXT,
        impact_score INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(news_id) REFERENCES news_items(id)
    );

    CREATE TABLE chart_analyses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date DATE NOT NULL,
        market_id INTEGER,
        timeframe TEXT,
        image_path TEXT,
        analysis_text TEXT,
        scenarios TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(market_id) REFERENCES markets(id)
    );

    CREATE TABLE reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date DATE NOT NULL,
        market_id INTEGER,
        report_html TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(market_id) REFERENCES markets(id)
    );

    CREATE TABLE postmortems (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        report_id INTEGER,
        reflection_text TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(report_id) REFERENCES reports(id)
    );
    """)

    conn.commit()
    conn.close()
    print(f"SQLite DB created/updated at: {db_path}")

if __name__ == "__main__":
    setup_database()