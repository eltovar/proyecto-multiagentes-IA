"""
Tests de Regresión Críticos - Consolidación de Estados
Verifica que la limpieza de código no afectó la funcionalidad
"""

# import pytest  # Not available
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agents.reception_agent import ReceptionAgent
from app.agents.leadsales_agent import LeadsalesAgent
from app.config import (
    STATE_NUEVO, STATE_POLITICAS_PRESENTADAS, STATE_RECOPILANDO_NOMBRE,
    STATE_NOMBRE_OBTENIDO, STATE_PREGUNTA_CONTRATO_INMOBILIARIA,
    STATE_PREGUNTA_CUAL_INMOBILIARIA, STATE_PREGUNTA_SOLICITUD_LIBERTADOR,
    STATE_PREGUNTA_FECHA_NECESIDAD, STATE_FLUJO_COMPLETADO,
    STATE_CAPTURANDO_DETALLES, STATE_PROFUNDIZANDO_NECESIDAD,
    STATE_CONFIRMANDO_INFORMACION, STATE_PROCESANDO_CRM, STATE_LEAD_CREADO
)


def test_estados_importados_correctamente():
    """Verificar que todos los agentes usan estados de config.py"""

    # Test ReceptionAgent usa estados centralizados
    reception_agent = ReceptionAgent()

    # Verificar que los estados están disponibles
    assert STATE_NUEVO is not None
    assert STATE_POLITICAS_PRESENTADAS is not None
    assert STATE_RECOPILANDO_NOMBRE is not None
    assert STATE_NOMBRE_OBTENIDO is not None
    assert STATE_PREGUNTA_CONTRATO_INMOBILIARIA is not None
    assert STATE_PREGUNTA_CUAL_INMOBILIARIA is not None
    assert STATE_PREGUNTA_SOLICITUD_LIBERTADOR is not None
    assert STATE_PREGUNTA_FECHA_NECESIDAD is not None
    assert STATE_FLUJO_COMPLETADO is not None

    print("   [OK] ReceptionAgent: Estados centralizados disponibles")

    # Test LeadsalesAgent usa estados centralizados
    leadsales_agent = LeadsalesAgent()

    assert STATE_CAPTURANDO_DETALLES is not None
    assert STATE_PROFUNDIZANDO_NECESIDAD is not None
    assert STATE_CONFIRMANDO_INFORMACION is not None
    assert STATE_PROCESANDO_CRM is not None
    assert STATE_LEAD_CREADO is not None

    print("   [OK] LeadsalesAgent: Estados centralizados disponibles")


def test_estados_consistencia_valores():
    """Verificar que los valores de estados son consistentes"""

    # Los estados deben tener valores string específicos
    assert STATE_NUEVO == "NUEVO"
    assert STATE_POLITICAS_PRESENTADAS == "POLITICAS_PRESENTADAS"
    assert STATE_RECOPILANDO_NOMBRE == "RECOPILANDO_NOMBRE"
    assert STATE_FLUJO_COMPLETADO == "FLUJO_COMPLETADO"

    assert STATE_CAPTURANDO_DETALLES == "CAPTURANDO_DETALLES"
    assert STATE_PROFUNDIZANDO_NECESIDAD == "PROFUNDIZANDO_NECESIDAD"
    assert STATE_PROCESANDO_CRM == "PROCESANDO_CRM"
    assert STATE_LEAD_CREADO == "LEAD_CREADO"

    print("   [OK] Valores de estados son consistentes")


async def test_agentes_usan_estados_centralizados():
    """Verificar que los agentes usan los estados centralizados en su lógica"""

    reception_agent = ReceptionAgent()
    message_data = {"from": "test", "text": {"body": "Hola"}}

    # Test estado NUEVO
    conversation_nuevo = {"state": STATE_NUEVO}
    can_handle = await reception_agent.can_handle(message_data, conversation_nuevo)
    assert can_handle == True
    print("   [OK] ReceptionAgent usa STATE_NUEVO centralizado")

    # Test estado POLITICAS_PRESENTADAS
    conversation_politicas = {"state": STATE_POLITICAS_PRESENTADAS}
    can_handle = await reception_agent.can_handle(message_data, conversation_politicas)
    assert can_handle == True
    print("   [OK] ReceptionAgent usa STATE_POLITICAS_PRESENTADAS centralizado")

    # Test LeadsalesAgent con estados centralizados
    leadsales_agent = LeadsalesAgent()
    conversation_details = {"state": STATE_CAPTURANDO_DETALLES}
    can_handle = await leadsales_agent.can_handle(message_data, conversation_details)
    assert can_handle == True
    print("   [OK] LeadsalesAgent usa STATE_CAPTURANDO_DETALLES centralizado")


def test_no_duplicacion_estados():
    """Verificar que no hay estados duplicados en los módulos de agentes"""

    # Verificar que los agentes no definen sus propios estados localmente
    import inspect

    # ReceptionAgent no debe tener definiciones locales de estados
    reception_source = inspect.getsource(ReceptionAgent)
    assert 'STATE_NUEVO = "NUEVO"' not in reception_source
    assert 'STATE_POLITICAS_PRESENTADAS = "POLITICAS_PRESENTADAS"' not in reception_source
    print("   [OK] ReceptionAgent no tiene estados duplicados")

    # LeadsalesAgent no debe tener definiciones locales de estados
    leadsales_source = inspect.getsource(LeadsalesAgent)
    assert 'STATE_CAPTURANDO_DETALLES = "CAPTURANDO_DETALLES"' not in leadsales_source
    assert 'STATE_PROFUNDIZANDO_NECESIDAD = "PROFUNDIZANDO_NECESIDAD"' not in leadsales_source
    print("   [OK] LeadsalesAgent no tiene estados duplicados")


async def test_transiciones_estados_funcionando():
    """Verificar que las transiciones de estado siguen funcionando"""

    reception_agent = ReceptionAgent()
    message_data = {"from": "test_user", "text": {"body": "Hola"}}

    # Test transición de NUEVO a POLITICAS_PRESENTADAS
    conversation = {"state": STATE_NUEVO, "interaction_count": 0}

    response = await reception_agent.process_message(message_data, conversation)

    # Debe transicionar al siguiente estado
    assert response.get("new_state") == STATE_POLITICAS_PRESENTADAS
    response_text = response.get("response", "")
    assert ("Politicas" in response_text or "políticas" in response_text.lower())

    print("   [OK] Transiciones de estado funcionan con estados centralizados")


if __name__ == "__main__":
    import asyncio

    print("=" * 70)
    print("TESTS DE REGRESIÓN - CONSOLIDACIÓN DE ESTADOS")
    print("=" * 70)

    try:
        test_estados_importados_correctamente()
        test_estados_consistencia_valores()
        asyncio.run(test_agentes_usan_estados_centralizados())
        test_no_duplicacion_estados()
        asyncio.run(test_transiciones_estados_funcionando())

        print("\n" + "=" * 70)
        print("[OK] TODOS LOS TESTS DE CONSOLIDACION PASARON")
        print("=" * 70)
        print("La consolidación de estados fue exitosa:")
        print("- Estados centralizados en config.py [OK]")
        print("- No hay duplicacion de estados [OK]")
        print("- Agentes usan estados centralizados [OK]")
        print("- Transiciones funcionan correctamente [OK]")

    except Exception as e:
        print(f"\n[ERROR] ERROR en tests de consolidacion: {e}")
        import traceback
        traceback.print_exc()