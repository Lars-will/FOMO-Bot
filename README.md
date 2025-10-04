# FOMO Bot - Trading Analysis Tool

The FOMO Bot is an automated tool for day traders that supports the morning preparation routine through data aggregation, analysis, and reporting.

## 🎯 Project Overview

The system is divided into three phases:

- **Phase 1** ✅: Automation of daily economic calendar analysis
- **Phase 2** ⏳: Automation of daily financial news analysis  
- **Phase 3** ⏳: Automated chart analysis of previous day's charts

## 🚀 Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python Package Manager)
- Chrome/Chromium Browser (for Selenium WebDriver)
- ChromeDriver (automatically managed by Selenium)

### Setup

1. **Clone the repository:**
```bash
git clone <repository-url>
cd FOMO-Bot
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Initialize the database:**
```bash
cd src/backend
python init_db.py
```

4. **Add initial markets:**
```bash
cd ../backend
python populate_markets.py
```

5. **Start the application:**
```bash
cd ../src
python run.py
```

6. **Open browser:**
```
http://localhost:5000
```

## 📊 Features

### Phase 1: Economic Calendar (Implemented)

- **Web Scraping**: Automatic scraping of investing.com with Selenium (JavaScript support)
- **LLM Analysis**: Market impact assessment with GPT-4o-mini
- **Report Generation**: HTML reports with summaries and expert commentary
- **Database Storage**: Local SQLite database for historical data

### Web Interface

- **Homepage**: Market selection and report generation
- **Reports Page**: Historical reports with filtering and deletion
- **Configuration**: API keys and settings management
- **Timezone Support**: Configurable timezone for event display

## 🔧 Configuration

### API Keys

1. Go to the configuration page (`/config`)
2. Add your OpenAI API key
3. Save the configuration

### Markets

The following markets are available by default:
- FDAX (DAX Futures)
- BTC (Bitcoin)
- ETH (Ethereum)
- SPY (S&P 500 ETF)
- EURUSD, GBPUSD, USDJPY (Forex)
- GOLD, OIL (Commodities)
- TSLA (Tesla Stock)

### Timezone Configuration

You can configure your timezone in the settings to display economic event times in your local timezone. Default is Europe/Berlin.

## 📁 Project Structure

```
FOMO-Bot/
├── database/
│   └── fomo-bot-DB.sqlite          # SQLite database
├── src/
│   ├── run.py                      # Main application
│   ├── backend/
│   │   ├── models.py               # SQLAlchemy ORM models
│   │   ├── init_db.py              # Database initialization
│   │   ├── scraper.py              # Web scraping for economic calendar
│   │   ├── llm_analyzer.py         # LLM analysis of events
│   │   ├── report_generator.py     # HTML report generation
│   │   ├── timezone_utils.py       # Timezone conversion utilities
│   │   └── populate_markets.py     # Initial market population
│   └── frontend/
│       ├── app.py                  # Flask web application
│       └── templates/              # HTML templates
│           ├── base.html
│           ├── index.html
│           ├── reports.html
│           ├── config.html
│           └── view_report.html
├── requirements.txt                # Python dependencies
└── README.md
```

## 🗄️ Database Schema

### Tables

- **markets**: Available markets (FDAX, BTC, etc.)
- **economic_events**: Economic events from the calendar
- **event_analyses**: LLM analyses of events (including expert commentary)
- **news_items**: Financial news (Phase 2)
- **news_analyses**: News analyses (Phase 2)
- **chart_analyses**: Chart analyses (Phase 3)
- **reports**: Generated HTML reports
- **postmortems**: Post-mortem analysis of reports
- **config**: System configuration (API keys, timezone, etc.)

## 🔄 Workflow

1. **Select Market**: Choose a market (e.g., FDAX)
2. **Generate Report**: Click "Generate Report"
3. **Automatic Processing**:
   - Scraping of economic calendar data (once per day)
   - LLM analysis of events for market relevance
   - HTML report generation with expert commentary
4. **View Report**: Automatic redirect to the report
5. **Historical Access**: View and manage previous reports

## 🛠️ Development

### Adding New Markets

```python
# In backend/populate_markets.py
markets = [
    ("SYMBOL", "Description"),
    # ...
]
```

### Extending API Integration

The LLM analysis can be adapted in `llm_analyzer.py`:

```python
# Add other LLM providers
def _call_llm_api(self, prompt: str):
    # OpenAI, Anthropic, etc.
```


## 📈 Roadmap

### Phase 2: Financial News
- [ ] Bloomberg, Reuters, FXStreet scraping
- [ ] Sentiment analysis of news
- [ ] Integration into reports

### Phase 3: Chart Analysis
- [ ] Vision LLM for chart screenshots
- [ ] Support/resistance detection
- [ ] Scenario generation

## 🐛 Troubleshooting

### Common Issues

1. **Database Errors**: Run `cd src/backend && python init_db.py`
2. **API Key Errors**: Check configuration in `/config`
3. **Scraping Errors**: Check internet connection
4. **Selenium Errors**: Ensure Chrome/Chromium is installed
5. **ChromeDriver Errors**: Selenium should automatically download ChromeDriver

### Logs

The application logs important events. Check the console for details.


## 📄 License

This project is intended for personal use by the developer.

## 🤝 Contributing

The project is in active development. Feedback and improvement suggestions are welcome.

---

**FOMO Bot** - Automated trading analysis for professional day traders