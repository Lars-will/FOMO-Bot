from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from datetime import datetime, date, timedelta
from pathlib import Path
import logging
import sys
import os

# Add backend to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from models import get_db_session, Market, Config, Report, Postmortem
from scraper import scrape_and_save_events
from llm_analyzer import analyze_economic_events
from report_generator import generate_report, ReportGenerator

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'fomo-bot-secret-key-2024'  # Change this in production

def get_available_markets():
    """Get list of available markets using ORM"""
    try:
        session = get_db_session()
        markets = session.query(Market).order_by(Market.symbol).all()
        session.close()
        return markets
    except Exception as e:
        logger.error(f"Error getting markets: {e}")
        return []

@app.route('/')
def index():
    """Homepage with market selection and report generation"""
    markets = get_available_markets()
    return render_template('index.html', markets=markets)

@app.route('/generate_report', methods=['POST'])
def generate_report_route():
    """Generate report for selected market and date"""
    try:
        market_symbol = request.form.get('market')
        report_date_str = request.form.get('date')
        
        if not market_symbol:
            flash('Please select a market.', 'error')
            return redirect(url_for('index'))
        
        # Parse date
        if report_date_str:
            report_date = datetime.strptime(report_date_str, '%Y-%m-%d').date()
        else:
            report_date = date.today()
        
        # Check if report already exists for this market and date
        session = get_db_session()
        existing_report = session.query(Report).join(Market).filter(
            Market.symbol == market_symbol,
            Report.date == report_date
        ).first()
        session.close()
        
        if existing_report:
            flash(f'Report for {market_symbol} on {report_date.strftime("%m/%d/%Y")} already exists!', 'info')
            return redirect(url_for('index'))
        
        # Step 1: Scrape economic events (only if not already done today)
        events_count = scrape_and_save_events(report_date)
        
        # Step 2: Analyze events with LLM for the specific market
        analyses = analyze_economic_events(report_date, market_symbol)
        
        # Step 3: Generate report
        report = generate_report(report_date, market_symbol)
        
        if report:
            return redirect(url_for('view_report', report_id=report['report_id']))
        else:
            flash('Failed to generate report', 'error')
            return redirect(url_for('index'))
            
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        flash(f'Error generating report: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/report/<int:report_id>')
def view_report(report_id):
    """View a specific report"""
    try:
        generator = ReportGenerator()
        report = generator.get_report(report_id)
        
        if not report:
            flash('Report not found', 'error')
            return redirect(url_for('index'))
        
        return render_template('view_report.html', 
                             report_html=report['report_html'],
                             report_id=report_id)
        
    except Exception as e:
        logger.error(f"Error viewing report: {e}")
        flash('Error loading report', 'error')
        return redirect(url_for('index'))

@app.route('/reports')
def reports():
    """Historical reports page"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 10
        offset = (page - 1) * per_page
        
        # Get filter parameters
        market_filter = request.args.get('market', '')
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')
        
        session = get_db_session()
        
        # Build query using ORM
        query = session.query(Report).join(Market)
        
        if market_filter:
            query = query.filter(Market.symbol == market_filter)
        
        if date_from:
            query = query.filter(Report.date >= date_from)
        
        if date_to:
            query = query.filter(Report.date <= date_to)
        
        # Get total count for pagination
        total_count = query.count()
        
        # Get paginated results
        reports = query.order_by(Report.date.desc(), Report.created_at.desc()).offset(offset).limit(per_page).all()
        
        # Get markets while session is still open
        markets = session.query(Market).order_by(Market.symbol).all()
        
        # Extract report data while session is still open to avoid lazy loading issues
        reports_data = []
        for report in reports:
            reports_data.append({
                'id': report.id,
                'date': report.date,
                'market_id': report.market_id,
                'created_at': report.created_at,
                'market_symbol': report.market.symbol,
                'market_description': report.market.description,
                'report_html': report.report_html
            })
        
        session.close()
        
        # Calculate pagination info
        total_pages = (total_count + per_page - 1) // per_page
        has_prev = page > 1
        has_next = page < total_pages
        
        return render_template('reports.html', 
                             reports=reports_data,
                             markets=markets,
                             current_market=market_filter,
                             date_from=date_from,
                             date_to=date_to,
                             page=page,
                             total_pages=total_pages,
                             has_prev=has_prev,
                             has_next=has_next)
        
    except Exception as e:
        logger.error(f"Error loading reports: {e}")
        flash('Error loading reports', 'error')
        return redirect(url_for('index'))

@app.route('/config')
def config():
    """Configuration page"""
    try:
        session = get_db_session()
        config_data = session.query(Config).order_by(Config.created_at.desc()).first()
        markets = session.query(Market).order_by(Market.symbol).all()
        session.close()
        
        return render_template('config.html', config=config_data, markets=markets)
        
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        flash('Error loading configuration', 'error')
        return redirect(url_for('index'))

@app.route('/save_config', methods=['POST'])
def save_config():
    """Save configuration"""
    try:
        llm_api_key = request.form.get('llm_api_key', '').strip()
        news_sources = request.form.get('news_sources', '').strip()
        chart_folder = request.form.get('chart_folder', '').strip()
        timezone = request.form.get('timezone', 'Europe/Berlin').strip()
        star_filter = int(request.form.get('star_filter', 1))
        
        session = get_db_session()
        
        # Check if config already exists
        config = session.query(Config).first()
        
        if config:
            # Update existing config
            config.llm_api_key = llm_api_key
            config.news_sources = news_sources
            config.chart_folder = chart_folder
            config.timezone = timezone
            config.star_filter = star_filter
        else:
            # Create new config
            config = Config(
                llm_api_key=llm_api_key,
                news_sources=news_sources,
                chart_folder=chart_folder,
                timezone=timezone,
                star_filter=star_filter
            )
            session.add(config)
        
        session.commit()
        session.close()
        
        flash('Configuration saved successfully!', 'success')
        return redirect(url_for('config'))
        
    except Exception as e:
        logger.error(f"Error saving config: {e}")
        flash('Error saving configuration', 'error')
        return redirect(url_for('config'))

@app.route('/add_market', methods=['POST'])
def add_market():
    """Add new market"""
    try:
        symbol = request.form.get('symbol', '').strip().upper()
        description = request.form.get('description', '').strip()
        
        if not symbol:
            flash('Market symbol is required', 'error')
            return redirect(url_for('config'))
        
        session = get_db_session()
        
        # Check if market already exists
        existing_market = session.query(Market).filter(Market.symbol == symbol).first()
        if existing_market:
            existing_market.description = description
        else:
            market = Market(symbol=symbol, description=description)
            session.add(market)
        
        session.commit()
        session.close()
        
        flash(f'Market {symbol} added successfully!', 'success')
        return redirect(url_for('config'))
        
    except Exception as e:
        logger.error(f"Error adding market: {e}")
        flash('Error adding market', 'error')
        return redirect(url_for('config'))

@app.route('/delete_market', methods=['POST'])
def delete_market():
    """Delete a market"""
    try:
        market_id = request.form.get('market_id')
        
        if not market_id:
            flash('Market ID is required', 'error')
            return redirect(url_for('config'))
        
        session = get_db_session()
        
        # Check if market exists
        market = session.query(Market).filter(Market.id == market_id).first()
        if not market:
            flash('Market not found', 'error')
            session.close()
            return redirect(url_for('config'))
        
        # Delete the market
        session.delete(market)
        session.commit()
        session.close()
        
        flash(f'Market {market.symbol} deleted successfully!', 'success')
        return redirect(url_for('config'))
        
    except Exception as e:
        logger.error(f"Error deleting market: {e}")
        flash('Error deleting market', 'error')
        return redirect(url_for('config'))

@app.route('/postmortem/<int:report_id>', methods=['GET', 'POST'])
def postmortem(report_id):
    """Add postmortem reflection to a report"""
    try:
        session = get_db_session()
        
        if request.method == 'POST':
            reflection_text = request.form.get('reflection_text', '').strip()
            
            if not reflection_text:
                flash('Reflection text is required', 'error')
                return redirect(url_for('postmortem', report_id=report_id))
            
            postmortem = Postmortem(
                report_id=report_id,
                reflection_text=reflection_text
            )
            session.add(postmortem)
            session.commit()
            session.close()
            
            flash('Postmortem saved successfully!', 'success')
            return redirect(url_for('reports'))
        
        # GET request - show form
        report = session.query(Report).join(Market).filter(Report.id == report_id).first()
        postmortem_data = session.query(Postmortem).filter(Postmortem.report_id == report_id).order_by(Postmortem.created_at.desc()).first()
        
        if not report:
            session.close()
            flash('Report not found', 'error')
            return redirect(url_for('reports'))
        
        # Extract report data while session is open to avoid lazy loading issues
        report_data = {
            'id': report.id,
            'date': report.date,
            'market': {
                'symbol': report.market.symbol,
                'description': report.market.description
            }
        }
        session.close()
        
        return render_template('postmortem.html', report=report_data, postmortem=postmortem_data)
        
    except Exception as e:
        logger.error(f"Error with postmortem: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        flash(f'Error processing postmortem: {str(e)}', 'error')
        return redirect(url_for('reports'))

@app.route('/delete_report/<int:report_id>', methods=['POST'])
def delete_report(report_id):
    """Delete a report"""
    try:
        session = get_db_session()
        
        # Check if report exists
        report = session.query(Report).filter(Report.id == report_id).first()
        if not report:
            flash('Report not found', 'error')
            session.close()
            return redirect(url_for('reports'))
        
        # Delete associated postmortems first
        postmortems = session.query(Postmortem).filter(Postmortem.report_id == report_id).all()
        for postmortem in postmortems:
            session.delete(postmortem)
        
        # Delete the report
        session.delete(report)
        session.commit()
        session.close()
        
        flash(f'Report deleted successfully!', 'success')
        return redirect(url_for('reports'))
        
    except Exception as e:
        logger.error(f"Error deleting report: {e}")
        flash('Error deleting report', 'error')
        return redirect(url_for('reports'))

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    templates_dir = Path('templates')
    templates_dir.mkdir(exist_ok=True)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
