"""
Test de Regresión: Validar que el output del scoring no cambia (snapshot testing)
"""
import pytest
from app.services.leadsales import LeadsalesService


class TestScoringOutputRegression:
    """Snapshot tests para validar que el output de scoring permanece estable"""

    @pytest.mark.asyncio
    async def test_scoring_output_regression(self):
        """Snapshot test: verificar que output no cambió"""
        service = LeadsalesService()
        service.initialize()

        test_cases = [
            {
                "needs": "Busco apartamento",
                "expected_score_range": (80, 100),  # Combina keywords high-value
                "expected_tags": ["APARTAMENTO"],
                "expected_priority": "MEDIA"
            },
            {
                "needs": "Quiero comprar casa urgente millones",
                "expected_score_range": (80, 100),
                "expected_tags": ["COMPRA", "CASA", "URGENTE", "PRESUPUESTO_DEFINIDO"],
                "expected_priority": "ALTA"
            },
        ]

        for case in test_cases:
            result = service._score_lead(case["needs"], {})

            assert case["expected_score_range"][0] <= result["quality_score"] <= case["expected_score_range"][1], \
                f"Score fuera de rango para '{case['needs']}': {result['quality_score']}"

            for tag in case["expected_tags"]:
                assert tag in result["tags"], \
                    f"Tag {tag} faltante en {result['tags']} para '{case['needs']}'"

            assert case["expected_priority"] in result["priority"], \
                f"Priority esperada {case['expected_priority']}, obtenida {result['priority']} para '{case['needs']}'"

    @pytest.mark.asyncio
    async def test_low_quality_baseline(self):
        """Baseline: mensaje de baja calidad debe dar score bajo"""
        service = LeadsalesService()
        service.initialize()

        low_quality_messages = [
            "Hola",
            "Info",
            "Me interesa",
            "Quiero saber más"
        ]

        for message in low_quality_messages:
            result = service._score_lead(message, {})
            assert result["quality_score"] < 50, \
                f"Score demasiado alto ({result['quality_score']}) para mensaje de baja calidad: '{message}'"

    @pytest.mark.asyncio
    async def test_high_quality_baseline(self):
        """Baseline: mensaje de alta calidad debe dar score alto"""
        service = LeadsalesService()
        service.initialize()

        high_quality_messages = [
            "Urgente busco apartamento para comprar en laureles con presupuesto de 500 millones",
            "Necesito casa rapido en envigado tengo 300 millones disponibles",
            "Quiero comprar apartamento urgente tengo presupuesto definido"
        ]

        for message in high_quality_messages:
            result = service._score_lead(message, {})
            assert result["quality_score"] >= 70, \
                f"Score demasiado bajo ({result['quality_score']}) para mensaje de alta calidad: '{message}'"

    @pytest.mark.asyncio
    async def test_transaction_type_tags_baseline(self):
        """Baseline: tags de tipo de transacción detectados correctamente"""
        service = LeadsalesService()
        service.initialize()

        test_cases = [
            {"needs": "Quiero comprar apartamento", "expected_tag": "COMPRA"},
            {"needs": "Busco casa para arrendar", "expected_tag": "ARRIENDO"},
            {"needs": "Me interesa vender mi propiedad", "expected_tag": "VENTA"},
        ]

        for case in test_cases:
            result = service._score_lead(case["needs"], {})
            assert case["expected_tag"] in result["tags"], \
                f"Tag {case['expected_tag']} no detectado en {result['tags']} para: '{case['needs']}'"

    @pytest.mark.asyncio
    async def test_property_type_tags_baseline(self):
        """Baseline: tags de tipo de propiedad detectados correctamente"""
        service = LeadsalesService()
        service.initialize()

        test_cases = [
            {"needs": "Busco apartamento", "expected_tag": "APARTAMENTO"},
            {"needs": "Quiero casa", "expected_tag": "CASA"},
            {"needs": "Busco local comercial", "expected_tag": "LOCAL_COMERCIAL"},
        ]

        for case in test_cases:
            result = service._score_lead(case["needs"], {})
            assert case["expected_tag"] in result["tags"], \
                f"Tag {case['expected_tag']} no detectado en {result['tags']} para: '{case['needs']}'"

    @pytest.mark.asyncio
    async def test_urgency_priority_baseline(self):
        """Baseline: prioridad según urgencia"""
        service = LeadsalesService()
        service.initialize()

        test_cases = [
            {"needs": "urgente busco apartamento", "min_priority": "ALTA"},
            {"needs": "rapido necesito casa", "min_priority": "ALTA"},
            {"needs": "tengo 500 millones para apartamento", "min_priority": "MEDIA"},
            {"needs": "quisiera informacion de casas", "min_priority": "MEDIA"},
        ]

        for case in test_cases:
            result = service._score_lead(case["needs"], {})
            # Verificar que la prioridad sea al menos la esperada
            priorities = ["BAJA", "MEDIA", "ALTA"]
            expected_idx = priorities.index(case["min_priority"])
            actual_idx = next((i for i, p in enumerate(priorities) if p in result["priority"]), 0)

            assert actual_idx >= expected_idx, \
                f"Prioridad muy baja para '{case['needs']}': esperada >= {case['min_priority']}, obtenida {result['priority']}"

    @pytest.mark.asyncio
    async def test_additional_data_libertador_tag(self):
        """Baseline: tag LIBERTADOR_APROBADO cuando additional_data lo indica"""
        service = LeadsalesService()
        service.initialize()

        # Con aprobación Libertador (usa key correcta)
        result = service._score_lead(
            "Busco apartamento",
            {"tiene_solicitud_libertador": True}
        )
        assert "LIBERTADOR_APROBADO" in result["tags"]

        # Sin aprobación Libertador
        result = service._score_lead(
            "Busco apartamento",
            {"tiene_solicitud_libertador": False}
        )
        assert "LIBERTADOR_APROBADO" not in result["tags"]

    @pytest.mark.asyncio
    async def test_scoring_metadata_structure(self):
        """Baseline: estructura de metadata de scoring"""
        service = LeadsalesService()
        service.initialize()

        result = service._score_lead("Busco apartamento para comprar", {})

        # Verificar estructura de metadata
        assert "scoring_metadata" in result
        metadata = result["scoring_metadata"]

        # Metadata real: quality_factors, quality_confidence, quality_reasoning
        assert "quality_factors" in metadata
        assert "quality_confidence" in metadata
        assert "quality_reasoning" in metadata

        assert isinstance(metadata["quality_factors"], dict)
        assert isinstance(metadata["quality_confidence"], (int, float))
        assert isinstance(metadata["quality_reasoning"], str)
