#!/usr/bin/env python3
"""
Timezone utilities for converting event times to user's configured timezone
"""

from datetime import datetime, time, timezone
import pytz
import logging
from typing import Optional

logger = logging.getLogger(__name__)

def get_user_timezone() -> str:
    """
    Get the user's configured timezone from the database
    Defaults to Europe/Berlin if not configured
    """
    try:
        from models import get_db_session, Config
        
        session = get_db_session()
        config = session.query(Config).first()
        session.close()
        
        if config and config.timezone:
            return config.timezone
        else:
            return 'Europe/Berlin'  # Default timezone
            
    except Exception as e:
        logger.error(f"Error getting user timezone: {e}")
        return 'Europe/Berlin'  # Fallback timezone

def convert_event_time_to_user_timezone(event_time: Optional[time], event_date, source_timezone: str = 'UTC') -> Optional[time]:
    """
    Convert an event time from source timezone to user's configured timezone
    
    Args:
        event_time: The time of the event (can be None for all-day events)
        event_date: The date of the event
        source_timezone: The timezone the event is originally in (default: UTC)
        
    Returns:
        The converted time in user's timezone, or None if event_time was None
    """
    try:
        # Handle None time (all-day events)
        if event_time is None:
            return None
        
        # Get user's timezone
        user_tz = get_user_timezone()
        
        # If source and target timezones are the same, no conversion needed
        if source_timezone == user_tz:
            return event_time
        
        # Create timezone objects
        source_tz = pytz.timezone(source_timezone)
        user_tz_obj = pytz.timezone(user_tz)
        
        # Create a datetime object with the event date and time
        event_datetime = datetime.combine(event_date, event_time)
        
        # Localize to source timezone
        localized_datetime = source_tz.localize(event_datetime)
        
        # Convert to user timezone
        converted_datetime = localized_datetime.astimezone(user_tz_obj)
        
        # Return just the time part
        return converted_datetime.time()
        
    except Exception as e:
        logger.error(f"Error converting timezone: {e}")
        # Return original time if conversion fails
        return event_time

def format_time_with_timezone(event_time: Optional[time], event_date) -> str:
    """
    Format event time with timezone information for display
    
    Args:
        event_time: The time of the event (can be None for all-day events)
        event_date: The date of the event
        
    Returns:
        Formatted time string with timezone abbreviation, or "All Day" if event_time is None
    """
    try:
        # Handle None time (all-day events)
        if event_time is None:
            return "All Day"
        
        user_tz = get_user_timezone()
        user_tz_obj = pytz.timezone(user_tz)
        
        # Create datetime and localize
        event_datetime = datetime.combine(event_date, event_time)
        localized_datetime = user_tz_obj.localize(event_datetime)
        
        # Get timezone abbreviation
        tz_abbr = localized_datetime.strftime('%Z')
        
        # Format time with timezone
        return f"{event_time.strftime('%H:%M')} {tz_abbr}"
        
    except Exception as e:
        logger.error(f"Error formatting time with timezone: {e}")
        if event_time is None:
            return "All Day"
        return event_time.strftime('%H:%M')

def get_timezone_display_name(timezone_str: str) -> str:
    """
    Get a user-friendly display name for a timezone
    
    Args:
        timezone_str: The timezone string (e.g., 'Europe/Berlin')
        
    Returns:
        User-friendly display name
    """
    timezone_names = {
        'Europe/Berlin': 'Deutschland (CET/CEST)',
        'Europe/London': 'Großbritannien (GMT/BST)',
        'America/New_York': 'New York (EST/EDT)',
        'America/Chicago': 'Chicago (CST/CDT)',
        'America/Los_Angeles': 'Los Angeles (PST/PDT)',
        'Asia/Tokyo': 'Japan (JST)',
        'Asia/Shanghai': 'China (CST)',
        'Australia/Sydney': 'Sydney (AEST/AEDT)',
        'UTC': 'UTC (Coordinated Universal Time)'
    }
    
    return timezone_names.get(timezone_str, timezone_str)

def get_available_timezones() -> list:
    """
    Get list of available timezones for the configuration
    
    Returns:
        List of tuples (timezone_string, display_name)
    """
    return [
        ('Europe/Berlin', '🇩🇪 Deutschland (CET/CEST)'),
        ('Europe/London', '🇬🇧 Großbritannien (GMT/BST)'),
        ('America/New_York', '🇺🇸 New York (EST/EDT)'),
        ('America/Chicago', '🇺🇸 Chicago (CST/CDT)'),
        ('America/Los_Angeles', '🇺🇸 Los Angeles (PST/PDT)'),
        ('Asia/Tokyo', '🇯🇵 Japan (JST)'),
        ('Asia/Shanghai', '🇨🇳 China (CST)'),
        ('Australia/Sydney', '🇦🇺 Sydney (AEST/AEDT)'),
        ('UTC', '🌍 UTC (Coordinated Universal Time)')
    ]
