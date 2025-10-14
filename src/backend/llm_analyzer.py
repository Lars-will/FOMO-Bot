import json
import requests
from datetime import datetime, date
from typing import Dict, List, Optional
import logging
import time
from models import get_db_session, Config, EconomicEvent, EventAnalysis, Market

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMAnalyzer:
    # Class-level rate limiting to ensure it works across all instances
    _last_api_call_time = 0
    _min_request_interval = 1.0  # Minimum 1.0 second between requests
    _rate_limit_lock = None  # Will be initialized when needed
    
    def __init__(self):
        self.api_key = self._get_api_key()
        self.model = self._get_llm_model()
        # Initialize lock for thread safety if not already done
        if LLMAnalyzer._rate_limit_lock is None:
            import threading
            LLMAnalyzer._rate_limit_lock = threading.Lock()
        
    def _enforce_rate_limit(self):
        """
        Enforce rate limiting to respect API subscription limits (1.0 second delay between requests)
        Uses class-level variables to ensure rate limiting works across all instances
        """
        with LLMAnalyzer._rate_limit_lock:
            current_time = time.time()
            time_since_last_call = current_time - LLMAnalyzer._last_api_call_time
            
            logger.info(f"Rate limiting check: {time_since_last_call:.2f}s since last call, need {LLMAnalyzer._min_request_interval}s")
            
            if time_since_last_call < LLMAnalyzer._min_request_interval:
                sleep_time = LLMAnalyzer._min_request_interval - time_since_last_call
                logger.info(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
                logger.info(f"Rate limiting: sleep completed, proceeding with API call")
            else:
                logger.info(f"Rate limiting: no sleep needed, proceeding with API call")
            
            # Don't update last_api_call_time here - it will be updated after the actual API call
        
    def _get_api_key(self) -> Optional[str]:
        """
        Get LLM API key from database config using ORM
        """
        try:
            session = get_db_session()
            config = session.query(Config).order_by(Config.created_at.desc()).first()
            session.close()
            return config.llm_api_key if config else None
        except Exception as e:
            logger.error(f"Error getting API key: {e}")
            return None
    
    def _get_llm_model(self) -> str:
        """
        Get configured LLM model from database config using ORM
        """
        try:
            session = get_db_session()
            config = session.query(Config).order_by(Config.created_at.desc()).first()
            session.close()
            return config.llm_model if config and config.llm_model else 'gpt-4o-mini'
        except Exception as e:
            logger.error(f"Error getting LLM model: {e}")
            return 'gpt-4o-mini'  # Default fallback
    
    def _get_star_filter(self) -> int:
        """
        Get star filter setting from database config
        """
        try:
            session = get_db_session()
            config = session.query(Config).order_by(Config.created_at.desc()).first()
            session.close()
            
            if config and config.star_filter:
                return config.star_filter
            else:
                return 1  # Default to analyze all events
                
        except Exception as e:
            logger.error(f"Error getting star filter: {e}")
            return 1  # Default to analyze all events
    
    def _get_event_importance(self, importance_str: str) -> int:
        """
        Convert importance string to numeric value for filtering
        """
        importance_map = {
            'Low': 1,
            'Medium': 2,
            'High': 3
        }
        return importance_map.get(importance_str, 1)  # Default to Low if unknown
    
    def analyze_economic_event(self, event_id: int, market_symbol: str) -> Optional[Dict]:
        """
        Analyze a single economic event using LLM for a specific market
        """
        try:
            # Check if analysis already exists for this event and market
            session = get_db_session()
            existing_analysis = session.query(EventAnalysis).filter(
                EventAnalysis.event_id == event_id,
                EventAnalysis.market_symbol == market_symbol
            ).order_by(EventAnalysis.created_at.desc()).first()
            session.close()
            
            if existing_analysis:
                logger.info(f"Analysis already exists for event {event_id} and market {market_symbol}, skipping LLM analysis")
                # Return existing analysis data
                return {
                    'is_relevant': True,  # Assume existing analysis is relevant
                    'event_description': existing_analysis.event_description or '',
                    'analysis_text': existing_analysis.analysis_text,
                    'impact_score': existing_analysis.impact_score,
                    'sentiment_summary': existing_analysis.sentiment_summary,
                    'key_factors': existing_analysis.search_sources or [],
                    'expert_commentary': existing_analysis.expert_commentary or ''
                }
            
            # Get event details from database
            event_data = self._get_event_data(event_id)
            if not event_data:
                logger.error(f"Event with ID {event_id} not found")
                return None
            
            # Check star filter - only analyze events with sufficient importance
            star_filter = self._get_star_filter()
            event_importance = self._get_event_importance(event_data['importance'])
            
            if event_importance < star_filter:
                logger.info(f"Event {event_id} importance ({event_importance}) below filter threshold ({star_filter}), skipping analysis")
                return None
            
            # Create analysis prompt with market context
            prompt = self._create_analysis_prompt(event_data, market_symbol)
            
            # Get LLM analysis
            analysis = self._call_llm_api(prompt)
            if not analysis:
                logger.error("Failed to get LLM analysis")
                return None
            
            # Parse and structure the analysis
            structured_analysis = self._parse_analysis(analysis, event_data)
            
            # Check if event is relevant for this market
            if not structured_analysis.get('is_relevant', True):
                logger.info(f"Event {event_id} not relevant for {market_symbol}, skipping analysis")
                return None
            
            # Save analysis to database
            analysis_id = self._save_analysis_to_db(event_id, market_symbol, structured_analysis)
            
            return {
                'analysis_id': analysis_id,
                'event_id': event_id,
                'analysis': structured_analysis
            }
            
        except Exception as e:
            logger.error(f"Error analyzing event {event_id}: {e}")
            return None
    
    def _get_event_data(self, event_id: int) -> Optional[Dict]:
        """
        Get event data from database using ORM
        """
        try:
            session = get_db_session()
            event = session.query(EconomicEvent).filter(EconomicEvent.id == event_id).first()
            session.close()
            
            if not event:
                return None
            
            return {
                'id': event.id,
                'date': event.date,
                'market_id': event.market_id,
                'time': event.time,
                'currency': event.currency,
                'importance': event.importance,
                'event_name': event.event_name,
                'actual': event.actual,
                'forecast': event.forecast,
                'previous': event.previous,
                'source_url': event.source_url,
                'market_symbol': None  # Will be determined by LLM analysis
            }
        except Exception as e:
            logger.error(f"Error getting event data: {e}")
            return None
    
    def _search_expert_commentary(self, event_name: str, market_symbol: str) -> str:
        """
        Simplified expert commentary - let LLM decide analysis approach
        """
        return f"Analyze {event_name} impact on {market_symbol} market with expert-level insights."

    # Removed hardcoded context generation methods - let LLM decide analysis approach


    def _create_analysis_prompt(self, event_data: Dict, market_symbol: str) -> str:
        """
        Create analysis prompt for LLM
        """
        prompt = f"""
Analyze this economic event for {market_symbol} market impact:

Event: {event_data['event_name']}
Date: {event_data['date']}
Time: {event_data['time']}
Region (given by the currency): {event_data['currency']}
Actual: {event_data['actual'] or 'Not released yet'}
Forecast: {event_data['forecast'] or 'N/A'}
Previous: {event_data['previous'] or 'N/A'}

Provide analysis focused on {market_symbol} only. Determine relevance, impact, and trading implications.

Output as JSON:
{{
    "is_relevant": true/false,
    "event_description": "Brief explanation of the event and why it matters for {market_symbol}",
    "analysis_text": "Concise analysis focused on {market_symbol} impact and trading implications",
    "impact_score": 1-10,
    "sentiment_summary": "bullish/bearish/neutral",
    "key_factors": ["factor1", "factor2", "factor3"],
    "expert_commentary": "Expert-level commentary on {market_symbol} market implications. Do a web search go get real time information on this"
}}
"""
        return prompt
    
    def _call_llm_api(self, prompt: str) -> Optional[str]:
        """
        Call LLM API (OpenAI GPT-4 or similar)
        """
        if not self.api_key:
            logger.error("No API key configured")
            return None
        
        # Enforce rate limiting before making API call
        self._enforce_rate_limit()
        
        logger.info(f"Making API call to OpenAI at {time.time():.2f}")
        
        try:
            # Using OpenAI API as default
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'model': self.model,
                'messages': [
                    {
                        'role': 'system',
                        'content': 'You are a professional financial analyst specializing in economic events and market impact analysis. Provide concise, actionable insights.'
                    },
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                'max_tokens': 500,
                'temperature': 0.3
            }
            
            logger.info(f"Using LLM model: {self.model}")
            
            response = requests.post(
                'https://api.openai.com/v1/chat/completions',
                headers=headers,
                json=data,
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            
            # Update timestamp after successful API call (class-level)
            LLMAnalyzer._last_api_call_time = time.time()
            logger.info(f"API call successful, timestamp updated to {LLMAnalyzer._last_api_call_time:.2f}")
            
            return result['choices'][0]['message']['content']
            
        except requests.RequestException as e:
            logger.error(f"API request failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Error calling LLM API: {e}")
            return None
    
    def _parse_analysis(self, analysis_text: str, event_data: Dict) -> Dict:
        """
        Parse LLM analysis response
        """
        try:
            # Clean the response text - remove markdown code blocks
            cleaned_text = analysis_text.strip()
            if cleaned_text.startswith('```json'):
                cleaned_text = cleaned_text[7:]  # Remove ```json
            if cleaned_text.endswith('```'):
                cleaned_text = cleaned_text[:-3]  # Remove ```
            cleaned_text = cleaned_text.strip()
            
            # Try to parse as JSON first
            if cleaned_text.startswith('{'):
                parsed_json = json.loads(cleaned_text)
                logger.info(f"Successfully parsed JSON analysis: {parsed_json.get('is_relevant', 'unknown')} relevance")
                return parsed_json
            
            # Fallback: extract information from text
            lines = analysis_text.split('\n')
            analysis = {
                'event_description': 'Event description not available in this format.',
                'analysis_text': analysis_text,
                'impact_score': 5,  # Default medium impact
                'sentiment_summary': 'neutral',
                'key_factors': [],
                'expert_commentary': 'Expert commentary not available in this format.'
            }
            
            # Try to extract impact score
            for line in lines:
                if 'impact' in line.lower() and any(char.isdigit() for char in line):
                    try:
                        score = int(''.join(filter(str.isdigit, line)))
                        if 1 <= score <= 10:
                            analysis['impact_score'] = score
                    except:
                        pass
            
            # Try to extract sentiment
            text_lower = analysis_text.lower()
            if 'bullish' in text_lower:
                analysis['sentiment_summary'] = 'bullish'
            elif 'bearish' in text_lower:
                analysis['sentiment_summary'] = 'bearish'
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error parsing analysis: {e}")
            logger.error(f"Raw analysis text: {analysis_text[:200]}...")
            return {
                'event_description': 'Event description not available due to parsing error.',
                'analysis_text': analysis_text,
                'impact_score': 5,
                'sentiment_summary': 'neutral',
                'key_factors': [],
                'expert_commentary': 'Expert commentary not available due to parsing error.'
            }
    
    def _save_analysis_to_db(self, event_id: int, market_symbol: str, analysis: Dict) -> Optional[int]:
        """
        Save analysis to database using ORM
        """
        try:
            session = get_db_session()
            
            event_analysis = EventAnalysis(
                event_id=event_id,
                market_symbol=market_symbol,
                event_description=analysis.get('event_description', ''),
                analysis_text=analysis['analysis_text'],
                impact_score=analysis['impact_score'],
                sentiment_summary=analysis['sentiment_summary'],
                search_sources=analysis.get('key_factors', []),
                expert_commentary=analysis.get('expert_commentary', '')
            )
            
            session.add(event_analysis)
            session.commit()
            analysis_id = event_analysis.id
            session.close()
            
            logger.info(f"Saved analysis for event {event_id}")
            return analysis_id
            
        except Exception as e:
            logger.error(f"Error saving analysis: {e}")
            return None
    
    def analyze_events_for_date(self, target_date: date, market_symbol: str, progress_callback=None) -> List[Dict]:
        """
        Analyze all events for a specific date and market using ORM
        
        Args:
            target_date: Date to analyze events for
            market_symbol: Market symbol to analyze for
            progress_callback: Optional callback function(current, total, event_name) to report progress
        """
        try:
            # Get all events for the date (no market filtering at DB level)
            session = get_db_session()
            events = session.query(EconomicEvent).filter(EconomicEvent.date == target_date).all()
            session.close()
            
            total_events = len(events)
            
            # Analyze each event for the specific market
            analyses = []
            for idx, event in enumerate(events, 1):
                # Report progress before analyzing
                if progress_callback:
                    progress_callback(idx, total_events, event.event_name)
                
                analysis = self.analyze_economic_event(event.id, market_symbol)
                if analysis:
                    analyses.append(analysis)
            
            logger.info(f"Analyzed {len(analyses)} relevant events for {market_symbol} on {target_date}")
            return analyses
            
        except Exception as e:
            logger.error(f"Error analyzing events for date: {e}")
            return []

def analyze_economic_events(target_date: date = None, market_symbol: str = "FDAX", progress_callback=None) -> List[Dict]:
    """
    Convenience function to analyze economic events
    
    Args:
        target_date: Date to analyze events for
        market_symbol: Market symbol to analyze for
        progress_callback: Optional callback function(current, total, event_name) to report progress
    """
    if target_date is None:
        target_date = date.today()
    
    analyzer = LLMAnalyzer()
    return analyzer.analyze_events_for_date(target_date, market_symbol, progress_callback)

if __name__ == "__main__":
    # Test the analyzer
    print("Testing LLM Analyzer...")
    analyses = analyze_economic_events()
    print(f"Analyzed {len(analyses)} events")
