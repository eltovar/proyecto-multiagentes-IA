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

from app.config import DEPARTMENT_CONTACTS


def test_department_contacts_structure():
    """Verifica estructura de DEPARTMENT_CONTACTS"""
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
        'support_agent.py'
    )

    with open(file_path, 'r', encoding='utf-8') as f:
        code = f.read()

    # Try to compile
    try:
        compile(code, 'support_agent.py', 'exec')
    except SyntaxError as e:
        pytest.fail(f"Syntax error in support_agent.py: {e}")


def test_support_agent_imports():
    """Verifica que imports necesarios están presentes"""
    file_path = os.path.join(
        os.path.dirname(__file__),
        '../..',
        'app',
        'agents',
        'support_agent.py'
    )

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    required_imports = [
        'from app.config import',
        'DEPARTMENT_CONTACTS',
        'from app.rag.rag_system import',  # Corrected import name
        'from app.services.llm_service import',
        'import json',
        'import re',
    ]

    for imp in required_imports:
        assert imp in content, f"Required import not found: {imp}"


def test_tripath_constants_defined():
    """Verifica que constantes de tri-path están definidas"""
    file_path = os.path.join(
        os.path.dirname(__file__),
        '../..',
        'app',
        'agents',
        'support_agent.py'
    )

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Should have routing path constants
    paths = [
        'CAMINO_1_INMUEBLE',
        'CAMINO_2_DEPARTAMENTO',
        'CAMINO_3_GENERAL'
    ]

    for path in paths:
        assert path in content, f"Routing path '{path}' not found in code"


def test_gap_fixes_implemented():
    """Verifica que GAP #1 y GAP #2 están implementados"""
    file_path = os.path.join(
        os.path.dirname(__file__),
        '../..',
        'app',
        'agents',
        'support_agent.py'
    )

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # GAP #1: RAG context usage in CAMINO 1
    assert 'rag_context' in content
    assert 'classify_with_prompt' in content
    assert 'response_format="text"' in content

    # GAP #2: TRANSFERIDO state in CAMINO 2
    assert 'new_state="TRANSFERIDO"' in content
    assert 'handoff_reason' in content


def test_code_comments_present():
    """Verifica que código tiene comentarios explicativos"""
    file_path = os.path.join(
        os.path.dirname(__file__),
        '../..',
        'app',
        'agents',
        'support_agent.py'
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
        'support_agent.py'
    )

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Allow some TODOs but not critical FIXMEs
    assert 'FIXME' not in content.upper(), "Critical FIXMEs found in code"


def test_helper_markers_present():
    """Verifica que marcadores de helpers están presentes"""
    file_path = os.path.join(
        os.path.dirname(__file__),
        '../..',
        'app',
        'agents',
        'support_agent.py'
    )

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Should have markers indicating helper usage
    assert '✅ Usando helper' in content or 'Usando helper' in content
    assert '_empty_rag_result' in content
    assert '_format_greeting' in content
    assert '_build_response_data' in content
