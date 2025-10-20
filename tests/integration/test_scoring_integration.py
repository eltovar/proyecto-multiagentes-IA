import pytest
from app.services.leadsales import LeadsalesService


@pytest.mark.asyncio
class TestDemoModeScoring:
    """Tests de scoring en modo demo (regresión)"""

    async def test_demo_mode_scoring_matches_refactored(self):
        """Verificar que scoring demo produce mismos resultados que antes"""
        service = LeadsalesService()
        service.initialize()

        # Forzar modo demo
        original_is_demo = service._is_demo_mode

        def force_demo_mode():
            return True

        service._is_demo_mode = force_demo_mode

        result = await service.create_lead(
            "Test Cliente",
            "+57300999",
            "Busco casa para comprar con presupuesto de 500 millones urgente",
            {"tiene_solicitud_libertador": "Sí"}
        )

        # Restaurar método original
        service._is_demo_mode = original_is_demo

        # Verificar estructura de respuesta demo
        assert result["success"] == True
        assert "customer_data" in result
        assert result["demo_mode"] == True

        customer_data = result["customer_data"]

        # Validar scoring
        assert "quality_score" in customer_data
        assert "tags" in customer_data
        assert "priority" in customer_data

        assert customer_data["quality_score"] >= 80, \
            "Lead de alta calidad debe tener score alto"
        assert "COMPRA" in customer_data["tags"], "Debe detectar tag COMPRA"
        assert "CASA" in customer_data["tags"], "Debe detectar tag CASA"
        assert "URGENTE" in customer_data["tags"], "Debe detectar tag URGENTE"
        assert "LIBERTADOR_APROBADO" in customer_data["tags"], \
            "Debe detectar tag LIBERTADOR"
        assert "ALTA" in customer_data["priority"], "Prioridad debe ser ALTA"

    async def test_demo_mode_includes_scoring_metadata(self):
        """Verificar que modo demo incluye metadata de scoring"""
        service = LeadsalesService()
        service.initialize()

        # Forzar modo demo
        service._is_demo_mode = lambda: True

        result = await service.create_lead(
            "Cliente Demo",
            "+57301111111",
            "Busco apartamento",
            {}
        )

        customer_data = result["customer_data"]

        # Verificar que incluye metadata adicional de scoring
        assert "quality_confidence" in customer_data
        assert "quality_factors" in customer_data
        assert "quality_reasoning" in customer_data

        # Verificar tipos
        assert isinstance(customer_data["quality_confidence"], (int, float))
        assert isinstance(customer_data["quality_factors"], dict)
        assert isinstance(customer_data["quality_reasoning"], str)

    async def test_demo_mode_low_quality_lead(self):
        """Verificar scoring de lead de baja calidad en demo"""
        service = LeadsalesService()
        service.initialize()
        service._is_demo_mode = lambda: True

        result = await service.create_lead(
            "Cliente Bajo",
            "+57302222222",
            "Solo información general",
            {}
        )

        customer_data = result["customer_data"]

        # Lead de baja calidad debe tener score bajo
        assert customer_data["quality_score"] < 70
        assert "MEDIA" in customer_data["priority"]
        # Tags puede estar vacío o con pocas tags
        assert len(customer_data["tags"]) <= 2

    async def test_demo_mode_medium_quality_lead(self):
        """Verificar scoring de lead de calidad media en demo"""
        service = LeadsalesService()
        service.initialize()
        service._is_demo_mode = lambda: True

        result = await service.create_lead(
            "Cliente Medio",
            "+57303333333",
            "Busco apartamento para arrendar en Laureles",  # "arrendar" (tagger busca esta palabra)
            {}
        )

        customer_data = result["customer_data"]

        # Lead de calidad buena (apartamento + busco + arrendar = keywords medium/high)
        # Score esperado: ~90 por combinación de keywords
        assert customer_data["quality_score"] >= 50
        assert "ARRIENDO" in customer_data["tags"]
        assert "APARTAMENTO" in customer_data["tags"]


@pytest.mark.asyncio
class TestScoringConsistency:
    """Tests de consistencia entre demo y producción"""

    async def test_same_input_same_scoring_demo_and_prod(self):
        """Verificar que mismo input genera mismo scoring en demo y prod"""
        service = LeadsalesService()
        service.initialize()

        customer_needs = "Comprar casa en Envigado presupuesto 300 millones"
        additional_data = {"tiene_solicitud_libertador": True}

        # Calcular scoring directamente (usado por ambos modos)
        scoring_result = service._score_lead(customer_needs, additional_data)

        # Verificar resultado
        assert scoring_result["quality_score"] > 70
        assert "COMPRA" in scoring_result["tags"]
        assert "CASA" in scoring_result["tags"]
        assert "LIBERTADOR_APROBADO" in scoring_result["tags"]
        assert "PRESUPUESTO_DEFINIDO" in scoring_result["tags"]

    async def test_multiple_transactions_detected(self):
        """Verificar detección de múltiples tipos de transacción"""
        service = LeadsalesService()

        # Mensaje ambiguo con múltiples intenciones
        scoring_result = service._score_lead(
            "Quiero vender mi casa y comprar un apartamento",
            {}
        )

        # Debe detectar ambas transacciones
        assert "COMPRA" in scoring_result["tags"]
        assert "VENTA" in scoring_result["tags"]
        assert "CASA" in scoring_result["tags"]
        assert "APARTAMENTO" in scoring_result["tags"]

    async def test_tags_limited_to_5_max(self):
        """Verificar que tags están limitadas a máximo 5"""
        service = LeadsalesService()

        # Mensaje con muchas keywords
        scoring_result = service._score_lead(
            "Comprar vender arrendar casa apartamento urgente presupuesto millones",
            {"tiene_solicitud_libertador": True}
        )

        # Máximo 5 tags
        assert len(scoring_result["tags"]) <= 5

    async def test_tags_are_unique(self):
        """Verificar que tags no se duplican"""
        service = LeadsalesService()

        scoring_result = service._score_lead(
            "Comprar comprar casa casa apartamento apartamento",
            {}
        )

        # Verificar que no hay duplicados
        assert len(scoring_result["tags"]) == len(set(scoring_result["tags"]))


@pytest.mark.asyncio
class TestScoringEdgeCases:
    """Tests de casos extremos de scoring"""

    async def test_empty_needs_message(self):
        """Verificar scoring con mensaje vacío"""
        service = LeadsalesService()

        scoring_result = service._score_lead("", {})

        # Debe retornar estructura válida aunque esté vacío
        assert "quality_score" in scoring_result
        assert "tags" in scoring_result
        assert "priority" in scoring_result

        # Score mínimo
        assert scoring_result["quality_score"] >= 30  # Mínimo del algoritmo

    async def test_very_short_message(self):
        """Verificar scoring con mensaje muy corto"""
        service = LeadsalesService()

        scoring_result = service._score_lead("casa", {})

        assert scoring_result["quality_score"] >= 30
        assert "CASA" in scoring_result["tags"]

    async def test_very_long_message(self):
        """Verificar scoring con mensaje muy largo"""
        service = LeadsalesService()

        long_message = """
        Busco apartamento para comprar en el poblado o envigado,
        tengo un presupuesto de 500 millones y necesito urgentemente
        porque me vence el contrato de arriendo. Busco 3 habitaciones,
        2 baños, con parqueadero y útil. Zona segura y cerca del metro.
        Ya tengo aprobación del banco Libertador.
        """

        scoring_result = service._score_lead(long_message, {})

        # Debe procesar correctamente mensaje largo
        assert scoring_result["quality_score"] > 80
        assert "COMPRA" in scoring_result["tags"]
        assert "APARTAMENTO" in scoring_result["tags"]
        assert "URGENTE" in scoring_result["tags"]

    async def test_message_with_special_characters(self):
        """Verificar scoring con caracteres especiales"""
        service = LeadsalesService()

        scoring_result = service._score_lead(
            "Busco casa!!! Urgente!!! $$$ 500 millones $$$",
            {}
        )

        # Debe ignorar caracteres especiales y procesar correctamente
        assert "CASA" in scoring_result["tags"]
        assert "URGENTE" in scoring_result["tags"]

    async def test_message_case_insensitive(self):
        """Verificar que scoring es case-insensitive"""
        service = LeadsalesService()

        result1 = service._score_lead("COMPRAR CASA URGENTE", {})
        result2 = service._score_lead("comprar casa urgente", {})
        result3 = service._score_lead("Comprar Casa Urgente", {})

        # Todos deben dar el mismo resultado
        assert result1["tags"] == result2["tags"] == result3["tags"]
        assert result1["quality_score"] == result2["quality_score"] == result3["quality_score"]


@pytest.mark.asyncio
class TestPriorityClassification:
    """Tests específicos de clasificación de prioridad"""

    async def test_urgent_keywords_high_priority(self):
        """Verificar que keywords de urgencia generan prioridad alta"""
        service = LeadsalesService()

        urgent_messages = [
            "URGENTE necesito apartamento",
            "rapido busco casa",  # Sin tilde (scorer busca sin tilde)
            "Necesito YA un local",
            "Inmediato arriendo"
        ]

        for message in urgent_messages:
            scoring_result = service._score_lead(message, {})
            assert "ALTA" in scoring_result["priority"], \
                f"Mensaje urgente debe tener prioridad ALTA: {message}"

    async def test_budget_keywords_medium_high_priority(self):
        """Verificar que presupuesto definido genera prioridad media-alta"""
        service = LeadsalesService()

        scoring_result = service._score_lead(
            "Busco casa presupuesto 400 millones",
            {}
        )

        assert "MEDIA-ALTA" in scoring_result["priority"]

    async def test_information_query_medium_priority(self):
        """Verificar que consultas informativas generan prioridad media"""
        service = LeadsalesService()

        scoring_result = service._score_lead(
            "Información sobre apartamentos disponibles",
            {}
        )

        assert "MEDIA" in scoring_result["priority"]

    async def test_default_priority_for_unclear(self):
        """Verificar prioridad por defecto para mensajes poco claros"""
        service = LeadsalesService()

        scoring_result = service._score_lead(
            "Hola buenos días",
            {}
        )

        # Debe asignar alguna prioridad por defecto
        assert "priority" in scoring_result
        assert len(scoring_result["priority"]) > 0


@pytest.mark.asyncio
class TestScoringWithAdditionalData:
    """Tests de scoring con datos adicionales del flujo"""

    async def test_libertador_approved_adds_tag(self):
        """Verificar que Libertador aprobado agrega tag"""
        service = LeadsalesService()

        scoring_result = service._score_lead(
            "Busco apartamento",
            {"tiene_solicitud_libertador": True}
        )

        assert "LIBERTADOR_APROBADO" in scoring_result["tags"]

    async def test_libertador_not_approved_no_tag(self):
        """Verificar que sin Libertador no se agrega tag"""
        service = LeadsalesService()

        scoring_result = service._score_lead(
            "Busco apartamento",
            {"tiene_solicitud_libertador": False}
        )

        assert "LIBERTADOR_APROBADO" not in scoring_result["tags"]

    async def test_additional_data_empty_dict(self):
        """Verificar scoring con additional_data vacío"""
        service = LeadsalesService()

        scoring_result = service._score_lead(
            "Busco casa para comprar",
            {}
        )

        # Debe funcionar correctamente sin additional_data
        assert "COMPRA" in scoring_result["tags"]
        assert "CASA" in scoring_result["tags"]
        assert scoring_result["quality_score"] > 0

    async def test_additional_data_none(self):
        """Verificar scoring con additional_data None"""
        service = LeadsalesService()

        scoring_result = service._score_lead(
            "Busco apartamento",
            None
        )

        # Debe manejar None correctamente (convertido a {} internamente)
        assert "quality_score" in scoring_result
        assert "tags" in scoring_result
        assert "APARTAMENTO" in scoring_result["tags"]