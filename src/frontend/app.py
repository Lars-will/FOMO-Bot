from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, Response, stream_with_context
from datetime import datetime, date, timedelta
from pathlib import Path
import logging
import sys
import os
import json
import queue
import threading
import uuid

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

# Global storage for status updates
status_queues = {}
status_locks = threading.Lock()

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
    """Generate report for selected market and date - async with status updates"""
    try:
        market_symbol = request.form.get('market')
        report_date_str = request.form.get('date')
        
        if not market_symbol:
            return jsonify({'error': 'Please select a market.'}), 400
        
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
            return jsonify({
                'exists': True, 
                'report_id': existing_report.id,
                'message': f'Report for {market_symbol} on {report_date.strftime("%m/%d/%Y")} already exists!'
            }), 200
        
        # Create a unique session ID for this report generation
        session_id = str(uuid.uuid4())
        
        # Create a queue for this session
        with status_locks:
            status_queues[session_id] = queue.Queue()
        
        # Start report generation in background thread
        thread = threading.Thread(
            target=_generate_report_async,
            args=(session_id, market_symbol, report_date)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({'session_id': session_id}), 200
            
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        return jsonify({'error': f'Error generating report: {str(e)}'}), 500

def _send_status(session_id: str, status: str, message: str, progress: int = 0, data: dict = None):
    """Send status update to the queue for a specific session"""
    try:
        with status_locks:
            if session_id in status_queues:
                status_data = {
                    'status': status,
                    'message': message,
                    'progress': progress,
                    'timestamp': datetime.now().isoformat()
                }
                if data:
                    status_data.update(data)
                status_queues[session_id].put(status_data)
                logger.info(f"Status update sent for {session_id}: {message}")
    except Exception as e:
        logger.error(f"Error sending status: {e}")

def _generate_report_async(session_id: str, market_symbol: str, report_date: date):
    """Background task to generate report with status updates"""
    try:
        _send_status(session_id, 'running', 'Starting report generation...', 0)
        
        # Step 1: Scrape economic events
        _send_status(session_id, 'running', 'Scraping economic events from investing.com...', 10)
        events_count = scrape_and_save_events(report_date)
        
        if events_count > 0:
            _send_status(session_id, 'running', f'Scraped {events_count} economic events', 30)
        else:
            _send_status(session_id, 'running', 'Using existing events data', 30)
        
        # Step 2: Analyze events with LLM
        _send_status(session_id, 'running', f'Analyzing events for {market_symbol} market with AI...', 40)
        
        # Get count of events to analyze
        session = get_db_session()
        from models import EconomicEvent
        total_events = session.query(EconomicEvent).filter(EconomicEvent.date == report_date).count()
        session.close()
        
        _send_status(session_id, 'running', f'Starting analysis of {total_events} events...', 45)
        
        # Define progress callback for granular updates
        def analysis_progress(current, total, event_name):
            # Calculate progress within the 45-70% range (25% total for analysis)
            progress = 45 + int((current / total) * 25)
            # Truncate long event names
            display_name = event_name if len(event_name) <= 50 else event_name[:47] + '...'
            _send_status(
                session_id, 
                'running', 
                f'Analyzing event {current}/{total}: {display_name}', 
                progress
            )
        
        analyses = analyze_economic_events(report_date, market_symbol, progress_callback=analysis_progress)
        
        _send_status(session_id, 'running', f'Analyzed {len(analyses)} relevant events for {market_symbol}', 70)
        
        # Step 3: Generate report
        _send_status(session_id, 'running', 'Generating HTML report...', 80)
        report = generate_report(report_date, market_symbol)
        
        if report:
            _send_status(session_id, 'running', 'Report generated successfully!', 90)
            _send_status(session_id, 'complete', 'Report generation complete', 100, {
                'report_id': report['report_id'],
                'events_count': report.get('events_count', 0)
            })
        else:
            _send_status(session_id, 'error', 'Failed to generate report', 0)
            
    except Exception as e:
        logger.error(f"Error in async report generation: {e}")
        _send_status(session_id, 'error', f'Error: {str(e)}', 0)
    finally:
        # Keep the queue alive for a bit to ensure client receives final message
        import time
        time.sleep(2)

@app.route('/status_stream/<session_id>')
def status_stream(session_id):
    """SSE endpoint to stream status updates"""
    def generate():
        try:
            # Wait for queue to be created
            max_wait = 10  # Wait up to 10 seconds
            wait_count = 0
            while session_id not in status_queues and wait_count < max_wait:
                import time
                time.sleep(0.1)
                wait_count += 1
            
            if session_id not in status_queues:
                yield f"data: {json.dumps({'status': 'error', 'message': 'Session not found'})}\n\n"
                return
            
            while True:
                try:
                    # Get status update from queue (timeout after 30 seconds)
                    status_update = status_queues[session_id].get(timeout=30)
                    
                    # Send the update
                    yield f"data: {json.dumps(status_update)}\n\n"
                    
                    # If complete or error, clean up and stop
                    if status_update['status'] in ['complete', 'error']:
                        # Clean up the queue after a delay
                        def cleanup():
                            import time
                            time.sleep(5)
                            with status_locks:
                                if session_id in status_queues:
                                    del status_queues[session_id]
                        
                        cleanup_thread = threading.Thread(target=cleanup)
                        cleanup_thread.daemon = True
                        cleanup_thread.start()
                        break
                        
                except queue.Empty:
                    # Send keep-alive
                    yield f": keep-alive\n\n"
                    
        except Exception as e:
            logger.error(f"Error in status stream: {e}")
            yield f"data: {json.dumps({'status': 'error', 'message': str(e)})}\n\n"
    
    return Response(stream_with_context(generate()), mimetype='text/event-stream')

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
        llm_model = request.form.get('llm_model', 'gpt-4o-mini').strip()
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
            config.llm_model = llm_model
            config.news_sources = news_sources
            config.chart_folder = chart_folder
            config.timezone = timezone
            config.star_filter = star_filter
        else:
            # Create new config
            config = Config(
                llm_api_key=llm_api_key,
                llm_model=llm_model,
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
