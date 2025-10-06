# -*- coding: utf-8 -*-
"""
Test Suite: Business Hours Validation - PR #1 Fundamentos
=========================================================

Tests unitarios para BusinessHoursConfig
"""

import pytest
from datetime import datetime, time
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.config.business_hours import BusinessHoursConfig

try:
    from zoneinfo import ZoneInfo
except ImportError:
    import pytz
    class ZoneInfo:
        def __init__(self, tz_name):
            self.tz = pytz.timezone(tz_name)

def test_is_business_hours_monday_morning():
    """Test: Lunes 10:00 AM = horario laboral."""
    try:
        dt = datetime(2025, 10, 6, 10, 0, tzinfo=ZoneInfo("America/Bogota"))
    except:
        import pytz
        dt = pytz.timezone("America/Bogota").localize(datetime(2025, 10, 6, 10, 0))
    
    result = BusinessHoursConfig.is_business_hours(dt)
    assert result == True

def test_is_business_hours_monday_evening():
    """Test: Lunes 8:00 PM = fuera de horario."""
    try:
        dt = datetime(2025, 10, 6, 20, 0, tzinfo=ZoneInfo("America/Bogota"))
    except:
        import pytz
        dt = pytz.timezone("America/Bogota").localize(datetime(2025, 10, 6, 20, 0))
    
    result = BusinessHoursConfig.is_business_hours(dt)
    assert result == False

def test_is_business_hours_saturday_morning():
    """Test: Sabado 10:00 AM = horario laboral."""
    try:
        dt = datetime(2025, 10, 11, 10, 0, tzinfo=ZoneInfo("America/Bogota"))
    except:
        import pytz
        dt = pytz.timezone("America/Bogota").localize(datetime(2025, 10, 11, 10, 0))
    
    result = BusinessHoursConfig.is_business_hours(dt)
    assert result == True

def test_is_business_hours_saturday_afternoon():
    """Test: Sabado 2:00 PM = fuera de horario."""
    try:
        dt = datetime(2025, 10, 11, 14, 0, tzinfo=ZoneInfo("America/Bogota"))
    except:
        import pytz
        dt = pytz.timezone("America/Bogota").localize(datetime(2025, 10, 11, 14, 0))
    
    result = BusinessHoursConfig.is_business_hours(dt)
    assert result == False

def test_is_business_hours_sunday():
    """Test: Domingo = siempre cerrado."""
    try:
        dt = datetime(2025, 10, 12, 10, 0, tzinfo=ZoneInfo("America/Bogota"))
    except:
        import pytz
        dt = pytz.timezone("America/Bogota").localize(datetime(2025, 10, 12, 10, 0))
    
    result = BusinessHoursConfig.is_business_hours(dt)
    assert result == False

def test_out_of_hours_message_without_name():
    """Test: Mensaje fuera de horario sin nombre."""
    message = BusinessHoursConfig.get_out_of_hours_message()
    message_lower = message.lower()
    assert ("horario" in message_lower and "atención" in message_lower) or "no estamos disponibles" in message_lower
    assert "8" in message

def test_out_of_hours_message_with_name():
    """Test: Mensaje fuera de horario con nombre."""
    message = BusinessHoursConfig.get_out_of_hours_message(customer_name="Carlos")
    assert "Carlos" in message

def test_get_current_status_structure():
    """Test: Estructura del status actual."""
    status = BusinessHoursConfig.get_current_status()
    assert isinstance(status, dict)
    assert "is_open" in status
    assert "current_time" in status or "day_name" in status
    assert isinstance(status["is_open"], bool)
