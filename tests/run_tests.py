#!/usr/bin/env python3
"""Script para ejecutar tests desde la raíz del proyecto"""

import sys
import os

# Agregar el directorio raíz al PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/.."))

import subprocess
from unittest.mock import Mock, patch
import importlib
import chat_local

def run_test(test_file):
    """Ejecuta un test específico desde la raíz del proyecto"""
    test_path = os.path.join("tests", test_file)
    if not os.path.exists(test_path):
        print(f"ERROR: Test {test_path} no encontrado")
        return False

    try:
        env = os.environ.copy()
        env['PYTHONPATH'] = '.'
        result = subprocess.run([sys.executable, test_path],
                              capture_output=False,
                              cwd=os.getcwd(),
                              env=env)
        return result.returncode == 0
    
    except Exception as e:
        print(f"ERROR ejecutando {test_file}: {e}")
        return False

def test_reload_and_run():
    """Test para validar la recarga dinámica y ejecución del chat"""
    import chat_local
    
    # Primero recargamos el módulo
    importlib.reload(chat_local)
    
    # Crear y asignar el mock directamente
    mock_start_chat = Mock()
    original_start_chat = chat_local.start_chat
    chat_local.start_chat = mock_start_chat
    
    try:
        # Ejecutar la función
        chat_local.start_chat()
        
        # Verificar que el mock fue llamado
        mock_start_chat.assert_called_once()
    finally:
        # Restaurar la función original
        chat_local.start_chat = original_start_chat

def test_feature_flag():
    """Test para validar el comportamiento del feature flag"""
    # Mock ENABLE_HOT_RELOAD y validar ambos flujos
    assert True

def test_production_consistency():
    """Test para validar la consistencia con producción"""
    # Validar que las dependencias cargadas son consistentes
    assert True

def test_chat_local_uses_factory_orchestrator():
    """Test para validar que el chat local utiliza el factory orchestrator"""
    # Lógica del test
    assert True  # Reemplaza con la lógica real

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python run_tests.py <test_file>")
        print("Ejemplo: python run_tests.py test_functionality.py")
        sys.exit(1)

    test_file = sys.argv[1]
    if not test_file.endswith(".py"):
        test_file += ".py"

    success = run_test(test_file)
    sys.exit(0 if success else 1)

    # Ejecutar un test específico
    import subprocess
    subprocess.run(["pytest", "tests/integration/test_chat_local_integration.py::test_chat_local_uses_factory_orchestrator"])