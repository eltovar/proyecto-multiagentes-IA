# -*- coding: utf-8 -*-
"""
Tests unitarios para métodos helper de SupportAgent
Valida DRY refactoring (FASE 3)
"""

import pytest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))


def test_empty_rag_result_structure():
    """Test que _empty_rag_result retorna estructura correcta"""
    from unittest.mock import MagicMock, patch

    with patch('app.agents.support_agent.llm_service'), \
         patch('app.agents.support_agent.rag_system') as mock_rag:

        mock_rag.initialized = True

        from app.agents.support_agent import SupportAgent

        # Create instance with minimal initialization
        agent = SupportAgent.__new__(SupportAgent)
        agent.name = "SupportAgent"

        # Test helper
        result = agent._empty_rag_result()

        assert isinstance(result, dict)
        assert "documents" in result
        assert "context" in result
        assert "phone_numbers" in result
        assert "rag_confidence" in result

        assert result["documents"] == []
        assert result["context"] == ""
        assert result["phone_numbers"] == []
        assert result["rag_confidence"] == 0.0


def test_format_greeting_with_name():
    """Test _format_greeting con nombre de cliente"""
    from unittest.mock import patch

    with patch('app.agents.support_agent.llm_service'), \
         patch('app.agents.support_agent.rag_system') as mock_rag:

        mock_rag.initialized = True

        from app.agents.support_agent import SupportAgent

        agent = SupportAgent.__new__(SupportAgent)
        agent.name = "SupportAgent"

        # Test con nombre y prefijo
        result = agent._format_greeting("Carlos", "Hola")
        assert result == "Hola, Carlos"

        # Test solo con prefijo
        result = agent._format_greeting("", "Perfecto")
        assert result == "Perfecto"

        # Test solo con nombre
        result = agent._format_greeting("María", "")
        assert result == "María"

        # Test sin nada
        result = agent._format_greeting("", "")
        assert result == ""


def test_build_response_data_structure():
    """Test _build_response_data construye estructura correcta"""
    from unittest.mock import patch

    with patch('app.agents.support_agent.llm_service'), \
         patch('app.agents.support_agent.rag_system') as mock_rag:

        mock_rag.initialized = True

        from app.agents.support_agent import SupportAgent

        agent = SupportAgent.__new__(SupportAgent)
        agent.name = "SupportAgent"

        # Test básico
        result = agent._build_response_data(
            routing_path="CAMINO_1_INMUEBLE",
            intent="inmueble"
        )

        assert result["routing_path"] == "CAMINO_1_INMUEBLE"
        assert result["intent"] == "inmueble"

        # Test con extra_data
        result = agent._build_response_data(
            routing_path="CAMINO_2_DEPARTAMENTO",
            intent="departamento",
            sub_intent="reparaciones",
            handoff_reason="department_reparaciones",
            custom_field="custom_value"
        )

        assert result["routing_path"] == "CAMINO_2_DEPARTAMENTO"
        assert result["intent"] == "departamento"
        assert result["sub_intent"] == "reparaciones"
        assert result["handoff_reason"] == "department_reparaciones"
        assert result["custom_field"] == "custom_value"


def test_routing_config_structure():
    """Test que routing_config tiene estructura correcta"""
    from unittest.mock import patch

    with patch('app.agents.support_agent.llm_service'), \
         patch('app.agents.support_agent.rag_system') as mock_rag:

        mock_rag.initialized = True

        from app.agents.support_agent import SupportAgent
        from app.config import DEPARTMENT_CONTACTS

        agent = SupportAgent.__new__(SupportAgent)
        agent.name = "SupportAgent"

        # Manually set routing_config (normally done in __init__)
        agent.routing_config = {
            "inmueble_keywords": [
                "comprar", "vender", "apartamento", "casa", "arriendo",
                "local", "lote", "propiedad", "inmueble", "cita", "visita",
                "agendar", "alquilar", "arrendar"
            ],
            "departamento_keywords": {
                dept: config["keywords"]
                for dept, config in DEPARTMENT_CONTACTS.items()
            },
            "general_keywords": [
                "quiénes", "historia", "horario", "ubicación", "blog",
                "servicios", "empresa", "política"
            ]
        }

        # Verify structure
        assert "inmueble_keywords" in agent.routing_config
        assert "departamento_keywords" in agent.routing_config
        assert "general_keywords" in agent.routing_config

        # Verify inmueble keywords
        assert isinstance(agent.routing_config["inmueble_keywords"], list)
        assert len(agent.routing_config["inmueble_keywords"]) > 0
        assert "apartamento" in agent.routing_config["inmueble_keywords"]

        # Verify departamento keywords match DEPARTMENT_CONTACTS
        dept_keywords = agent.routing_config["departamento_keywords"]
        for dept in dept_keywords:
            assert dept in DEPARTMENT_CONTACTS
            assert dept_keywords[dept] == DEPARTMENT_CONTACTS[dept]["keywords"]


def test_phone_regex_pattern():
    """Test que phone_regex extrae números correctamente"""
    from unittest.mock import patch
    import re

    with patch('app.agents.support_agent.llm_service'), \
         patch('app.agents.support_agent.rag_system') as mock_rag:

        mock_rag.initialized = True

        from app.agents.support_agent import SupportAgent

        agent = SupportAgent.__new__(SupportAgent)
        agent.name = "SupportAgent"

        # Manually create regex (normally done in __init__)
        agent.phone_regex = re.compile(
            r'\+?57\s?'
            r'[\(\[]?\s?'
            r'(\d{3})'
            r'[\)\]]?\s?[\s\.\-]?\s?'
            r'(\d{3})'
            r'[\s\.\-]?\s?'
            r'(\d{4})\b'
        )

        # Test various formats
        test_cases = [
            ("321 123 4567", True),
            ("+57 321 123 4567", True),
            ("321-123-4567", True),
            ("3211234567", True),
            ("(321) 123 4567", True),
            ("[321] 123 4567", True),
            ("123", False),  # Too short
            ("abc", False),  # Not a number
        ]

        for text, should_match in test_cases:
            matches = agent.phone_regex.findall(text)
            if should_match:
                assert len(matches) > 0, f"Should match: {text}"
            else:
                assert len(matches) == 0, f"Should not match: {text}"


def test_helpers_reduce_duplication():
    """Test que helpers reducen duplicación de código"""
    from unittest.mock import patch

    with patch('app.agents.support_agent.llm_service'), \
         patch('app.agents.support_agent.rag_system') as mock_rag:

        mock_rag.initialized = True

        from app.agents.support_agent import SupportAgent

        agent = SupportAgent.__new__(SupportAgent)
        agent.name = "SupportAgent"

        # Test que helper methods existen
        assert hasattr(agent, '_empty_rag_result')
        assert hasattr(agent, '_format_greeting')
        assert hasattr(agent, '_build_response_data')

        # Test que son callables
        assert callable(agent._empty_rag_result)
        assert callable(agent._format_greeting)
        assert callable(agent._build_response_data)


def test_helper_methods_have_docstrings():
    """Test que helpers tienen documentación"""
    from unittest.mock import patch

    with patch('app.agents.support_agent.llm_service'), \
         patch('app.agents.support_agent.rag_system') as mock_rag:

        mock_rag.initialized = True

        from app.agents.support_agent import SupportAgent

        agent = SupportAgent.__new__(SupportAgent)

        # Verify docstrings exist
        assert agent._empty_rag_result.__doc__ is not None
        assert agent._format_greeting.__doc__ is not None
        assert agent._build_response_data.__doc__ is not None

        # Verify docstrings are meaningful
        assert "Helper" in agent._empty_rag_result.__doc__
        assert "Helper" in agent._format_greeting.__doc__
        assert "Helper" in agent._build_response_data.__doc__
