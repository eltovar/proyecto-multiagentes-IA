"""
Configuración global de pytest
"""
import os
import sys

# Agregar directorio raíz al PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))