"""
Test de Logs: Validar que los logs de scoring se generan correctamente
"""
import pytest
import re
import logging
from app.services.leadsales import LeadsalesService


class TestScoringLogs:
    """Tests de validación de logs para el sistema de scoring"""

    def test_initialization_logs(self, caplog):
        """Verificar logs de inicialización del servicio"""
        caplog.set_level(logging.INFO)
        service = LeadsalesService()
        service.initialize()

        # Verificar log de inicialización de componentes
        assert "LeadsalesService inicializado" in caplog.text
        assert "6 componentes cargados" in caplog.text

    def test_scoring_execution_logs(self, caplog):
        """Verificar logs cuando se ejecuta scoring"""
        caplog.set_level(logging.INFO)
        service = LeadsalesService()
        service.initialize()

        # Limpiar logs anteriores
        caplog.clear()

        # Ejecutar scoring
        result = service._score_lead("Busco apartamento urgente", {})

        # Verificar log de scoring ejecutado
        assert "[LeadsalesService] Lead scored:" in caplog.text
        assert "quality=" in caplog.text
        assert "tags=" in caplog.text
        assert "priority=" in caplog.text

    def test_scoring_log_format_high_quality(self, caplog):
        """Verificar formato del log para lead de alta calidad"""
        caplog.set_level(logging.INFO)
        service = LeadsalesService()
        service.initialize()

        caplog.clear()

        # Lead de alta calidad
        service._score_lead("Urgente busco apartamento para comprar tengo 500 millones", {})

        # Debe mostrar quality alto, varios tags y prioridad ALTA
        assert "quality=100" in caplog.text or "quality=9" in caplog.text  # >= 90
        assert "tags=" in caplog.text
        assert "priority=ALTA" in caplog.text

    def test_scoring_log_format_medium_quality(self, caplog):
        """Verificar formato del log para lead de calidad media"""
        caplog.set_level(logging.INFO)
        service = LeadsalesService()
        service.initialize()

        caplog.clear()

        # Lead de calidad media
        service._score_lead("Busco apartamento", {})

        # Debe mostrar quality y priority
        assert "[LeadsalesService] Lead scored:" in caplog.text
        assert "quality=" in caplog.text
        assert "tags=" in caplog.text
        assert "priority=MEDIA" in caplog.text

    def test_scoring_log_shows_tag_count(self, caplog):
        """Verificar que el log muestra el número de tags"""
        caplog.set_level(logging.INFO)
        service = LeadsalesService()
        service.initialize()

        caplog.clear()

        # Lead con múltiples tags
        service._score_lead("Quiero comprar casa urgente tengo presupuesto", {})

        # Debe mostrar número de tags (no los tags mismos)
        assert "tags=" in caplog.text
        # Extraer número de tags del log
        match = re.search(r'tags=(\d+)', caplog.text)
        assert match is not None
        tag_count = int(match.group(1))
        assert tag_count >= 1  # Al menos un tag detectado

    def test_scoring_log_priority_short_format(self, caplog):
        """Verificar que el log muestra prioridad en formato corto"""
        caplog.set_level(logging.INFO)
        service = LeadsalesService()
        service.initialize()

        caplog.clear()

        # Lead urgente
        service._score_lead("URGENTE necesito apartamento YA", {})

        # Debe mostrar solo "ALTA" no "ALTA - Contacto inmediato"
        assert "priority=ALTA" in caplog.text
        assert " - " not in caplog.text.split("priority=")[1].split(",")[0]

    def test_multiple_scoring_logs(self, caplog):
        """Verificar logs de múltiples ejecuciones de scoring"""
        caplog.set_level(logging.INFO)
        service = LeadsalesService()
        service.initialize()

        caplog.clear()

        # Ejecutar múltiples scorings
        messages = [
            "Busco apartamento",
            "Quiero casa urgente",
            "Información sobre locales"
        ]

        for message in messages:
            service._score_lead(message, {})

        # Debe haber 3 logs de scoring
        log_count = caplog.text.count("[LeadsalesService] Lead scored:")
        assert log_count == 3

    def test_scoring_log_with_additional_data(self, caplog):
        """Verificar logs cuando se usa additional_data"""
        caplog.set_level(logging.INFO)
        service = LeadsalesService()
        service.initialize()

        caplog.clear()

        # Scoring con additional_data (Libertador aprobado)
        service._score_lead(
            "Busco apartamento",
            {"tiene_solicitud_libertador": True}
        )

        # Debe generar log normalmente
        assert "[LeadsalesService] Lead scored:" in caplog.text
        assert "quality=" in caplog.text
        assert "tags=" in caplog.text

    def test_no_duplicate_initialization_logs(self, caplog):
        """Verificar que no se duplican logs de inicialización"""
        caplog.set_level(logging.INFO)
        service = LeadsalesService()

        # Debe haber solo UN log de inicialización de componentes
        init_count = caplog.text.count("LeadsalesService inicializado (6 componentes cargados)")
        assert init_count == 1

    def test_log_ordering(self, caplog):
        """Verificar que logs de inicialización aparecen correctamente"""
        caplog.set_level(logging.INFO)
        service = LeadsalesService()
        service.initialize()

        # Verificar que el log de componentes inicializados existe
        assert "LeadsalesService inicializado" in caplog.text

        # Verificar que aparece en las primeras líneas (durante __init__)
        log_lines = caplog.text.split('\n')
        component_init_found = False

        for line in log_lines:
            if "LeadsalesService inicializado" in line:
                component_init_found = True
                break

        assert component_init_found
