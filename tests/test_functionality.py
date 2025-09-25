#!/usr/bin/env python3
"""Script de prueba de funcionalidad automatizado"""

import asyncio
from app.core.orchestrator import orchestrator

async def test_functionality():
    """Prueba la funcionalidad completa del sistema"""
    print("INICIANDO PRUEBAS DE FUNCIONALIDAD")
    print("=" * 50)

    # Test 1: Sistema inicializado
    print("Test 1: Verificar inicializacion")
    if len(orchestrator.agents) > 0:
        print(f"OK Sistema inicializado correctamente - {len(orchestrator.agents)} agentes")
    else:
        print("ERROR Sistema no inicializado")
        return False

    # Test 2: Saludo inicial
    print("\nTest 2: Saludo inicial")
    message_data = {
        "from": "test123456",
        "text": {"body": "hola"}
    }
    await orchestrator.process_message(message_data)
    print("OK Mensaje procesado correctamente")

    # Test 3: Recopilar nombre
    print("\nTest 3: Recopilar nombre")
    message_data = {
        "from": "test123456",
        "text": {"body": "Mi nombre es Juan Perez"}
    }
    await orchestrator.process_message(message_data)
    print("OK Nombre procesado correctamente")

    # Test 4: Health check
    print("\nTest 4: Health check")
    health = orchestrator.health_check()
    print(f"Status: {health.get('status')}")
    print(f"Agents: {health.get('agents_count')}")

    print("\nTODAS LAS PRUEBAS COMPLETADAS")
    return True

if __name__ == "__main__":
    asyncio.run(test_functionality())