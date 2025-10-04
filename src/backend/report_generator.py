from datetime import datetime, date
from typing import Dict, List, Optional
import logging
from models import get_db_session, Market, EconomicEvent, EventAnalysis, Report

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ReportGenerator:
    def __init__(self):
        pass
    
    def generate_economic_calendar_report(self, target_date: date, market_symbol: str) -> Optional[Dict]:
        """
        Generate HTML report for economic calendar analysis
        """
        try:
            # Get market information
            market_data = self._get_market_data(market_symbol)
            if not market_data:
                logger.error(f"Market {market_symbol} not found")
                return None
            
            # Get events and analyses for the date
            events_data = self._get_events_with_analyses(target_date, market_symbol)
            
            # Generate HTML report
            html_content = self._create_html_report(target_date, market_data, events_data)
            
            # Save report to database
            report_id = self._save_report_to_db(target_date, market_data['id'], html_content)
            
            return {
                'report_id': report_id,
                'date': target_date,
                'market_symbol': market_symbol,
                'html_content': html_content,
                'events_count': len(events_data)
            }
            
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            return None
    
    def _get_market_data(self, market_symbol: str) -> Optional[Dict]:
        """
        Get market data from database using ORM
        """
        try:
            session = get_db_session()
            market = session.query(Market).filter(Market.symbol == market_symbol).first()
            session.close()
            
            if not market:
                return None
            
            return {
                'id': market.id,
                'symbol': market.symbol,
                'description': market.description
            }
        except Exception as e:
            logger.error(f"Error getting market data: {e}")
            return None
    
    def _get_events_with_analyses(self, target_date: date, market_symbol: str) -> List[Dict]:
        """
        Get events with their analyses for a specific date and market using ORM
        """
        try:
            session = get_db_session()
            
            # Get all events for the date (no market filtering at DB level)
            events = session.query(EconomicEvent).filter(
                EconomicEvent.date == target_date
            ).order_by(EconomicEvent.time.asc(), EconomicEvent.importance.desc()).all()
            
            events_data = []
            for event in events:
                # Get the latest analysis for this event and market
                analysis = session.query(EventAnalysis).filter(
                    EventAnalysis.event_id == event.id,
                    EventAnalysis.market_symbol == market_symbol
                ).order_by(EventAnalysis.created_at.desc()).first()
                
                # Only include events that have been analyzed (relevant for this market)
                if analysis:
                    events_data.append({
                        'id': event.id,
                        'time': event.time,
                        'currency': event.currency,
                        'importance': event.importance,
                        'event_name': event.event_name,
                        'actual': event.actual,
                        'forecast': event.forecast,
                        'previous': event.previous,
                        'source_url': event.source_url,
                        'event_description': analysis.event_description,
                        'analysis_text': analysis.analysis_text,
                        'impact_score': analysis.impact_score,
                        'sentiment_summary': analysis.sentiment_summary,
                        'search_sources': analysis.search_sources,
                        'expert_commentary': analysis.expert_commentary,
                        'analysis_created_at': analysis.created_at
                    })
            
            session.close()
            return events_data
            
        except Exception as e:
            logger.error(f"Error getting events with analyses: {e}")
            return []
    
    
    def _create_html_report(self, target_date: date, market_data: Dict, events_data: List[Dict]) -> str:
        """
        Create HTML report content
        """
        # Calculate summary statistics
        total_events = len(events_data)
        high_impact_events = len([e for e in events_data if e['importance'] == 'High'])
        analyzed_events = len([e for e in events_data if e['analysis_text']])
        
        # Get sentiment distribution
        sentiments = [e['sentiment_summary'] for e in events_data if e['sentiment_summary']]
        sentiment_counts = {
            'bullish': sentiments.count('bullish'),
            'bearish': sentiments.count('bearish'),
            'neutral': sentiments.count('neutral')
        }
        
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FOMO Bot Report - {market_data['symbol']} - {target_date}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
            color: #333;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }}
        .header .subtitle {{
            margin: 10px 0 0 0;
            font-size: 1.2em;
            opacity: 0.9;
        }}
        .summary {{
            padding: 30px;
            background: #f8f9fa;
            border-bottom: 1px solid #dee2e6;
        }}
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}
        .summary-card {{
            background: white;
            padding: 20px;
            border-radius: 6px;
            text-align: center;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        .summary-card h3 {{
            margin: 0 0 10px 0;
            color: #667eea;
            font-size: 2em;
        }}
        .summary-card p {{
            margin: 0;
            color: #666;
            font-size: 0.9em;
        }}
        .events-section {{
            padding: 30px;
        }}
        .events-section h2 {{
            color: #333;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
            margin-bottom: 30px;
        }}
        .event-card {{
            background: white;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            margin-bottom: 20px;
            overflow: hidden;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        .event-header {{
            background: #f8f9fa;
            padding: 15px 20px;
            border-bottom: 1px solid #dee2e6;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .event-time-container {{
            display: flex;
            flex-direction: column;
            align-items: flex-start;
        }}
        .time-label {{
            font-size: 0.8em;
            color: #666;
            margin-bottom: 2px;
            font-weight: 500;
        }}
        .event-time {{
            font-weight: bold;
            color: #667eea;
        }}
        .importance-container {{
            display: flex;
            flex-direction: column;
            align-items: flex-end;
        }}
        .importance-label {{
            font-size: 0.8em;
            color: #666;
            margin-bottom: 2px;
            font-weight: 500;
        }}
        .importance-badge {{
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: bold;
            text-transform: uppercase;
        }}
        .importance-high {{
            background: #dc3545;
            color: white;
        }}
        .importance-medium {{
            background: #ffc107;
            color: #333;
        }}
        .importance-low {{
            background: #28a745;
            color: white;
        }}
        .event-content {{
            padding: 20px;
        }}
        .event-title {{
            font-size: 1.2em;
            font-weight: bold;
            margin-bottom: 10px;
            color: #333;
        }}
        .event-details {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-bottom: 15px;
        }}
        .detail-item {{
            background: #f8f9fa;
            padding: 10px;
            border-radius: 4px;
        }}
        .detail-label {{
            font-size: 0.8em;
            color: #666;
            text-transform: uppercase;
            margin-bottom: 5px;
        }}
        .detail-value {{
            font-weight: bold;
            color: #333;
        }}
        .analysis {{
            background: #e3f2fd;
            border-left: 4px solid #2196f3;
            padding: 15px;
            margin-top: 15px;
            border-radius: 0 4px 4px 0;
        }}
        .analysis h4 {{
            margin: 0 0 10px 0;
            color: #1976d2;
        }}
        .analysis-metrics {{
            display: flex;
            gap: 20px;
            margin-bottom: 15px;
            flex-wrap: wrap;
        }}
        .metric-item {{
            display: flex;
            flex-direction: column;
            gap: 5px;
            min-width: 150px;
        }}
        .metric-label {{
            font-size: 0.9em;
            color: #666;
            font-weight: 500;
        }}
        .analysis-content {{
            margin-top: 10px;
        }}
        .expert-commentary {{
            background: #f3e5f5;
            border-left: 4px solid #9c27b0;
            padding: 15px;
            margin-top: 15px;
            border-radius: 0 4px 4px 0;
        }}
        .expert-commentary h4 {{
            margin: 0 0 10px 0;
            color: #7b1fa2;
        }}
        .commentary-content {{
            margin-top: 10px;
        }}
        .key-factors {{
            margin-top: 10px;
            padding: 10px;
            background: #e9ecef;
            border-radius: 3px;
        }}
        .key-factors ul {{
            margin: 5px 0 0 0;
            padding-left: 20px;
        }}
        .key-factors li {{
            margin-bottom: 3px;
        }}
        .event-description {{
            background: #f0f8ff;
            border-left: 4px solid #2196f3;
            padding: 15px;
            margin-top: 15px;
            border-radius: 0 4px 4px 0;
        }}
        .event-description h4 {{
            margin: 0 0 10px 0;
            color: #1976d2;
            font-size: 1em;
        }}
        .event-description p {{
            margin: 0;
            color: #333;
            line-height: 1.5;
        }}
        .impact-score {{
            display: inline-block;
            color: white;
            padding: 6px 12px;
            border-radius: 15px;
            font-size: 0.9em;
            font-weight: bold;
            text-align: center;
            min-width: 80px;
        }}
        .impact-low {{
            background: #4caf50;
        }}
        .impact-medium {{
            background: #ff9800;
        }}
        .impact-high {{
            background: #f44336;
        }}
        .sentiment {{
            display: inline-block;
            padding: 6px 12px;
            border-radius: 15px;
            font-size: 0.9em;
            font-weight: bold;
            text-align: center;
            min-width: 80px;
        }}
        .sentiment-bullish {{
            background: #4caf50;
            color: white;
        }}
        .sentiment-bearish {{
            background: #f44336;
            color: white;
        }}
        .sentiment-neutral {{
            background: #9e9e9e;
            color: white;
        }}
        .footer {{
            background: #333;
            color: white;
            padding: 20px;
            text-align: center;
            font-size: 0.9em;
        }}
        .no-events {{
            text-align: center;
            padding: 40px;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>FOMO Bot Report</h1>
            <div class="subtitle">{market_data['symbol']} - {target_date.strftime('%d.%m.%Y')}</div>
        </div>
        
        <div class="summary">
            <h2>Summary</h2>
            <div class="summary-grid">
                <div class="summary-card">
                    <h3>{total_events}</h3>
                    <p>Total Events</p>
                </div>
                <div class="summary-card">
                    <h3>{high_impact_events}</h3>
                    <p>High Impact</p>
                </div>
                <div class="summary-card">
                    <h3>{analyzed_events}</h3>
                    <p>Analysiert</p>
                </div>
                <div class="summary-card">
                    <h3>{sentiment_counts['bullish']}/{sentiment_counts['bearish']}/{sentiment_counts['neutral']}</h3>
                    <p>Bullish/Bearish/Neutral</p>
                </div>
            </div>
        </div>
        
        <div class="events-section">
            <h2>Economic Calendar Events</h2>
"""
        
        if not events_data:
            html += """
            <div class="no-events">
                <h3>No Events Found</h3>
                <p>No economic events were found for this day.</p>
            </div>
"""
        else:
            for event in events_data:
                importance_class = f"importance-{event['importance'].lower()}"
                sentiment_class = f"sentiment-{event['sentiment_summary']}" if event['sentiment_summary'] else "sentiment-neutral"
                
                html += f"""
            <div class="event-card">
                <div class="event-header">
                    <div class="event-time-container">
                        <div class="time-label">🕐 Time</div>
                        <div class="event-time">{event['time'] or 'All Day'}</div>
                    </div>
                    <div class="importance-container">
                        <div class="importance-label">📊 Importance</div>
                        <div class="importance-badge {importance_class}">{event['importance']}</div>
                    </div>
                </div>
                <div class="event-content">
                    <div class="event-title">{event['event_name']}</div>
                    <div class="event-details">
                        <div class="detail-item">
                            <div class="detail-label">Currency</div>
                            <div class="detail-value">{event['currency']}</div>
                        </div>
                        <div class="detail-item">
                            <div class="detail-label">Actual</div>
                            <div class="detail-value">{event['actual'] or 'N/A'}</div>
                        </div>
                        <div class="detail-item">
                            <div class="detail-label">Forecast</div>
                            <div class="detail-value">{event['forecast'] or 'N/A'}</div>
                        </div>
                        <div class="detail-item">
                            <div class="detail-label">Previous</div>
                            <div class="detail-value">{event['previous'] or 'N/A'}</div>
                        </div>
                    </div>
"""
                
                # Add event description section before analysis
                if event.get('event_description') and event['event_description'].strip():
                    html += f"""
                    <div class="event-description">
                        <h4>📋 Event Description</h4>
                        <p>{event['event_description']}</p>
                    </div>
"""
                
                if event['analysis_text']:
                    # Try to parse analysis_text as JSON, if it fails, use as plain text
                    analysis_display = event['analysis_text']
                    try:
                        import json
                        if event['analysis_text'].strip().startswith('{'):
                            parsed_analysis = json.loads(event['analysis_text'])
                            analysis_display = parsed_analysis.get('analysis_text', event['analysis_text'])
                    except:
                        pass  # Use original text if parsing fails
                    
                    # Get key factors if available
                    key_factors = event.get('search_sources', [])
                    if isinstance(key_factors, list) and key_factors:
                        factors_html = "<div class='key-factors'><strong>Key Factors:</strong><ul>"
                        for factor in key_factors:
                            factors_html += f"<li>{factor}</li>"
                        factors_html += "</ul></div>"
                    else:
                        factors_html = ""
                    
                    # Create impact level description
                    impact_score = event['impact_score']
                    if impact_score <= 3:
                        impact_level = "Low"
                        impact_description = "Low impact on the market"
                    elif impact_score <= 6:
                        impact_level = "Medium"
                        impact_description = "Moderate impact on the market"
                    else:
                        impact_level = "High"
                        impact_description = "Strong impact on the market"
                    
                    # Create sentiment description
                    sentiment = event['sentiment_summary'] or 'neutral'
                    sentiment_descriptions = {
                        'bullish': 'Positive - Expectation of rising prices',
                        'bearish': 'Negative - Expectation of falling prices',
                        'neutral': 'Neutral - No clear direction'
                    }
                    sentiment_description = sentiment_descriptions.get(sentiment, 'Neutral - No clear direction')
                    
                    html += f"""
                    <div class="analysis">
                        <h4>🤖 AI Analysis</h4>
                        <div class="analysis-metrics">
                            <div class="metric-item" title="{impact_description}">
                                <span class="metric-label">📊 Market Impact:</span>
                                <span class="impact-score impact-{impact_level.lower()}">{impact_level} ({impact_score}/10)</span>
                            </div>
                            <div class="metric-item" title="{sentiment_description}">
                                <span class="metric-label">📈 Market Sentiment:</span>
                                <span class="sentiment {sentiment_class}">{sentiment.title()}</span>
                            </div>
                        </div>
                        <div class="analysis-content">
                            <p>{analysis_display}</p>
                            {factors_html}
                        </div>
                    </div>
"""
                
                # Add expert commentary section if available
                if event.get('expert_commentary') and event['expert_commentary'].strip():
                    html += f"""
                    <div class="expert-commentary">
                        <h4>💬 Expert Commentary</h4>
                        <div class="commentary-content">
                            <p>{event['expert_commentary']}</p>
                        </div>
                    </div>
"""
                
                html += """
                </div>
            </div>
"""
        
        # Get current timestamp for footer
        current_time = datetime.now().strftime('%m/%d/%Y at %H:%M')
        
        html += f"""
        </div>
        
        <div class="footer">
            <p>Generated by FOMO Bot on {current_time}</p>
        </div>
    </div>
</body>
</html>
"""
        
        return html
    
    def _save_report_to_db(self, target_date: date, market_id: int, html_content: str) -> Optional[int]:
        """
        Save report to database using ORM
        """
        try:
            session = get_db_session()
            
            report = Report(
                date=target_date,
                market_id=market_id,
                report_html=html_content
            )
            
            session.add(report)
            session.commit()
            report_id = report.id
            session.close()
            
            logger.info(f"Saved report for {target_date} with ID {report_id}")
            return report_id
            
        except Exception as e:
            logger.error(f"Error saving report: {e}")
            return None
    
    def get_report(self, report_id: int) -> Optional[Dict]:
        """
        Get report by ID using ORM
        """
        try:
            session = get_db_session()
            report = session.query(Report).join(Market).filter(Report.id == report_id).first()
            
            if not report:
                session.close()
                return None
            
            # Extract data while session is still open
            result = {
                'id': report.id,
                'date': report.date,
                'market_id': report.market_id,
                'report_html': report.report_html,
                'created_at': report.created_at,
                'market_symbol': report.market.symbol,
                'market_description': report.market.description
            }
            
            session.close()
            return result
            
        except Exception as e:
            logger.error(f"Error getting report: {e}")
            return None

def generate_report(target_date: date = None, market_symbol: str = "FDAX") -> Optional[Dict]:
    """
    Convenience function to generate a report
    """
    if target_date is None:
        target_date = date.today()
    
    generator = ReportGenerator()
    return generator.generate_economic_calendar_report(target_date, market_symbol)

if __name__ == "__main__":
    # Test the report generator
    print("Testing Report Generator...")
    report = generate_report()
    if report:
        print(f"Generated report with ID {report['report_id']}")
        print(f"Report contains {report['events_count']} events")
    else:
        print("Failed to generate report")
