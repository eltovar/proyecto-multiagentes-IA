#!/usr/bin/env python3
"""Script para ejecutar tests desde la raíz del proyecto"""

import sys
import os
import subprocess

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