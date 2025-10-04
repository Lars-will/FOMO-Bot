from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from datetime import datetime, date, time
from pathlib import Path
import time as time_module
import json
from typing import List, Dict, Optional
import logging
from models import get_db_session, Market, EconomicEvent
from timezone_utils import convert_event_time_to_user_timezone

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EconomicCalendarScraper:
    def __init__(self):
        self.base_url = "https://www.investing.com/economic-calendar/"
        self.driver = None
        
    def _setup_driver(self):
        """Setup Chrome WebDriver with headless options"""
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        
        try:
            self.driver = webdriver.Chrome(options=options)
            return True
        except Exception as e:
            logger.error(f"Error setting up Chrome driver: {e}")
            return False
    
    def _cleanup_driver(self):
        """Clean up the WebDriver"""
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                logger.error(f"Error closing driver: {e}")
            finally:
                self.driver = None
    
    def _events_exist_for_date(self, target_date: date) -> bool:
        """
        Check if events already exist for the given date
        """
        try:
            session = get_db_session()
            event_count = session.query(EconomicEvent).filter(EconomicEvent.date == target_date).count()
            session.close()
            return event_count > 0
        except Exception as e:
            logger.error(f"Error checking existing events: {e}")
            return False
        
    def get_economic_events(self, target_date: date = None) -> List[Dict]:
        """
        Scrape economic events from investing.com for a specific date using Selenium
        Only scrapes once per day - checks if events already exist for the date
        """
        if target_date is None:
            target_date = date.today()
            
        # Check if events already exist for this date
        if self._events_exist_for_date(target_date):
            logger.info(f"Events already exist for {target_date}, skipping scraping")
            return []
            
        logger.info(f"Scraping economic events for {target_date}")
        
        # Setup WebDriver
        if not self._setup_driver():
            logger.error("Failed to setup WebDriver")
            return []
        
        try:
            # Navigate to the economic calendar
            self.driver.get(self.base_url)
            time_module.sleep(5)  # Let JavaScript load fully
            
            # Parse the page source with BeautifulSoup
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            events = []
            # Use the CSS selector from your working code
            for row in soup.select("tr.js-event-item"):
                try:
                    event_data = self._parse_event_row_selenium(row, target_date)
                    if event_data:
                        events.append(event_data)
                except Exception as e:
                    logger.error(f"Error parsing event row: {e}")
                    continue
            
            logger.info(f"Scraped {len(events)} economic events")
            return events
            
        except Exception as e:
            logger.error(f"Error during scraping: {e}")
            return []
        finally:
            self._cleanup_driver()
    
    def _parse_event_row_selenium(self, row, target_date: date) -> Optional[Dict]:
        """
        Parse a single event row using the Selenium-based approach
        No market filtering - all events are saved
        """
        try:
            # Extract data using the selectors from your working code
            event_time_elem = row.select_one(".time")
            currency_elem = row.select_one(".left.flagCur")
            event_name_elem = row.select_one(".event")
            
            # Count the ACTIVE bull icons for importance
            importance_bulls = len(row.select(".sentiment i.grayFullBullishIcon"))
            
            # Extract actual, forecast, previous values
            actual_elem = row.select_one("td[class*='act']")
            forecast_elem = row.select_one("td[class*='fore']")
            previous_elem = row.select_one("td[class*='prev']")
            
            # Extract text values
            time_text = event_time_elem.get_text(strip=True) if event_time_elem else ""
            currency = currency_elem.get_text(strip=True) if currency_elem else ""
            event_name = event_name_elem.get_text(strip=True) if event_name_elem else ""
            actual = actual_elem.get_text(strip=True) if actual_elem else ""
            forecast = forecast_elem.get_text(strip=True) if forecast_elem else ""
            previous = previous_elem.get_text(strip=True) if previous_elem else ""
            
            # Convert importance count to text
            importance = self._convert_importance_count(importance_bulls)
            
            # Parse time
            event_time = self._parse_time(time_text)
            
            # Convert time to user's configured timezone
            # investing.com times are typically in UTC or GMT
            converted_time = convert_event_time_to_user_timezone(
                event_time, 
                target_date, 
                source_timezone='UTC'  # investing.com typically uses UTC
            )
            
            # Don't set market_id - events are market-agnostic
            # LLM will determine relevance later
            
            return {
                'date': target_date,
                'market_id': None,  # No market filtering at scraping level
                'time': converted_time,  # Use converted time
                'currency': currency,
                'importance': importance,
                'event_name': event_name,
                'actual': actual if actual and actual != '-' else None,
                'forecast': forecast if forecast and forecast != '-' else None,
                'previous': previous if previous and previous != '-' else None,
                'source_url': f"https://www.investing.com/economic-calendar/"
            }
            
        except Exception as e:
            logger.error(f"Error parsing event row: {e}")
            return None
    
    def _parse_time(self, time_text: str) -> Optional[time]:
        """
        Parse time string to time object
        """
        try:
            if not time_text or time_text == 'All Day':
                return None
            
            # Handle different time formats
            if ':' in time_text:
                time_part = time_text.split()[0]  # Get time part before AM/PM
                if 'AM' in time_text or 'PM' in time_text:
                    return datetime.strptime(time_text, '%I:%M %p').time()
                else:
                    return datetime.strptime(time_part, '%H:%M').time()
            return None
        except:
            return None
    
    def _convert_importance_count(self, bull_count: int) -> str:
        """
        Convert bull icon count to importance level
        """
        if bull_count >= 3:
            return 'High'
        elif bull_count == 2:
            return 'Medium'
        else:
            return 'Low'
    
    def _get_market_id(self, market_symbol: str) -> Optional[int]:
        """
        Get market_id from database for given symbol using ORM
        """
        try:
            session = get_db_session()
            market = session.query(Market).filter(Market.symbol == market_symbol).first()
            session.close()
            return market.id if market else None
        except Exception as e:
            logger.error(f"Error getting market_id: {e}")
            return None
    
    
    def save_events_to_db(self, events: List[Dict]) -> int:
        """
        Save scraped events to database using ORM
        """
        if not events:
            return 0
            
        try:
            session = get_db_session()
            saved_count = 0
            
            for event_data in events:
                try:
                    # Check if event already exists
                    existing_event = session.query(EconomicEvent).filter(
                        EconomicEvent.date == event_data['date'],
                        EconomicEvent.event_name == event_data['event_name'],
                        EconomicEvent.time == event_data['time']
                    ).first()
                    
                    if existing_event:
                        # Update existing event
                        existing_event.market_id = event_data['market_id']
                        existing_event.currency = event_data['currency']
                        existing_event.importance = event_data['importance']
                        existing_event.actual = event_data['actual']
                        existing_event.forecast = event_data['forecast']
                        existing_event.previous = event_data['previous']
                        existing_event.source_url = event_data['source_url']
                    else:
                        # Create new event
                        event = EconomicEvent(
                            date=event_data['date'],
                            market_id=event_data['market_id'],
                            time=event_data['time'],
                            currency=event_data['currency'],
                            importance=event_data['importance'],
                            event_name=event_data['event_name'],
                            actual=event_data['actual'],
                            forecast=event_data['forecast'],
                            previous=event_data['previous'],
                            source_url=event_data['source_url']
                        )
                        session.add(event)
                    
                    saved_count += 1
                except Exception as e:
                    logger.error(f"Error saving event: {e}")
                    continue
            
            session.commit()
            session.close()
            
            logger.info(f"Saved {saved_count} events to database")
            return saved_count
            
        except Exception as e:
            logger.error(f"Error saving events to database: {e}")
            return 0

def scrape_and_save_events(target_date: date = None) -> int:
    """
    Convenience function to scrape and save economic events
    """
    scraper = EconomicCalendarScraper()
    events = scraper.get_economic_events(target_date)
    return scraper.save_events_to_db(events)

if __name__ == "__main__":
    # Test the scraper
    print("Testing Economic Calendar Scraper...")
    events_count = scrape_and_save_events()
    print(f"Scraped and saved {events_count} events")
