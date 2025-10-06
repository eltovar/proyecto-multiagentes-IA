# -*- coding: utf-8 -*-
"""
Tests de validación estática para SupportAgent
Verifica estructura del código sin ejecutar inicialización
"""

import pytest
import ast
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))


def get_support_agent_ast():
    """Parse support_agent.py y retorna AST"""
    file_path = os.path.join(
        os.path.dirname(__file__),
        '../..',
        'app',
        'agents',
        'support_agent.py'
    )

    with open(file_path, 'r', encoding='utf-8') as f:
        return ast.parse(f.read(), filename='support_agent.py')


def get_class_methods(tree, class_name):
    """Extrae métodos de una clase del AST"""
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            methods = []
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    methods.append(item.name)
            return methods
    return []


def get_method_calls_in_method(tree, class_name, method_name, called_method):
    """Cuenta cuántas veces un método llama a otro método específico"""
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == method_name:
                    count = 0
                    for subnode in ast.walk(item):
                        if isinstance(subnode, ast.Call):
                            if isinstance(subnode.func, ast.Attribute):
                                if subnode.func.attr == called_method:
                                    count += 1
                    return count
    return 0


def test_helper_methods_exist():
    """Verifica que métodos helper existen en SupportAgent"""
    tree = get_support_agent_ast()
    methods = get_class_methods(tree, 'SupportAgent')

    required_helpers = [
        '_empty_rag_result',
        '_format_greeting',
        '_build_response_data'
    ]

    for helper in required_helpers:
        assert helper in methods, f"Helper method '{helper}' not found in SupportAgent"


def test_core_methods_exist():
    """Verifica que métodos core del tri-path existen"""
    tree = get_support_agent_ast()
    methods = get_class_methods(tree, 'SupportAgent')

    required_methods = [
        'process_message',
        '_classify_user_intent',
        '_search_rag_for_routing',
        '_determine_routing_path',
        '_handle_camino_1_inmueble',
        '_handle_camino_2_departamento',
        '_handle_camino_3_general'
    ]

    for method in required_methods:
        assert method in methods, f"Core method '{method}' not found in SupportAgent"


def test_empty_rag_result_is_used():
    """Verifica que _empty_rag_result se usa en el código"""
    tree = get_support_agent_ast()

    # Check usage in _search_rag_for_routing
    usage_count = get_method_calls_in_method(
        tree,
        'SupportAgent',
        '_search_rag_for_routing',
        '_empty_rag_result'
    )

    assert usage_count >= 2, f"_empty_rag_result should be used at least 2 times in _search_rag_for_routing, found {usage_count}"


def test_build_response_data_is_used():
    """Verifica que _build_response_data se usa en handlers"""
    tree = get_support_agent_ast()

    handlers = [
        '_handle_camino_1_inmueble',
        '_handle_camino_2_departamento',
        '_handle_camino_3_general'
    ]

    total_usage = 0
    for handler in handlers:
        count = get_method_calls_in_method(
            tree,
            'SupportAgent',
            handler,
            '_build_response_data'
        )
        total_usage += count

    assert total_usage >= 4, f"_build_response_data should be used at least 4 times across handlers, found {total_usage}"


def test_format_greeting_is_used():
    """Verifica que _format_greeting se usa en handlers"""
    tree = get_support_agent_ast()

    handlers = [
        '_handle_camino_1_inmueble',
        '_handle_camino_2_departamento'
    ]

    total_usage = 0
    for handler in handlers:
        count = get_method_calls_in_method(
            tree,
            'SupportAgent',
            handler,
            '_format_greeting'
        )
        total_usage += count

    assert total_usage >= 3, f"_format_greeting should be used at least 3 times across handlers, found {total_usage}"


def test_no_hardcoded_rag_empty_dicts():
    """Verifica que no hay diccionarios vacíos hardcodeados para RAG results"""
    file_path = os.path.join(
        os.path.dirname(__file__),
        '../..',
        'app',
        'agents',
        'support_agent.py'
    )

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Should not have multiple occurrences of hardcoded empty RAG structure
    # (allowing for the definition in _empty_rag_result itself)
    pattern_count = content.count('"documents": []')

    # Should be mostly in _empty_rag_result definition only
    assert pattern_count <= 2, f"Found {pattern_count} hardcoded empty RAG structures, should use _empty_rag_result() helper"


def test_department_contacts_imported():
    """Verifica que DEPARTMENT_CONTACTS se importa de config"""
    file_path = os.path.join(
        os.path.dirname(__file__),
        '../..',
        'app',
        'agents',
        'support_agent.py'
    )

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    assert 'from app.config import' in content
    assert 'DEPARTMENT_CONTACTS' in content


def test_transferido_state_used():
    """Verifica que estado TRANSFERIDO se usa en CAMINO 2"""
    file_path = os.path.join(
        os.path.dirname(__file__),
        '../..',
        'app',
        'agents',
        'support_agent.py'
    )

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Should use TRANSFERIDO in _handle_camino_2_departamento
    assert 'new_state="TRANSFERIDO"' in content
    # Should NOT use old DEPARTMENT_REDIRECT
    assert 'new_state="DEPARTMENT_REDIRECT"' not in content


def test_rag_context_used_metadata():
    """Verifica que metadata rag_context_used se incluye en CAMINO 1"""
    file_path = os.path.join(
        os.path.dirname(__file__),
        '../..',
        'app',
        'agents',
        'support_agent.py'
    )

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    assert 'rag_context_used' in content, "CAMINO 1 should include rag_context_used in metadata"


def test_handoff_reason_metadata():
    """Verifica que metadata handoff_reason se incluye en CAMINO 2"""
    file_path = os.path.join(
        os.path.dirname(__file__),
        '../..',
        'app',
        'agents',
        'support_agent.py'
    )

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    assert 'handoff_reason' in content, "CAMINO 2 should include handoff_reason in metadata"


def test_classify_with_prompt_used():
    """Verifica que classify_with_prompt se usa para generación de mensajes"""
    file_path = os.path.join(
        os.path.dirname(__file__),
        '../..',
        'app',
        'agents',
        'support_agent.py'
    )

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    assert 'classify_with_prompt' in content, "Should use classify_with_prompt for message generation"
    assert 'response_format="text"' in content, "Should use TEXT mode for message generation"


def test_routing_paths_constants():
    """Verifica que constantes de routing paths se usan correctamente"""
    file_path = os.path.join(
        os.path.dirname(__file__),
        '../..',
        'app',
        'agents',
        'support_agent.py'
    )

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    required_paths = [
        'CAMINO_1_INMUEBLE',
        'CAMINO_2_DEPARTAMENTO',
        'CAMINO_3_GENERAL'
    ]

    for path in required_paths:
        assert path in content, f"Routing path constant '{path}' not found"


def test_docstrings_present():
    """Verifica que métodos principales tienen docstrings"""
    tree = get_support_agent_ast()

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == 'SupportAgent':
            important_methods = [
                'process_message',
                '_handle_camino_1_inmueble',
                '_handle_camino_2_departamento',
                '_handle_camino_3_general',
                '_empty_rag_result',
                '_format_greeting',
                '_build_response_data'
            ]

            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name in important_methods:
                    # Check if first statement is a docstring
                    has_docstring = (
                        len(item.body) > 0 and
                        isinstance(item.body[0], ast.Expr) and
                        isinstance(item.body[0].value, ast.Constant) and
                        isinstance(item.body[0].value.value, str)
                    )
                    assert has_docstring, f"Method '{item.name}' should have a docstring"
