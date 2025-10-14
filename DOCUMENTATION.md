# FOMO Bot - Complete Code Documentation

## Table of Contents
1. [Overview](#overview)
2. [Application Entry Point](#application-entry-point)
3. [Backend Modules](#backend-modules)
4. [Frontend Application](#frontend-application)

---

## Overview

FOMO Bot is a trading analysis tool that scrapes economic calendar events, analyzes them using AI/LLM, and generates comprehensive trading reports. The application is built with Python, Flask, SQLAlchemy, and Selenium.

**Technology Stack:**
- **Backend**: Python 3.x, SQLAlchemy ORM, SQLite
- **Frontend**: Flask, Jinja2 Templates, Bootstrap
- **Data Collection**: Selenium WebDriver (Chrome)
- **AI Analysis**: OpenAI GPT-4o-mini API
- **Libraries**: requests, pytz, BeautifulSoup4

---

## Application Entry Point

### `src/run.py`

**Purpose**: Main application entry point that initializes the environment and starts the Flask web server.

#### Functions

##### `setup_environment()`
```python
def setup_environment() -> bool
```

**Description**: Validates the environment before starting the application.

**Process**:
1. Checks if the database file exists
2. Verifies that markets are populated in the database
3. Auto-populates initial markets if none exist

**Returns**:
- `bool`: `True` if environment is ready, `False` otherwise

**Side Effects**:
- Prints status messages to console
- May auto-populate markets if database is empty

**Errors**:
- Returns `False` if database is missing or inaccessible
- Logs errors to console

---

##### `main()`
```python
def main() -> None
```

**Description**: Main entry point that orchestrates the application startup.

**Process**:
1. Calls `setup_environment()` to validate prerequisites
2. Displays startup banner with phase information
3. Imports and starts the Flask application
4. Handles graceful shutdown on KeyboardInterrupt

**Side Effects**:
- Starts Flask web server on `0.0.0.0:5000`
- Runs in debug mode
- Blocks until server is stopped

**Errors**:
- Exits with code 1 if environment setup fails
- Exits with code 1 on unhandled exceptions

---

## Backend Modules

### `src/backend/init_db.py`

**Purpose**: Database initialization script that creates or resets the database schema.

#### Functions

##### `setup_database()`
```python
def setup_database() -> None
```

**Description**: Creates or resets the database with all required tables.

**Process**:
1. Determines database path (relative to project root)
2. Prompts user for confirmation (destructive operation)
3. Calls `init_database()` from models module to create tables

**User Interaction**:
- Requires explicit "yes"/"no" confirmation
- Warns about data deletion

**Tables Created**:
- `markets`: Trading markets (FDAX, BTC, SPY, etc.)
- `config`: Application configuration
- `economic_events`: Scraped calendar events
- `event_analyses`: AI-generated event analyses
- `news_items`: Financial news (Phase 2)
- `news_analyses`: News analysis (Phase 2)
- `chart_analyses`: Technical chart analysis (Phase 3)
- `reports`: Generated HTML reports
- `postmortems`: Trading reflections

**Warning**: This is a DESTRUCTIVE operation that deletes all existing data.

---

### `src/backend/models.py`

**Purpose**: SQLAlchemy ORM models and database connection management.

#### Database Models

##### `Market`
```python
class Market(Base)
```

**Description**: Represents a trading market (e.g., FDAX, BTC, SPY).

**Columns**:
- `id` (Integer, PK): Unique identifier
- `symbol` (String(20), Unique, Not Null): Market ticker symbol
- `description` (Text): Human-readable description

**Relationships**:
- `economic_events`: One-to-many with EconomicEvent
- `news_items`: One-to-many with NewsItem
- `chart_analyses`: One-to-many with ChartAnalysis
- `reports`: One-to-many with Report

---

##### `Config`
```python
class Config(Base)
```

**Description**: Application configuration settings.

**Columns**:
- `id` (Integer, PK): Unique identifier
- `llm_api_key` (Text): OpenAI API key for LLM analysis
- `news_sources` (Text): URLs for news scraping (Phase 2)
- `chart_folder` (Text): Path to chart screenshots (Phase 3)
- `timezone` (String(50)): User's timezone (default: Europe/Berlin)
- `star_filter` (Integer): Minimum event importance to analyze (1=Low, 2=Medium, 3=High)
- `created_at` (DateTime): Record creation timestamp

**Configuration Options**:
- **Star Filter**: Controls which events are analyzed based on importance
  - `1`: Analyze all events (Low, Medium, High)
  - `2`: Analyze Medium and High only
  - `3`: Analyze High importance only

---

##### `EconomicEvent`
```python
class EconomicEvent(Base)
```

**Description**: Economic calendar event scraped from investing.com.

**Columns**:
- `id` (Integer, PK): Unique identifier
- `date` (Date, Not Null): Event date
- `market_id` (Integer, FK): Associated market (nullable)
- `time` (Time): Event time (None for all-day events)
- `currency` (String(10)): Currency/region code (USD, EUR, GBP, etc.)
- `importance` (String(10)): Low, Medium, or High
- `event_name` (Text, Not Null): Event name
- `actual` (Text): Actual released value
- `forecast` (Text): Forecasted value
- `previous` (Text): Previous value
- `source_url` (Text): Source URL from investing.com

**Relationships**:
- `market`: Many-to-one with Market
- `analyses`: One-to-many with EventAnalysis

**Notes**:
- Events are market-agnostic at scraping time
- LLM determines market relevance during analysis
- Time is converted to user's configured timezone

---

##### `EventAnalysis`
```python
class EventAnalysis(Base)
```

**Description**: AI-generated analysis of an economic event for a specific market.

**Columns**:
- `id` (Integer, PK): Unique identifier
- `event_id` (Integer, FK): Associated economic event
- `market_symbol` (String(20), Not Null): Target market (e.g., FDAX, BTC)
- `event_description` (Text): LLM-generated event description
- `analysis_text` (Text): Detailed analysis text
- `impact_score` (Integer): Impact rating 1-10
- `sentiment_summary` (String(20)): bullish, bearish, or neutral
- `search_sources` (JSON): Key factors array
- `expert_commentary` (Text): Expert-level market commentary
- `created_at` (DateTime): Analysis timestamp

**Importance**:
- **Market-Specific**: Same event can have different analyses for different markets
- **Unique Constraint**: One analysis per event-market combination

**Relationships**:
- `event`: Many-to-one with EconomicEvent

---

##### `NewsItem` (Phase 2)
```python
class NewsItem(Base)
```

**Description**: Financial news article (future implementation).

**Columns**:
- `id` (Integer, PK): Unique identifier
- `date` (Date, Not Null): Article date
- `market_id` (Integer, FK): Associated market
- `title` (Text): Article title
- `summary` (Text): Article summary
- `url` (Text): Article URL
- `source` (String(100)): News source

**Relationships**:
- `market`: Many-to-one with Market
- `analyses`: One-to-many with NewsAnalysis

---

##### `NewsAnalysis` (Phase 2)
```python
class NewsAnalysis(Base)
```

**Description**: AI analysis of news article (future implementation).

**Columns**:
- `id` (Integer, PK): Unique identifier
- `news_id` (Integer, FK): Associated news item
- `analysis_text` (Text): Analysis content
- `sentiment` (String(20)): bullish, bearish, or neutral
- `impact_score` (Integer): Impact rating 1-10
- `created_at` (DateTime): Analysis timestamp

**Relationships**:
- `news_item`: Many-to-one with NewsItem

---

##### `ChartAnalysis` (Phase 3)
```python
class ChartAnalysis(Base)
```

**Description**: Technical chart analysis (future implementation).

**Columns**:
- `id` (Integer, PK): Unique identifier
- `date` (Date, Not Null): Chart date
- `market_id` (Integer, FK): Associated market
- `timeframe` (String(20)): Chart timeframe (Daily, Hourly, etc.)
- `image_path` (Text): Path to chart image
- `analysis_text` (Text): Technical analysis
- `scenarios` (JSON): Trading scenarios
- `created_at` (DateTime): Analysis timestamp

**Relationships**:
- `market`: Many-to-one with Market

---

##### `Report`
```python
class Report(Base)
```

**Description**: Generated HTML report combining all analyses.

**Columns**:
- `id` (Integer, PK): Unique identifier
- `date` (Date, Not Null): Report date
- `market_id` (Integer, FK): Associated market
- `report_html` (Text): Complete HTML content
- `created_at` (DateTime): Report generation timestamp

**Relationships**:
- `market`: Many-to-one with Market
- `postmortems`: One-to-many with Postmortem

---

##### `Postmortem`
```python
class Postmortem(Base)
```

**Description**: Trading reflection and post-analysis notes.

**Columns**:
- `id` (Integer, PK): Unique identifier
- `report_id` (Integer, FK): Associated report
- `reflection_text` (Text): User's reflection notes
- `created_at` (DateTime): Postmortem timestamp

**Relationships**:
- `report`: Many-to-one with Report

---

#### Utility Functions

##### `get_database_url()`
```python
def get_database_url() -> str
```

**Description**: Constructs the SQLite database URL.

**Returns**:
- `str`: SQLite connection string (e.g., `sqlite:///path/to/fomo-bot-DB.sqlite`)

**Path Logic**:
- Resolves path relative to project root
- Creates `database/fomo-bot-DB.sqlite`

---

##### `create_engine_and_session()`
```python
def create_engine_and_session() -> Tuple[Engine, SessionLocal]
```

**Description**: Creates SQLAlchemy engine and session factory.

**Returns**:
- `Engine`: SQLAlchemy database engine
- `SessionLocal`: Session factory class

**Configuration**:
- `echo=False`: Disables SQL logging
- `autocommit=False`: Requires explicit commits
- `autoflush=False`: Manual flush control

---

##### `get_db_session()`
```python
def get_db_session() -> Session
```

**Description**: Creates a new database session.

**Returns**:
- `Session`: Active SQLAlchemy session

**Usage Pattern**:
```python
session = get_db_session()
try:
    # Database operations
    session.commit()
finally:
    session.close()
```

---

##### `init_database()`
```python
def init_database() -> Engine
```

**Description**: Initializes database schema with all tables.

**Returns**:
- `Engine`: SQLAlchemy database engine

**Side Effects**:
- Creates all tables defined in `Base.metadata`
- Drops and recreates existing tables (destructive)

---

### `src/backend/scraper.py`

**Purpose**: Scrapes economic calendar events from investing.com using Selenium.

#### Class: `EconomicCalendarScraper`

##### `__init__()`
```python
def __init__(self) -> None
```

**Description**: Initializes the scraper instance.

**Attributes**:
- `base_url`: investing.com economic calendar URL
- `driver`: Chrome WebDriver instance (initially None)

---

##### `_setup_driver()`
```python
def _setup_driver(self) -> bool
```

**Description**: Configures and initializes Chrome WebDriver with headless options.

**Chrome Options**:
- `--headless`: Runs without GUI
- `--no-sandbox`: Disables sandbox security (for compatibility)
- `--disable-dev-shm-usage`: Reduces memory usage
- `--disable-gpu`: Disables GPU acceleration
- `--window-size=1920,1080`: Sets viewport size
- Custom user-agent: Mimics real browser

**Returns**:
- `bool`: `True` if setup successful, `False` otherwise

**Side Effects**:
- Sets `self.driver` to WebDriver instance
- Logs errors on failure

---

##### `_cleanup_driver()`
```python
def _cleanup_driver(self) -> None
```

**Description**: Safely closes and cleans up the WebDriver.

**Side Effects**:
- Quits WebDriver if active
- Sets `self.driver` to None
- Logs errors if cleanup fails

---

##### `_events_exist_for_date()`
```python
def _events_exist_for_date(self, target_date: date) -> bool
```

**Description**: Checks if events have already been scraped for a given date.

**Parameters**:
- `target_date` (date): Date to check

**Returns**:
- `bool`: `True` if events exist, `False` otherwise

**Purpose**: Prevents duplicate scraping (scrape once per day optimization)

---

##### `get_economic_events()`
```python
def get_economic_events(self, target_date: date = None) -> List[Dict]
```

**Description**: Main scraping method that retrieves economic events from investing.com.

**Parameters**:
- `target_date` (date, optional): Date to scrape (default: today)

**Returns**:
- `List[Dict]`: List of event dictionaries

**Process**:
1. Checks if events already exist (skip if yes)
2. Sets up Chrome WebDriver
3. Navigates to investing.com economic calendar
4. Waits 5 seconds for JavaScript to load
5. Parses page HTML with BeautifulSoup
6. Extracts events using CSS selectors
7. Converts event times to user's timezone
8. Cleans up WebDriver

**Event Dictionary Structure**:
```python
{
    'date': date,
    'market_id': None,  # No market filtering at scraping
    'time': time,  # Converted to user timezone
    'currency': str,
    'importance': str,  # 'Low', 'Medium', 'High'
    'event_name': str,
    'actual': str | None,
    'forecast': str | None,
    'previous': str | None,
    'source_url': str
}
```

**Error Handling**:
- Logs errors for individual rows
- Returns empty list on critical failure
- Always cleans up WebDriver in finally block

---

##### `_parse_event_row_selenium()`
```python
def _parse_event_row_selenium(self, row, target_date: date) -> Optional[Dict]
```

**Description**: Parses a single event row from the HTML table.

**Parameters**:
- `row`: BeautifulSoup element (table row)
- `target_date` (date): Event date

**Returns**:
- `Optional[Dict]`: Event dictionary or None on parse failure

**CSS Selectors Used**:
- `.time`: Event time
- `.left.flagCur`: Currency/region
- `.event`: Event name
- `.sentiment i.grayFullBullishIcon`: Importance indicators
- `td[class*='act']`: Actual value
- `td[class*='fore']`: Forecast value
- `td[class*='prev']`: Previous value

**Importance Mapping**:
- 3+ bulls → "High"
- 2 bulls → "Medium"
- 0-1 bulls → "Low"

**Timezone Conversion**:
- Assumes investing.com uses UTC
- Converts to user's configured timezone via `convert_event_time_to_user_timezone()`

---

##### `_parse_time()`
```python
def _parse_time(self, time_text: str) -> Optional[time]
```

**Description**: Converts time string to Python time object.

**Parameters**:
- `time_text` (str): Time string (e.g., "09:00 AM", "15:30", "All Day")

**Returns**:
- `Optional[time]`: Parsed time or None for all-day events

**Supported Formats**:
- "HH:MM AM/PM" (12-hour format)
- "HH:MM" (24-hour format)
- "All Day" (returns None)

---

##### `_convert_importance_count()`
```python
def _convert_importance_count(self, bull_count: int) -> str
```

**Description**: Maps bull icon count to importance level.

**Parameters**:
- `bull_count` (int): Number of bull icons

**Returns**:
- `str`: "High", "Medium", or "Low"

**Mapping**:
- `>= 3` → "High"
- `== 2` → "Medium"
- `< 2` → "Low"

---

##### `_get_market_id()`
```python
def _get_market_id(self, market_symbol: str) -> Optional[int]
```

**Description**: Retrieves database ID for a market symbol.

**Parameters**:
- `market_symbol` (str): Market ticker (e.g., "FDAX")

**Returns**:
- `Optional[int]`: Market ID or None if not found

**Note**: Currently unused as events are market-agnostic at scraping stage.

---

##### `save_events_to_db()`
```python
def save_events_to_db(self, events: List[Dict]) -> int
```

**Description**: Persists scraped events to the database.

**Parameters**:
- `events` (List[Dict]): List of event dictionaries

**Returns**:
- `int`: Number of events successfully saved

**Process**:
1. Checks for existing events (by date, name, time)
2. Updates existing events with new data
3. Inserts new events
4. Commits transaction
5. Returns count of affected rows

**Error Handling**:
- Logs individual event save failures
- Continues processing remaining events
- Returns 0 on critical database error

---

#### Module Function

##### `scrape_and_save_events()`
```python
def scrape_and_save_events(target_date: date = None) -> int
```

**Description**: Convenience function combining scrape and save operations.

**Parameters**:
- `target_date` (date, optional): Date to scrape (default: today)

**Returns**:
- `int`: Number of events saved

**Usage**:
```python
count = scrape_and_save_events(date(2024, 10, 4))
print(f"Saved {count} events")
```

---

### `src/backend/llm_analyzer.py`

**Purpose**: Analyzes economic events using OpenAI's GPT-4o-mini LLM with market-specific insights.

#### Class: `LLMAnalyzer`

**Class-Level Attributes** (for thread-safe rate limiting):
- `_last_api_call_time` (float): Timestamp of last API call
- `_min_request_interval` (float): Minimum seconds between requests (1.0)
- `_rate_limit_lock` (threading.Lock): Thread synchronization lock

---

##### `__init__()`
```python
def __init__(self) -> None
```

**Description**: Initializes the LLM analyzer with API key and rate limiting.

**Side Effects**:
- Retrieves API key from database
- Initializes thread lock for rate limiting (class-level, shared across instances)

---

##### `_enforce_rate_limit()`
```python
def _enforce_rate_limit(self) -> None
```

**Description**: Enforces 1-second minimum delay between API calls (thread-safe).

**Rate Limiting Strategy**:
- Uses class-level variables for cross-instance synchronization
- Thread-safe via `threading.Lock`
- Calculates time since last call
- Sleeps if necessary to maintain 1.0s interval

**Logging**:
- Logs time since last call
- Logs sleep duration
- Confirms when rate limit check completes

**Why Class-Level**:
- Ensures rate limiting works even with multiple analyzer instances
- Prevents race conditions in concurrent scenarios

---

##### `_get_api_key()`
```python
def _get_api_key(self) -> Optional[str]
```

**Description**: Retrieves OpenAI API key from database configuration.

**Returns**:
- `Optional[str]`: API key or None if not configured

**Database Query**:
- Queries `Config` table ordered by `created_at DESC`
- Returns most recent configuration

---

##### `_get_star_filter()`
```python
def _get_star_filter(self) -> int
```

**Description**: Retrieves star filter setting from configuration.

**Returns**:
- `int`: Minimum importance level (1=Low, 2=Medium, 3=High)
- Default: 1 (analyze all events)

**Purpose**: Allows users to skip low-importance events to reduce API costs and rate limit issues.

---

##### `_get_event_importance()`
```python
def _get_event_importance(self, importance_str: str) -> int
```

**Description**: Converts importance string to numeric value for filtering.

**Parameters**:
- `importance_str` (str): "Low", "Medium", or "High"

**Returns**:
- `int`: 1 (Low), 2 (Medium), or 3 (High)

**Mapping**:
```python
{
    'Low': 1,
    'Medium': 2,
    'High': 3
}
```

---

##### `analyze_economic_event()`
```python
def analyze_economic_event(self, event_id: int, market_symbol: str) -> Optional[Dict]
```

**Description**: Main analysis method - analyzes a single event for a specific market.

**Parameters**:
- `event_id` (int): Database ID of economic event
- `market_symbol` (str): Target market (e.g., "FDAX", "BTC", "SPY")

**Returns**:
- `Optional[Dict]`: Analysis result or None

**Return Dictionary**:
```python
{
    'analysis_id': int,
    'event_id': int,
    'analysis': {
        'is_relevant': bool,
        'event_description': str,
        'analysis_text': str,
        'impact_score': int,  # 1-10
        'sentiment_summary': str,  # 'bullish', 'bearish', 'neutral'
        'key_factors': List[str],
        'expert_commentary': str
    }
}
```

**Process**:
1. Check if analysis already exists (event_id + market_symbol)
2. Return existing analysis if found (skip LLM call)
3. Retrieve event data from database
4. Check star filter - skip if importance too low
5. Create analysis prompt
6. Call LLM API (with rate limiting)
7. Parse JSON response
8. Check if event is relevant for this market
9. Save analysis to database
10. Return structured result

**Optimization**:
- **Caching**: Reuses existing analyses (no duplicate API calls)
- **Star Filtering**: Skips low-importance events if configured
- **Market-Specific**: Same event analyzed differently for each market

**Error Handling**:
- Returns None if event not found
- Returns None if importance below filter threshold
- Returns None if event not relevant for market
- Logs all errors

---

##### `_get_event_data()`
```python
def _get_event_data(self, event_id: int) -> Optional[Dict]
```

**Description**: Retrieves event data from database by ID.

**Parameters**:
- `event_id` (int): Event database ID

**Returns**:
- `Optional[Dict]`: Event data dictionary or None

**Event Data Dictionary**:
```python
{
    'id': int,
    'date': date,
    'market_id': int | None,
    'time': time | None,
    'currency': str,
    'importance': str,
    'event_name': str,
    'actual': str | None,
    'forecast': str | None,
    'previous': str | None,
    'source_url': str,
    'market_symbol': None
}
```

---

##### `_search_expert_commentary()`
```python
def _search_expert_commentary(self, event_name: str, market_symbol: str) -> str
```

**Description**: Simplified placeholder for expert commentary (hardcoded context removed).

**Parameters**:
- `event_name` (str): Name of the event
- `market_symbol` (str): Target market

**Returns**:
- `str`: Simple instruction for LLM

**Note**: Previously contained complex, hardcoded expert contexts based on event keywords. Now simplified to let LLM decide analysis approach naturally.

---

##### `_create_analysis_prompt()`
```python
def _create_analysis_prompt(self, event_data: Dict, market_symbol: str) -> str
```

**Description**: Creates the LLM prompt for event analysis.

**Parameters**:
- `event_data` (Dict): Event information
- `market_symbol` (str): Target market

**Returns**:
- `str`: Formatted prompt string

**Prompt Structure**:
```
Analyze this economic event for {market_symbol} market impact:

Event: {event_name}
Date: {date}
Time: {time}
Region (given by the currency): {currency}
Actual: {actual or 'Not released yet'}
Forecast: {forecast or 'N/A'}
Previous: {previous or 'N/A'}

Provide analysis focused on {market_symbol} only. Determine relevance, impact, and trading implications.

Output as JSON:
{
    "is_relevant": true/false,
    "event_description": "Brief explanation...",
    "analysis_text": "Concise analysis...",
    "impact_score": 1-10,
    "sentiment_summary": "bullish/bearish/neutral",
    "key_factors": ["factor1", "factor2", "factor3"],
    "expert_commentary": "Expert-level commentary... Do a web search to get real time information on this"
}
```

**Design Philosophy**:
- Simple and focused
- Let LLM decide analysis approach
- No hardcoded event categories
- Works for all event types

---

##### `_call_llm_api()`
```python
def _call_llm_api(self, prompt: str) -> Optional[str]
```

**Description**: Makes the actual API call to OpenAI with rate limiting.

**Parameters**:
- `prompt` (str): Analysis prompt

**Returns**:
- `Optional[str]`: LLM response text or None on failure

**API Configuration**:
- **Endpoint**: `https://api.openai.com/v1/chat/completions`
- **Model**: `gpt-4o-mini`
- **Max Tokens**: 500
- **Temperature**: 0.3 (low creativity for consistency)
- **Timeout**: 30 seconds

**System Message**:
```
You are a professional financial analyst specializing in economic events and market impact analysis. Provide concise, actionable insights.
```

**Process**:
1. Enforce rate limit (wait if necessary)
2. Make POST request to OpenAI
3. Raise exception on HTTP error
4. Parse JSON response
5. Update `_last_api_call_time` (class-level)
6. Return content string

**Error Handling**:
- Logs all request exceptions
- Returns None on any failure
- Rate limit timestamp only updated on success

---

##### `_parse_analysis()`
```python
def _parse_analysis(self, analysis_text: str, event_data: Dict) -> Dict
```

**Description**: Parses LLM response (JSON or fallback text parsing).

**Parameters**:
- `analysis_text` (str): Raw LLM response
- `event_data` (Dict): Original event data (for context)

**Returns**:
- `Dict`: Structured analysis data

**Parsing Strategy**:
1. **Primary**: Parse as JSON (with markdown code block cleanup)
2. **Fallback**: Text analysis if JSON parsing fails
   - Extract impact score from text
   - Detect sentiment keywords (bullish/bearish)
   - Return with default values

**JSON Cleaning**:
- Removes markdown code blocks (` ```json ` and ` ``` `)
- Strips whitespace
- Validates JSON starts with `{`

**Fallback Defaults**:
```python
{
    'event_description': 'Event description not available',
    'analysis_text': analysis_text,  # raw text
    'impact_score': 5,  # neutral
    'sentiment_summary': 'neutral',
    'key_factors': [],
    'expert_commentary': 'Expert commentary not available'
}
```

---

##### `_save_analysis_to_db()`
```python
def _save_analysis_to_db(self, event_id: int, market_symbol: str, analysis: Dict) -> Optional[int]
```

**Description**: Persists analysis to database.

**Parameters**:
- `event_id` (int): Event database ID
- `market_symbol` (str): Target market
- `analysis` (Dict): Structured analysis data

**Returns**:
- `Optional[int]`: Analysis ID or None on failure

**Database Fields Saved**:
- `event_id`: Links to economic event
- `market_symbol`: Target market for this analysis
- `event_description`: LLM-generated description
- `analysis_text`: Main analysis content
- `impact_score`: 1-10 rating
- `sentiment_summary`: bullish/bearish/neutral
- `search_sources`: Key factors (stored as JSON)
- `expert_commentary`: Expert-level insights

**Error Handling**:
- Logs save errors
- Returns None on failure

---

##### `analyze_events_for_date()`
```python
def analyze_events_for_date(self, target_date: date, market_symbol: str) -> List[Dict]
```

**Description**: Analyzes all events for a specific date and market.

**Parameters**:
- `target_date` (date): Date to analyze
- `market_symbol` (str): Target market

**Returns**:
- `List[Dict]`: List of analysis results

**Process**:
1. Query all events for the date (no market filtering)
2. Loop through each event
3. Call `analyze_economic_event()` for each
4. Collect successful analyses
5. Return list of results

**Optimization**:
- Reuses existing analyses (cached)
- Respects star filter
- Skips irrelevant events

---

#### Module Function

##### `analyze_economic_events()`
```python
def analyze_economic_events(target_date: date = None, market_symbol: str = "FDAX") -> List[Dict]
```

**Description**: Convenience function for batch event analysis.

**Parameters**:
- `target_date` (date, optional): Date to analyze (default: today)
- `market_symbol` (str): Target market (default: "FDAX")

**Returns**:
- `List[Dict]`: Analysis results

**Usage**:
```python
analyses = analyze_economic_events(date(2024, 10, 4), "BTC")
print(f"Analyzed {len(analyses)} relevant events")
```

---

### `src/backend/report_generator.py`

**Purpose**: Generates beautiful HTML reports combining event data and AI analyses.

#### Class: `ReportGenerator`

##### `__init__()`
```python
def __init__(self) -> None
```

**Description**: Initializes report generator (currently no state needed).

---

##### `generate_economic_calendar_report()`
```python
def generate_economic_calendar_report(self, target_date: date, market_symbol: str) -> Optional[Dict]
```

**Description**: Main method to generate a complete HTML report.

**Parameters**:
- `target_date` (date): Report date
- `market_symbol` (str): Target market

**Returns**:
- `Optional[Dict]`: Report metadata or None on failure

**Return Dictionary**:
```python
{
    'report_id': int,
    'date': date,
    'market_symbol': str,
    'html_content': str,
    'events_count': int
}
```

**Process**:
1. Retrieve market data from database
2. Get events with analyses for date/market
3. Generate HTML content
4. Save report to database
5. Return metadata

---

##### `_get_market_data()`
```python
def _get_market_data(self, market_symbol: str) -> Optional[Dict]
```

**Description**: Retrieves market information from database.

**Parameters**:
- `market_symbol` (str): Market ticker

**Returns**:
- `Optional[Dict]`: Market data or None

**Return Dictionary**:
```python
{
    'id': int,
    'symbol': str,
    'description': str
}
```

---

##### `_get_events_with_analyses()`
```python
def _get_events_with_analyses(self, target_date: date, market_symbol: str) -> List[Dict]
```

**Description**: Retrieves events and their analyses for report generation.

**Parameters**:
- `target_date` (date): Report date
- `market_symbol` (str): Target market

**Returns**:
- `List[Dict]`: List of event+analysis dictionaries

**Filtering**:
- Only includes events that have been analyzed
- Only includes analyses for the specified market
- Orders by time (ascending) then importance (descending)

**Event+Analysis Dictionary**:
```python
{
    'id': int,
    'time': time | None,
    'currency': str,
    'importance': str,
    'event_name': str,
    'actual': str | None,
    'forecast': str | None,
    'previous': str | None,
    'source_url': str,
    'event_description': str,
    'analysis_text': str,
    'impact_score': int,
    'sentiment_summary': str,
    'search_sources': List[str],
    'expert_commentary': str,
    'analysis_created_at': datetime
}
```

---

##### `_create_html_report()`
```python
def _create_html_report(self, target_date: date, market_data: Dict, events_data: List[Dict]) -> str
```

**Description**: Generates the complete HTML report document.

**Parameters**:
- `target_date` (date): Report date
- `market_data` (Dict): Market information
- `events_data` (List[Dict]): Events with analyses

**Returns**:
- `str`: Complete HTML document

**Report Sections**:

1. **Header**:
   - Title: "FOMO Bot Report"
   - Subtitle: Market symbol and date
   - Gradient background (purple)

2. **Summary Section**:
   - Total events count
   - High impact events count
   - Analyzed events count
   - Sentiment distribution (bullish/bearish/neutral)

3. **Events Section**:
   - Each event in a card format
   - Event time and importance badge
   - Event name and details (actual/forecast/previous)
   - Event description (LLM-generated)
   - AI Analysis with metrics
   - Impact score (1-10) with color coding
   - Market sentiment badge
   - Key factors list
   - Expert commentary

4. **Footer**:
   - Generation timestamp
   - "Generated by FOMO Bot" message

**Styling**:
- Modern card-based design
- Gradient backgrounds
- Color-coded importance levels
- Responsive layout
- Professional typography
- Bootstrap-inspired aesthetics

**Impact Score Color Coding**:
- **Low (1-3)**: Green
- **Medium (4-6)**: Orange
- **High (7-10)**: Red

**Sentiment Color Coding**:
- **Bullish**: Green
- **Bearish**: Red
- **Neutral**: Gray

---

##### `_save_report_to_db()`
```python
def _save_report_to_db(self, target_date: date, market_id: int, html_content: str) -> Optional[int]
```

**Description**: Saves generated report to database.

**Parameters**:
- `target_date` (date): Report date
- `market_id` (int): Market database ID
- `html_content` (str): Complete HTML

**Returns**:
- `Optional[int]`: Report ID or None on failure

---

##### `get_report()`
```python
def get_report(self, report_id: int) -> Optional[Dict]
```

**Description**: Retrieves a saved report from database.

**Parameters**:
- `report_id` (int): Report database ID

**Returns**:
- `Optional[Dict]`: Report data or None

**Return Dictionary**:
```python
{
    'id': int,
    'date': date,
    'market_id': int,
    'report_html': str,
    'created_at': datetime,
    'market_symbol': str,
    'market_description': str
}
```

**Note**: Extracts all data while session is open to avoid lazy loading issues.

---

#### Module Function

##### `generate_report()`
```python
def generate_report(target_date: date = None, market_symbol: str = "FDAX") -> Optional[Dict]
```

**Description**: Convenience function for report generation.

**Parameters**:
- `target_date` (date, optional): Report date (default: today)
- `market_symbol` (str): Target market (default: "FDAX")

**Returns**:
- `Optional[Dict]`: Report metadata

**Usage**:
```python
report = generate_report(date(2024, 10, 4), "BTC")
if report:
    print(f"Report ID: {report['report_id']}")
    print(f"Events: {report['events_count']}")
```

---

### `src/backend/timezone_utils.py`

**Purpose**: Handles timezone conversions for event times based on user configuration.

#### Functions

##### `get_user_timezone()`
```python
def get_user_timezone() -> str
```

**Description**: Retrieves user's configured timezone from database.

**Returns**:
- `str`: Timezone string (e.g., "Europe/Berlin")
- Default: "Europe/Berlin" if not configured

**Error Handling**:
- Returns default on database error
- Logs errors

---

##### `convert_event_time_to_user_timezone()`
```python
def convert_event_time_to_user_timezone(
    event_time: Optional[time], 
    event_date: date, 
    source_timezone: str = 'UTC'
) -> Optional[time]
```

**Description**: Converts event time from source timezone to user's timezone.

**Parameters**:
- `event_time` (Optional[time]): Original event time (None for all-day events)
- `event_date` (date): Event date
- `source_timezone` (str): Source timezone (default: "UTC")

**Returns**:
- `Optional[time]`: Converted time or None

**Process**:
1. Return None for all-day events (event_time is None)
2. Get user's configured timezone
3. Return original if source == target
4. Create timezone objects with pytz
5. Combine date and time
6. Localize to source timezone
7. Convert to target timezone
8. Extract and return time component

**Error Handling**:
- Returns original time on conversion error
- Logs errors

**Example**:
```python
# Event at 14:00 UTC, user in Berlin (CET, +1)
utc_time = time(14, 0)
event_date = date(2024, 10, 4)
converted = convert_event_time_to_user_timezone(utc_time, event_date, 'UTC')
# Result: 15:00 (Berlin time)
```

---

##### `format_time_with_timezone()`
```python
def format_time_with_timezone(event_time: Optional[time], event_date: date) -> str
```

**Description**: Formats time with timezone abbreviation for display.

**Parameters**:
- `event_time` (Optional[time]): Event time (None for all-day)
- `event_date` (date): Event date

**Returns**:
- `str`: Formatted time string (e.g., "15:00 CEST" or "All Day")

**Example Outputs**:
- `"09:00 CET"` - Winter time in Berlin
- `"15:30 EDT"` - Summer time in New York
- `"All Day"` - All-day events

---

##### `get_timezone_display_name()`
```python
def get_timezone_display_name(timezone_str: str) -> str
```

**Description**: Converts timezone string to user-friendly display name.

**Parameters**:
- `timezone_str` (str): Timezone (e.g., "Europe/Berlin")

**Returns**:
- `str`: Display name (e.g., "Deutschland (CET/CEST)")

**Supported Timezones**:
- Europe/Berlin → "Deutschland (CET/CEST)"
- Europe/London → "Großbritannien (GMT/BST)"
- America/New_York → "New York (EST/EDT)"
- America/Chicago → "Chicago (CST/CDT)"
- America/Los_Angeles → "Los Angeles (PST/PDT)"
- Asia/Tokyo → "Japan (JST)"
- Asia/Shanghai → "China (CST)"
- Australia/Sydney → "Sydney (AEST/AEDT)"
- UTC → "UTC (Coordinated Universal Time)"

---

##### `get_available_timezones()`
```python
def get_available_timezones() -> List[Tuple[str, str]]
```

**Description**: Returns list of available timezones for configuration UI.

**Returns**:
- `List[Tuple[str, str]]`: List of (timezone_string, display_name) tuples

**Example**:
```python
[
    ('Europe/Berlin', '🇩🇪 Deutschland (CET/CEST)'),
    ('America/New_York', '🇺🇸 New York (EST/EDT)'),
    ...
]
```

---

## Frontend Application

### `src/frontend/app.py`

**Purpose**: Flask web application providing the user interface for FOMO Bot.

#### Application Setup

**Flask Configuration**:
- `secret_key`: Session encryption key
- Debug mode: Enabled
- Host: `0.0.0.0` (accessible from network)
- Port: `5000`

---

#### Utility Functions

##### `get_available_markets()`
```python
def get_available_markets() -> List[Market]
```

**Description**: Retrieves all configured markets from database.

**Returns**:
- `List[Market]`: Ordered list of market objects

**Usage**: Populates market dropdowns in UI.

---

#### Routes

##### `index()` - Homepage
```python
@app.route('/')
def index()
```

**Description**: Main landing page with report generation form.

**Template**: `index.html`

**Features**:
- Market selection dropdown
- Date picker (defaults to today)
- "Generate Report" button with loading state

**Template Variables**:
- `markets`: List of available markets

---

##### `generate_report_route()` - Generate Report
```python
@app.route('/generate_report', methods=['POST'])
def generate_report_route()
```

**Description**: Handles report generation workflow.

**Form Parameters**:
- `market`: Market symbol (required)
- `date`: Report date (optional, defaults to today)

**Process**:
1. Validate market selection
2. Parse date
3. Check for duplicate report
4. Scrape events (if not already done)
5. Analyze events with LLM
6. Generate HTML report
7. Redirect to report view

**Duplicate Handling**:
- Checks if report exists for market+date combination
- Flashes info message and redirects to homepage
- Prevents duplicate API costs

**Error Handling**:
- Flashes error messages
- Redirects to homepage on failure
- Logs all errors

---

##### `view_report()` - View Report
```python
@app.route('/report/<int:report_id>')
def view_report(report_id: int)
```

**Description**: Displays a generated report.

**URL Parameters**:
- `report_id`: Database ID of report

**Template**: `view_report.html`

**Template Variables**:
- `report_html`: Complete HTML report content
- `report_id`: Report ID for reference

**Features**:
- Displays full HTML report
- "Back to Reports" button
- Extends base template (includes navigation)

---

##### `reports()` - Reports List
```python
@app.route('/reports')
def reports()
```

**Description**: Historical reports page with filtering and pagination.

**Query Parameters**:
- `page` (int): Page number (default: 1)
- `market` (str): Market filter
- `date_from` (str): Start date filter
- `date_to` (str): End date filter

**Template**: `reports.html`

**Features**:
- Paginated report list (10 per page)
- Filter by market
- Filter by date range
- View report button
- Delete report button
- Postmortem button

**Template Variables**:
- `reports`: List of report data dictionaries
- `markets`: Available markets for filter
- `current_market`: Currently selected market filter
- `date_from`: Start date filter value
- `date_to`: End date filter value
- `page`: Current page number
- `total_pages`: Total number of pages
- `has_prev`: Boolean for "Previous" button
- `has_next`: Boolean for "Next" button

**Lazy Loading Fix**:
- Extracts all data while session is open
- Prevents "Parent instance not bound to Session" errors

---

##### `config()` - Configuration Page
```python
@app.route('/config')
def config()
```

**Description**: Application configuration interface.

**Template**: `config.html`

**Configuration Sections**:
1. **API Configuration**:
   - LLM API Key (OpenAI)
   - News Sources (Phase 2)
   - Chart Folder (Phase 3)
   - Timezone
   - Star Filter (event importance threshold)

2. **Market Management**:
   - Add new markets
   - View existing markets
   - Delete markets

**Template Variables**:
- `config`: Configuration data object
- `markets`: List of markets

---

##### `save_config()` - Save Configuration
```python
@app.route('/save_config', methods=['POST'])
def save_config()
```

**Description**: Persists configuration changes.

**Form Parameters**:
- `llm_api_key`: OpenAI API key
- `news_sources`: News URLs (Phase 2)
- `chart_folder`: Chart directory (Phase 3)
- `timezone`: User timezone
- `star_filter`: Minimum event importance (1-3)

**Process**:
1. Extract form data
2. Query for existing config
3. Update or create config record
4. Commit to database
5. Flash success message
6. Redirect to config page

---

##### `add_market()` - Add Market
```python
@app.route('/add_market', methods=['POST'])
def add_market()
```

**Description**: Adds or updates a market.

**Form Parameters**:
- `symbol`: Market ticker (required, auto-uppercase)
- `description`: Market description (optional)

**Process**:
1. Validate symbol
2. Check for existing market
3. Update or create market record
4. Commit to database
5. Flash success message
6. Redirect to config page

---

##### `delete_market()` - Delete Market
```python
@app.route('/delete_market', methods=['POST'])
def delete_market()
```

**Description**: Removes a market from the system.

**Form Parameters**:
- `market_id`: Database ID of market

**Process**:
1. Validate market_id
2. Query for market
3. Delete market record
4. Commit to database
5. Flash success message
6. Redirect to config page

**Warning**: Deleting a market may affect related reports and events.

---

##### `postmortem()` - Postmortem Reflection
```python
@app.route('/postmortem/<int:report_id>', methods=['GET', 'POST'])
def postmortem(report_id: int)
```

**Description**: Add trading reflections to a report.

**URL Parameters**:
- `report_id`: Database ID of report

**GET Request**:
- Displays postmortem form
- Shows existing postmortem if available

**POST Request**:
- Saves reflection text
- Redirects to reports list

**Form Parameters** (POST):
- `reflection_text`: User's reflection notes (required)

**Template**: `postmortem.html`

**Template Variables** (GET):
- `report`: Report data (date, market)
- `postmortem`: Existing postmortem data (if any)

**Features**:
- Multiple postmortems per report (ordered by date)
- Markdown-friendly text area
- Pre-populated instructions

---

##### `delete_report()` - Delete Report
```python
@app.route('/delete_report/<int:report_id>', methods=['POST'])
def delete_report(report_id: int)
```

**Description**: Deletes a report and associated postmortems.

**URL Parameters**:
- `report_id`: Database ID of report

**Process**:
1. Query for report
2. Delete associated postmortems
3. Delete report record
4. Commit to database
5. Flash success message
6. Redirect to reports list

**Cascade Deletion**:
- Deletes all postmortems linked to the report
- Prevents orphaned records

---

## Application Workflow

### Complete Report Generation Flow

1. **User Action**: User selects market and date, clicks "Generate Report"

2. **Frontend** (`app.py:generate_report_route()`):
   - Validates input
   - Checks for duplicate report
   - Initiates workflow

3. **Scraping** (`scraper.py:scrape_and_save_events()`):
   - Checks if events already scraped for date
   - If not, launches Selenium WebDriver
   - Navigates to investing.com
   - Parses economic events
   - Converts times to user timezone
   - Saves events to database

4. **Analysis** (`llm_analyzer.py:analyze_economic_events()`):
   - Retrieves all events for date
   - For each event:
     - Checks if already analyzed for market
     - Checks star filter (skip if too low)
     - Creates analysis prompt
     - Calls OpenAI API (with rate limiting)
     - Parses JSON response
     - Saves analysis to database

5. **Report Generation** (`report_generator.py:generate_report()`):
   - Retrieves events with analyses
   - Generates HTML report
   - Saves report to database

6. **Display** (`app.py:view_report()`):
   - Retrieves report HTML
   - Renders in browser

---

## Key Design Patterns

### 1. **Market-Agnostic Events**
- Events scraped without market filtering
- LLM determines relevance per market
- Same event can have different analyses for different markets

### 2. **Analysis Caching**
- Analyses stored per event-market combination
- Reused on subsequent report generations
- Reduces API costs and latency

### 3. **Rate Limiting**
- Class-level variables ensure cross-instance synchronization
- Thread-safe with `threading.Lock`
- 1.0 second minimum delay between API calls

### 4. **Star Filtering**
- Configurable importance threshold
- Reduces API calls for low-priority events
- Helps avoid rate limit errors

### 5. **Timezone Handling**
- Events converted to user timezone during scraping
- Configurable timezone in settings
- Supports multiple timezones globally

### 6. **Lazy Loading Prevention**
- Data extracted while session is open
- Passed as dictionaries to templates
- Prevents SQLAlchemy lazy loading errors

### 7. **Error Resilience**
- Logs all errors comprehensively
- Graceful degradation on failures
- User-friendly error messages

---

## Database Relationships

```
Market
├── EconomicEvent (many)
│   └── EventAnalysis (many)
├── NewsItem (many)
│   └── NewsAnalysis (many)
├── ChartAnalysis (many)
└── Report (many)
    └── Postmortem (many)

Config (standalone, global settings)
```

---

## API Integration

### OpenAI API Configuration
- **Endpoint**: `https://api.openai.com/v1/chat/completions`
- **Model**: `gpt-4o-mini`
- **Authentication**: Bearer token (API key)
- **Rate Limit**: 1 request per second (enforced client-side)
- **Max Tokens**: 500
- **Temperature**: 0.3 (consistent, low-creativity)
- **Timeout**: 30 seconds

---

## Security Considerations

1. **API Key Storage**: Stored in database, not in code
2. **Secret Key**: Flask session encryption (change in production)
3. **Input Validation**: Market symbol validation, date parsing
4. **SQL Injection**: Protected by SQLAlchemy ORM
5. **XSS**: Template escaping (Jinja2 default)

---

## Performance Optimizations

1. **Single Scrape Per Day**: Events cached after first scrape
2. **Analysis Caching**: Reuse existing analyses
3. **Star Filtering**: Skip low-importance events
4. **Database Indexing**: Primary keys and foreign keys indexed
5. **Pagination**: Reports paginated (10 per page)
6. **Headless Browser**: Selenium runs without GUI

---

## Future Enhancements (Phases 2 & 3)

### Phase 2: Financial News Analysis
- Scrape news from configured sources
- Analyze news sentiment with LLM
- Include in reports

### Phase 3: Chart Analysis
- Read chart screenshots
- Analyze technical patterns with vision LLM
- Generate trading scenarios

---

## Troubleshooting

### Common Issues

**1. Database Locked Error**
- **Cause**: SQLite file open in another application
- **Solution**: Close database viewers, retry operation

**2. 429 Too Many Requests**
- **Cause**: API rate limit exceeded
- **Solution**: Increase `_min_request_interval`, use star filter

**3. Lazy Loading Error**
- **Cause**: Accessing relationships after session closed
- **Solution**: Extract data while session is open

**4. WebDriver Not Found**
- **Cause**: ChromeDriver not installed
- **Solution**: Install ChromeDriver, add to PATH

**5. Timezone Conversion Error**
- **Cause**: Invalid timezone string or None time
- **Solution**: Validate timezone, handle None times

---

## Conclusion

FOMO Bot is a comprehensive trading analysis system that combines web scraping, AI analysis, and beautiful report generation. The modular architecture allows for easy extension and maintenance, with clear separation between data collection, analysis, and presentation layers.

For questions or contributions, refer to the project README or contact the development team.

---

**Documentation Generated**: October 4, 2025  
**Version**: 1.0  
**Author**: FOMO Bot Development Team

