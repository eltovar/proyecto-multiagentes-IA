# -*- coding: utf-8 -*-
"""
Tests de configuración tri-path
"""

import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.config import (
    DEPARTMENT_CONTACTS,
    VALID_STATES,
    STATE_ROUTING_ANALYSIS,
    STATE_SUPPORT_ACTIVE,
    STATE_DEPARTMENT_REDIRECT
)


def test_department_contacts_structure():
    """Validar estructura de DEPARTMENT_CONTACTS"""
    assert len(DEPARTMENT_CONTACTS) == 5

    for dept_name, config in DEPARTMENT_CONTACTS.items():
        assert "phone" in config
        assert "name" in config
        assert "hours" in config
        assert "services" in config
        assert "keywords" in config

        # Validar formato teléfono (XXX XXX XXXX)
        phone = config["phone"]
        assert len(phone.replace(" ", "").replace("-", "")) == 10


def test_tripath_states_in_valid_states():
    """Validar que estados tri-path están en VALID_STATES"""
    assert STATE_ROUTING_ANALYSIS in VALID_STATES
    assert STATE_SUPPORT_ACTIVE in VALID_STATES
    assert STATE_DEPARTMENT_REDIRECT in VALID_STATES


def test_department_keywords_not_empty():
    """Validar que cada departamento tiene keywords"""
    for dept_name, config in DEPARTMENT_CONTACTS.items():
        keywords = config.get("keywords", [])
        assert len(keywords) > 0, f"{dept_name} no tiene keywords"


def test_prompt_import():
    """Validar que CLASSIFY_TRIPATH_INTENT se puede importar"""
    from app.prompts.classification_prompts import CLASSIFY_TRIPATH_INTENT

    assert "CAMINO 1" in CLASSIFY_TRIPATH_INTENT
    assert "CAMINO 2" in CLASSIFY_TRIPATH_INTENT
    assert "CAMINO 3" in CLASSIFY_TRIPATH_INTENT
    assert "{message}" in CLASSIFY_TRIPATH_INTENT
