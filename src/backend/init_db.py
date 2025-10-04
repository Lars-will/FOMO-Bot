#!/usr/bin/env python3
"""
Database Initialization Script for FOMO Bot

This script creates the SQLite database from scratch with all required tables.
Run this script once before starting the application for the first time.

Tables created:
- markets: Trading markets (FDAX, BTC, SPY, etc.)
- config: Application configuration (API keys, timezone, etc.)
- economic_events: Scraped economic calendar events
- event_analyses: AI-generated event analyses
- news_items: Financial news (Phase 2)
- news_analyses: News analysis (Phase 2)
- chart_analyses: Technical chart analysis (Phase 3)
- reports: Generated HTML reports
- postmortems: Trading reflections
"""

from pathlib import Path
import sys
from models import init_database, get_db_session, Market, Config

def create_database_directory():
    """Create the database directory if it doesn't exist"""
    project_root = Path(__file__).parent.parent.parent
    db_dir = project_root / "database"
    db_dir.mkdir(parents=True, exist_ok=True)
    return db_dir / "fomo-bot-DB.sqlite"

def setup_database(force=False):
    """
    Initialize the database with all required tables
    
    Args:
        force (bool): If True, skip confirmation prompt
    """
    db_path = create_database_directory()
    
    # Check if database already exists
    db_exists = db_path.exists()
    
    if db_exists and not force:
        print("⚠️  WARNING: Database already exists!")
        print(f"   Location: {db_path}")
        print()
        print("   This will DELETE ALL existing data including:")
        print("   - All reports and postmortems")
        print("   - All economic events and analyses")
        print("   - All configuration and API keys")
        print("   - All market definitions")
        print()
        
        while True:
            response = input("Do you want to continue? (yes/no): ").lower().strip()
            if response in ['yes', 'y']:
                break
            elif response in ['no', 'n']:
                print("❌ Database setup cancelled.")
                return False
            else:
                print("Please enter 'yes' or 'no'.")
    
    # Initialize database schema
    print("🔄 Creating database schema...")
    try:
        engine = init_database()
        print(f"✅ Database schema created successfully!")
        print(f"   Location: {db_path}")
        print()
        
        # Show created tables
        print("📊 Created tables:")
        tables = [
            "markets", "config", "economic_events", "event_analyses",
            "news_items", "news_analyses", "chart_analyses", 
            "reports", "postmortems"
        ]
        for table in tables:
            print(f"   ✓ {table}")
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        return False

def populate_initial_data():
    """Populate database with initial sample data (optional)"""
    try:
        session = get_db_session()
        
        # Check if markets already exist
        market_count = session.query(Market).count()
        if market_count > 0:
            print(f"ℹ️  Skipping initial data - {market_count} markets already exist")
            session.close()
            return
        
        print("📝 Adding sample markets...")
        
        # Add some common trading markets
        sample_markets = [
            Market(symbol="FDAX", description="DAX Futures (Germany)"),
            Market(symbol="BTC", description="Bitcoin"),
            Market(symbol="SPY", description="S&P 500 ETF"),
            Market(symbol="EUR/USD", description="Euro/US Dollar"),
        ]
        
        for market in sample_markets:
            session.add(market)
            print(f"   ✓ Added {market.symbol} - {market.description}")
        
        # Create default config
        default_config = Config(
            timezone='Europe/Berlin',
            star_filter=1  # Analyze all events by default
        )
        session.add(default_config)
        
        session.commit()
        session.close()
        
        print("✅ Initial data populated successfully!")
        print()
        
    except Exception as e:
        print(f"❌ Error populating initial data: {e}")

def show_next_steps():
    """Display next steps for the user"""
    print("=" * 60)
    print("🎉 Database setup complete!")
    print("=" * 60)
    print()
    print("📋 Next steps:")
    print()
    print("1. Configure your API key:")
    print("   - Run the application: python src/run.py")
    print("   - Go to Configuration page in the web interface")
    print("   - Add your OpenAI API key")
    print()
    print("2. (Optional) Add more markets:")
    print("   - Go to Configuration page")
    print("   - Use the 'Add Market' form")
    print()
    print("3. Generate your first report:")
    print("   - Go to the homepage")
    print("   - Select a market and date")
    print("   - Click 'Generate Report'")
    print()
    print("=" * 60)

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 FOMO Bot Database Initialization")
    print("=" * 60)
    print()
    
    # Check if --force flag is provided
    force = "--force" in sys.argv or "-f" in sys.argv
    
    # Setup database
    success = setup_database(force=force)
    
    if success:
        # Populate with initial data
        populate_initial_data()
        
        # Show next steps
        show_next_steps()
    else:
        sys.exit(1)