#!/usr/bin/env python3
"""
FOMO Bot - Main Application Runner
"""

import sys
import os
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

# Add the frontend directory to Python path
frontend_dir = Path(__file__).parent / "frontend"
sys.path.insert(0, str(frontend_dir))

def setup_environment():
    """Setup the environment and check dependencies"""
    print("🚀 Starting FOMO Bot...")
    
    # Check if database exists (relative to project root)
    db_path = Path(__file__).parent.parent / "database" / "fomo-bot-DB.sqlite"
    if not db_path.exists():
        print("❌ Database not found. Please run init_db.py first.")
        print("   Run: cd backend && python init_db.py")
        return False
    
    # Check if markets are populated
    try:
        from models import get_db_session, Market
        session = get_db_session()
        market_count = session.query(Market).count()
        session.close()
        
        if market_count == 0:
            print("⚠️  No markets found. Populating initial markets...")
            from populate_markets import populate_initial_markets
            populate_initial_markets()
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")
        return False
    
    print("✅ Environment setup complete!")
    return True

def main():
    """Main function to run the FOMO Bot"""
    if not setup_environment():
        sys.exit(1)
    
    print("\n📊 FOMO Bot - Trading Analysis Tool")
    print("=" * 50)
    print("Phase 1: Economic Calendar Analysis ✅")
    print("Phase 2: Financial News Analysis ⏳")
    print("Phase 3: Chart Analysis ⏳")
    print("=" * 50)
    
    try:
        from app import app
        print("\n🌐 Starting web server...")
        print("📱 Open your browser and go to: http://localhost:5000")
        print("⏹️  Press Ctrl+C to stop the server")
        print("-" * 50)
        
        app.run(debug=True, host='0.0.0.0', port=5000)
        
    except KeyboardInterrupt:
        print("\n👋 FOMO Bot stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting FOMO Bot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()



