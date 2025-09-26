#!/usr/bin/env python3
"""Test simple de validación de nombres"""

import sys
import os

# Setup path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agents.reception_agent import ReceptionAgent

def test_name_validation():
    """Test específico para validación de nombres"""

    print("TEST: VALIDACION DE NOMBRES")
    print("=" * 25)

    agent = ReceptionAgent()

    # Test cases: respuestas que NO deben ser aceptadas como nombres
    invalid_inputs = ["no", "si", "ok", "hola", "bien"]

    print("1. RESPUESTAS INVALIDAS:")
    for test_input in invalid_inputs:
        result = agent._extract_name(test_input)
        status = "RECHAZADO" if result is None else f"ACEPTADO: {result}"
        print(f"   '{test_input}' = {status}")

    print("\n2. NOMBRES VALIDOS:")
    valid_inputs = ["Juan", "Maria", "Carlos"]

    for test_input in valid_inputs:
        result = agent._extract_name(test_input)
        status = f"ACEPTADO: {result}" if result else "RECHAZADO"
        print(f"   '{test_input}' = {status}")

    # Verificar específicamente el caso problemático "no"
    no_result = agent._extract_name("no")
    print(f"\n3. CASO PROBLEMATICO:")
    print(f"   'no' = {'RECHAZADO (CORRECTO)' if no_result is None else f'ACEPTADO (ERROR): {no_result}'}")

if __name__ == "__main__":
    test_name_validation()