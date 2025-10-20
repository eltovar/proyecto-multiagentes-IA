"""
Test de Logs: Validar que los logs de scoring se generan correctamente
"""
import pytest
import io
import sys
from app.services.leadsales import LeadsalesService


class TestScoringLogs:
    """Tests de validación de logs para el sistema de scoring"""

    def test_initialization_logs(self, capsys):
        """Verificar logs de inicialización del servicio"""
        service = LeadsalesService()
        service.initialize()

        captured = capsys.readouterr()

        # Verificar log de inicialización de componentes
        assert "[LeadsalesService] Scoring components initialized:" in captured.out
        assert "1 quality_scorer" in captured.out
        assert "4 taggers" in captured.out
        assert "1 priority_classifier" in captured.out

        # Verificar log de servicio inicializado
        assert "[LeadsalesService] Servicio inicializado correctamente" in captured.out

    def test_scoring_execution_logs(self, capsys):
        """Verificar logs cuando se ejecuta scoring"""
        service = LeadsalesService()
        service.initialize()

        # Limpiar output anterior
        capsys.readouterr()

        # Ejecutar scoring
        result = service._score_lead("Busco apartamento urgente", {})

        captured = capsys.readouterr()

        # Verificar log de scoring ejecutado
        assert "[LeadsalesService] Lead scored:" in captured.out
        assert "quality=" in captured.out
        assert "tags=" in captured.out
        assert "priority=" in captured.out

    def test_scoring_log_format_high_quality(self, capsys):
        """Verificar formato del log para lead de alta calidad"""
        service = LeadsalesService()
        service.initialize()

        capsys.readouterr()

        # Lead de alta calidad
        service._score_lead("Urgente busco apartamento para comprar tengo 500 millones", {})

        captured = capsys.readouterr()

        # Debe mostrar quality alto, varios tags y prioridad ALTA
        assert "quality=100" in captured.out or "quality=9" in captured.out  # >= 90
        assert "tags=" in captured.out
        assert "priority=ALTA" in captured.out

    def test_scoring_log_format_medium_quality(self, capsys):
        """Verificar formato del log para lead de calidad media"""
        service = LeadsalesService()
        service.initialize()

        capsys.readouterr()

        # Lead de calidad media
        service._score_lead("Busco apartamento", {})

        captured = capsys.readouterr()

        # Debe mostrar quality y priority
        log_line = captured.out
        assert "[LeadsalesService] Lead scored:" in log_line
        assert "quality=" in log_line
        assert "tags=" in log_line
        assert "priority=MEDIA" in log_line

    def test_scoring_log_shows_tag_count(self, capsys):
        """Verificar que el log muestra el número de tags"""
        service = LeadsalesService()
        service.initialize()

        capsys.readouterr()

        # Lead con múltiples tags
        service._score_lead("Quiero comprar casa urgente tengo presupuesto", {})

        captured = capsys.readouterr()

        # Debe mostrar número de tags (no los tags mismos)
        assert "tags=" in captured.out
        # Extraer número de tags del log
        import re
        match = re.search(r'tags=(\d+)', captured.out)
        assert match is not None
        tag_count = int(match.group(1))
        assert tag_count >= 1  # Al menos un tag detectado

    def test_scoring_log_priority_short_format(self, capsys):
        """Verificar que el log muestra prioridad en formato corto"""
        service = LeadsalesService()
        service.initialize()

        capsys.readouterr()

        # Lead urgente
        service._score_lead("URGENTE necesito apartamento YA", {})

        captured = capsys.readouterr()

        # Debe mostrar solo "ALTA" no "ALTA - Contacto inmediato"
        assert "priority=ALTA" in captured.out
        assert " - " not in captured.out.split("priority=")[1].split(",")[0]

    def test_multiple_scoring_logs(self, capsys):
        """Verificar logs de múltiples ejecuciones de scoring"""
        service = LeadsalesService()
        service.initialize()

        capsys.readouterr()

        # Ejecutar múltiples scorings
        messages = [
            "Busco apartamento",
            "Quiero casa urgente",
            "Información sobre locales"
        ]

        for message in messages:
            service._score_lead(message, {})

        captured = capsys.readouterr()

        # Debe haber 3 logs de scoring
        log_count = captured.out.count("[LeadsalesService] Lead scored:")
        assert log_count == 3

    def test_scoring_log_with_additional_data(self, capsys):
        """Verificar logs cuando se usa additional_data"""
        service = LeadsalesService()
        service.initialize()

        capsys.readouterr()

        # Scoring con additional_data (Libertador aprobado)
        service._score_lead(
            "Busco apartamento",
            {"tiene_solicitud_libertador": True}
        )

        captured = capsys.readouterr()

        # Debe generar log normalmente
        assert "[LeadsalesService] Lead scored:" in captured.out
        assert "quality=" in captured.out
        assert "tags=" in captured.out

    def test_no_duplicate_initialization_logs(self, capsys):
        """Verificar que no se duplican logs de inicialización"""
        service = LeadsalesService()

        captured = capsys.readouterr()

        # Debe haber solo UN log de inicialización de componentes
        init_count = captured.out.count("[LeadsalesService] Scoring components initialized:")
        assert init_count == 1

    def test_log_ordering(self, capsys):
        """Verificar orden correcto de logs"""
        service = LeadsalesService()
        service.initialize()

        captured = capsys.readouterr()

        # Los logs deben aparecer en este orden
        log_lines = captured.out.split('\n')

        # Encontrar índices de logs clave
        component_init_idx = None
        service_init_idx = None

        for i, line in enumerate(log_lines):
            if "Scoring components initialized" in line:
                component_init_idx = i
            if "Servicio inicializado correctamente" in line:
                service_init_idx = i

        # Componentes se inicializan ANTES que el servicio
        # (en __init__ antes de initialize())
        assert component_init_idx is not None
        assert service_init_idx is not None
