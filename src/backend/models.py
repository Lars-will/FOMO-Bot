from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Date, Time, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime, date, time
from pathlib import Path
import os

Base = declarative_base()

class Market(Base):
    __tablename__ = 'markets'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), unique=True, nullable=False)
    description = Column(Text)
    
    # Relationships
    economic_events = relationship("EconomicEvent", back_populates="market")
    news_items = relationship("NewsItem", back_populates="market")
    chart_analyses = relationship("ChartAnalysis", back_populates="market")
    reports = relationship("Report", back_populates="market")

class Config(Base):
    __tablename__ = 'config'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    llm_api_key = Column(Text)
    news_sources = Column(Text)
    chart_folder = Column(Text)
    timezone = Column(String(50), default='Europe/Berlin')  # Default to German timezone
    star_filter = Column(Integer, default=1)  # Minimum star level to analyze (1=Low, 2=Medium, 3=High)
    created_at = Column(DateTime, default=datetime.now)

class EconomicEvent(Base):
    __tablename__ = 'economic_events'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False)
    market_id = Column(Integer, ForeignKey('markets.id'))
    time = Column(Time)
    currency = Column(String(10))
    importance = Column(String(10))  # Low, Medium, High
    event_name = Column(Text, nullable=False)
    actual = Column(Text)
    forecast = Column(Text)
    previous = Column(Text)
    source_url = Column(Text)
    
    # Relationships
    market = relationship("Market", back_populates="economic_events")
    analyses = relationship("EventAnalysis", back_populates="event")

class EventAnalysis(Base):
    __tablename__ = 'event_analyses'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(Integer, ForeignKey('economic_events.id'))
    market_symbol = Column(String(20), nullable=False)  # Market this analysis is for (e.g., FDAX, BTC, SPY)
    event_description = Column(Text)  # LLM-generated description of what the event means
    analysis_text = Column(Text)
    impact_score = Column(Integer)  # 1-10 scale
    sentiment_summary = Column(String(20))  # bullish, bearish, neutral
    search_sources = Column(JSON)  # Store as JSON
    expert_commentary = Column(Text)  # Expert opinions and market commentary
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    event = relationship("EconomicEvent", back_populates="analyses")

class NewsItem(Base):
    __tablename__ = 'news_items'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False)
    market_id = Column(Integer, ForeignKey('markets.id'))
    title = Column(Text)
    summary = Column(Text)
    url = Column(Text)
    source = Column(String(100))
    
    # Relationships
    market = relationship("Market", back_populates="news_items")
    analyses = relationship("NewsAnalysis", back_populates="news_item")

class NewsAnalysis(Base):
    __tablename__ = 'news_analyses'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    news_id = Column(Integer, ForeignKey('news_items.id'))
    analysis_text = Column(Text)
    sentiment = Column(String(20))  # bullish, bearish, neutral
    impact_score = Column(Integer)  # 1-10 scale
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    news_item = relationship("NewsItem", back_populates="analyses")

class ChartAnalysis(Base):
    __tablename__ = 'chart_analyses'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False)
    market_id = Column(Integer, ForeignKey('markets.id'))
    timeframe = Column(String(20))  # Daily, Hourly, 30-min, etc.
    image_path = Column(Text)
    analysis_text = Column(Text)
    scenarios = Column(JSON)  # Store as JSON
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    market = relationship("Market", back_populates="chart_analyses")

class Report(Base):
    __tablename__ = 'reports'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False)
    market_id = Column(Integer, ForeignKey('markets.id'))
    report_html = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    market = relationship("Market", back_populates="reports")
    postmortems = relationship("Postmortem", back_populates="report")

class Postmortem(Base):
    __tablename__ = 'postmortems'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(Integer, ForeignKey('reports.id'))
    reflection_text = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    report = relationship("Report", back_populates="postmortems")

# Database setup
def get_database_url():
    """Get database URL based on environment"""
    # Get the project root directory (two levels up from backend)
    project_root = Path(__file__).parent.parent.parent
    db_path = project_root / "database" / "fomo-bot-DB.sqlite"
    return f"sqlite:///{db_path}"

def create_engine_and_session():
    """Create SQLAlchemy engine and session"""
    engine = create_engine(get_database_url(), echo=False)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return engine, SessionLocal

def get_db_session():
    """Get database session"""
    _, SessionLocal = create_engine_and_session()
    return SessionLocal()

def init_database():
    """Initialize database with all tables"""
    engine, _ = create_engine_and_session()
    Base.metadata.create_all(bind=engine)
    return engine
