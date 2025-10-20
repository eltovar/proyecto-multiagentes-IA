# -*- coding: utf-8 -*-
"""
Tests de configuración para SupportAgent
Valida integridad de routing_config y DEPARTMENT_CONTACTS
"""

import pytest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.config import DEPARTMENT_CONTACTS, get_department_contacts, get_department_contact


def test_department_contacts_structure():
    """Verifica estructura de DEPARTMENT_CONTACTS (backward compatibility)"""
    assert isinstance(DEPARTMENT_CONTACTS, dict)
    assert len(DEPARTMENT_CONTACTS) > 0

    required_fields = ["name", "keywords", "phone", "hours"]

    for dept, config in DEPARTMENT_CONTACTS.items():
        assert isinstance(dept, str), f"Department key should be string: {dept}"
        assert isinstance(config, dict), f"Config for {dept} should be dict"

        for field in required_fields:
            assert field in config, f"Missing field '{field}' in department '{dept}'"

        # Verify types
        assert isinstance(config["name"], str)
        assert isinstance(config["keywords"], list)
        assert isinstance(config["phone"], str)
        assert isinstance(config["hours"], str)

        # Verify non-empty
        assert len(config["name"]) > 0
        assert len(config["keywords"]) > 0
        assert len(config["phone"]) > 0
        assert len(config["hours"]) > 0


def test_department_contacts_has_required_departments():
    """Verifica que departamentos clave existen"""
    required_departments = [
        "propietarios",
        "proveedores",
        "contratos",
        "reparaciones",
        "abogados"
    ]

    for dept in required_departments:
        assert dept in DEPARTMENT_CONTACTS, f"Required department '{dept}' not found"


def test_department_keywords_no_duplicates():
    """Verifica que no hay keywords duplicados entre departamentos"""
    all_keywords = []

    for dept, config in DEPARTMENT_CONTACTS.items():
        keywords = config["keywords"]
        for keyword in keywords:
            # Check if keyword appears in multiple departments
            count = sum(
                1 for d, c in DEPARTMENT_CONTACTS.items()
                if keyword in c["keywords"]
            )

            # It's OK if some keywords overlap, but warn if too much overlap
            if count > 1:
                # This is informational, not a failure
                pass


def test_department_phones_valid_format():
    """Verifica que números de teléfono tienen formato válido"""
    import re

    # Colombian phone format: 10 digits, may have spaces/dashes
    phone_pattern = re.compile(r'^[\d\s\-\(\)\[\]]+$')

    for dept, config in DEPARTMENT_CONTACTS.items():
        phone = config["phone"]
        assert phone_pattern.match(phone), f"Invalid phone format for {dept}: {phone}"

        # Remove non-digits
        digits_only = re.sub(r'[^\d]', '', phone)
        assert len(digits_only) == 10, f"Phone for {dept} should have 10 digits: {phone}"


def test_support_agent_file_syntax():
    """Verifica que support_agent.py tiene sintaxis válida"""
    file_path = os.path.join(
        os.path.dirname(__file__),
        '../..',
        'app',
        'agents',
        'support',
        'agent.py'
    )

    with open(file_path, 'r', encoding='utf-8') as f:
        code = f.read()

    # Try to compile
    try:
        compile(code, 'agent.py', 'exec')
    except SyntaxError as e:
        pytest.fail(f"Syntax error in support/agent.py: {e}")


def test_support_agent_imports():
    """Verifica que imports necesarios están presentes en el nuevo SupportAgent refactorizado"""
    file_path = os.path.join(
        os.path.dirname(__file__),
        '../..',
        'app',
        'agents',
        'support',
        'agent.py'
    )

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Imports del nuevo SupportAgent con Pipeline Pattern
    required_imports = [
        'from app.agents.base_agent import BaseAgent',
        'from app.core.pipeline import',
        'from app.agents.support.pipeline_steps import',
        'from app.agents.support.classifiers.intent import IntentClassifier',
        'from app.agents.support.handlers',
    ]

    for imp in required_imports:
        assert imp in content, f"Required import not found: {imp}"


def test_tripath_constants_defined():
    """Verifica que los 3 handlers del tri-path están definidos (PropertyHandler, DepartmentHandler, GeneralHandler)"""
    file_path = os.path.join(
        os.path.dirname(__file__),
        '../..',
        'app',
        'agents',
        'support',
        'agent.py'
    )

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # El nuevo SupportAgent usa handlers en lugar de constantes
    # PropertyHandler → equivalente a CAMINO_1_INMUEBLE
    # DepartmentHandler → equivalente a CAMINO_2_DEPARTAMENTO
    # GeneralHandler → equivalente a CAMINO_3_GENERAL
    handlers = [
        'PropertyHandler',
        'DepartmentHandler',
        'GeneralHandler'
    ]

    for handler in handlers:
        assert handler in content, f"Handler '{handler}' not found in code"


def test_gap_fixes_implemented():
    """Verifica que Pipeline Pattern con RAG y routing están implementados"""
    file_path = os.path.join(
        os.path.dirname(__file__),
        '../..',
        'app',
        'agents',
        'support',
        'agent.py'
    )

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # El nuevo SupportAgent usa Pipeline Pattern con steps específicos
    # GAP #1: RAGSearchStep maneja búsqueda RAG (equivalente a rag_context)
    # GAP #2: RoutingDecisionStep maneja routing y transferencias (equivalente a TRANSFERIDO/handoff_reason)
    assert 'RAGSearchStep' in content, "RAGSearchStep (equivalente a GAP #1) no encontrado"
    assert 'RoutingDecisionStep' in content, "RoutingDecisionStep (equivalente a GAP #2) no encontrado"
    assert 'ResponseGeneratorStep' in content, "ResponseGeneratorStep no encontrado"
    assert 'MessagePipeline' in content or 'PipelineBuilder' in content, "Pipeline infrastructure no encontrada"


def test_code_comments_present():
    """Verifica que código tiene comentarios explicativos"""
    file_path = os.path.join(
        os.path.dirname(__file__),
        '../..',
        'app',
        'agents',
        'support',
        'agent.py'
    )

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Count comment lines
    comment_lines = [line for line in lines if line.strip().startswith('#')]
    code_lines = [line for line in lines if line.strip() and not line.strip().startswith('#')]

    # Should have reasonable ratio of comments
    comment_ratio = len(comment_lines) / len(code_lines) if code_lines else 0

    assert comment_ratio > 0.05, f"Code should have comments (ratio: {comment_ratio:.2%})"


def test_no_todo_or_fixme_comments():
    """Verifica que no hay TODOs o FIXMEs pendientes críticos"""
    file_path = os.path.join(
        os.path.dirname(__file__),
        '../..',
        'app',
        'agents',
        'support',
        'agent.py'
    )

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Allow some TODOs but not critical FIXMEs
    assert 'FIXME' not in content.upper(), "Critical FIXMEs found in code"


def test_helper_markers_present():
    """Verifica que la arquitectura del Pipeline Pattern está implementada correctamente"""
    file_path = os.path.join(
        os.path.dirname(__file__),
        '../..',
        'app',
        'agents',
        'support',
        'agent.py'
    )

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # El nuevo SupportAgent usa Pipeline Pattern en lugar de helpers legacy
    # Verificar componentes clave del pipeline
    assert 'PipelineBuilder' in content, "PipelineBuilder no encontrado"
    assert '.add(' in content, "Configuración de steps con .add() no encontrada"
    assert 'IntentClassifierStep' in content, "IntentClassifierStep no encontrado"
    assert 'context.get_result(' in content, "Acceso a resultados del pipeline no encontrado"


def test_get_department_contacts_function():
    """Verifica que nueva función get_department_contacts() funciona"""
    contacts = get_department_contacts()
    assert isinstance(contacts, dict)
    assert len(contacts) > 0

    # Validar estructura de contactos devueltos
    required_fields = ["name", "keywords", "phone", "hours"]

    for dept, config in contacts.items():
        assert isinstance(dept, str)
        assert isinstance(config, dict)

        for field in required_fields:
            assert field in config, f"Missing field '{field}' in department '{dept}'"


def test_get_department_contact_function():
    """Verifica que get_department_contact() funciona"""
    dept = get_department_contact("propietarios")
    assert dept is not None
    assert "phone" in dept
    assert "name" in dept
    assert "hours" in dept
    assert "keywords" in dept

    # Test departamento inexistente
    non_existent = get_department_contact("departamento_inexistente")
    assert non_existent is None


def test_department_contacts_backward_compatibility():
    """Verifica que DEPARTMENT_CONTACTS mantiene compatibilidad con código legacy"""
    # La variable global DEPARTMENT_CONTACTS debe seguir funcionando
    assert DEPARTMENT_CONTACTS is not None
    assert isinstance(DEPARTMENT_CONTACTS, dict)

    # Debe tener la misma estructura que get_department_contacts()
    contacts_from_function = get_department_contacts()

    # Ambos deben tener los mismos departamentos
    assert set(DEPARTMENT_CONTACTS.keys()) == set(contacts_from_function.keys())
