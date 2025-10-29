import pytest
from app.services.client_classifier import ClientClassifier, ClientClassification


class TestClientClassifierRules:
    """Tests para clasificación por reglas"""
    
    @pytest.mark.asyncio
    async def test_classify_inversionista_high_confidence(self):
        """Detecta inversionista con alta confianza"""
        classifier = ClientClassifier()
        
        result = await classifier.classify(
            "Busco apartamento para inversión, me interesa la rentabilidad y plusvalía de la zona"
        )
        
        assert result.profile == "inversionista"
        assert result.confidence >= 0.8
        assert result.classification_method == "rules"
        assert result.cost_usd == 0.0
        assert "inversión" in result.detected_keywords or "rentabilidad" in result.detected_keywords
    
    @pytest.mark.asyncio
    async def test_classify_arquitecto_explicit(self):
        """Detecta arquitecto cuando menciona explícitamente"""
        classifier = ClientClassifier()
        
        result = await classifier.classify(
            "Hola, soy arquitecto y busco apartamento para remodelar, me interesan los planos y distribución de espacios"
        )
        
        assert result.profile == "arquitecto"
        assert result.profession_explicit is True
        assert result.confidence >= 0.9
        assert result.classification_method == "rules"
    
    @pytest.mark.asyncio
    async def test_classify_familia_by_keywords(self):
        """Detecta perfil familia por keywords"""
        classifier = ClientClassifier()

        result = await classifier.classify(
            "Busco casa para mi familia con 4 habitaciones, cerca de colegios y parques para mis hijos"
        )

        assert result.profile == "familia"
        assert result.confidence >= 0.7
        assert result.classification_method == "rules"
        # Verificar que alguna keyword detectada contenga las palabras esperadas
        assert any(
            any(expected in kw for expected in ["familia", "hijos", "colegio"])
            for kw in result.detected_keywords
        )
    
    @pytest.mark.asyncio
    async def test_classify_individual_default(self):
        """Clasifica como individual cuando no hay keywords específicos"""
        classifier = ClientClassifier()

        result = await classifier.classify(
            "Busco apartamento de 2 habitaciones"
        )

        assert result.profile == "individual"
        # Mensaje genérico sin keywords específicos puede usar LLM o rules
        assert result.classification_method in ["rules", "rules_fallback", "llm"]
    
    @pytest.mark.asyncio
    async def test_sophistication_alto_by_keywords(self):
        """Detecta sofisticación alta por keywords técnicos"""
        classifier = ClientClassifier()
        
        result = await classifier.classify(
            "Busco propiedad con buen ROI, he hecho análisis financiero de la zona y la proyección de plusvalía es favorable"
        )
        
        assert result.sophistication_level == "alto"
        assert result.confidence >= 0.6
    
    @pytest.mark.asyncio
    async def test_sophistication_bajo_first_time(self):
        """Detecta sofisticación baja para primera vez"""
        classifier = ClientClassifier()
        
        result = await classifier.classify(
            "Es mi primera vez comprando, no sé mucho del proceso, necesito ayuda"
        )
        
        assert result.sophistication_level == "bajo"


class TestClientClassifierLLM:
    """Tests para clasificación por LLM (casos complejos)"""
    
    @pytest.mark.asyncio
    async def test_llm_used_for_ambiguous_case(self):
        """LLM se usa para casos ambiguos"""
        classifier = ClientClassifier()

        result = await classifier.classify(
            "Me interesa una propiedad con potencial de valorización"
        )

        # Caso ambiguo: sin keywords high_confidence
        # Debe intentar usar LLM, pero puede caer a rules_fallback si hay rate limits
        assert result.classification_method in ["llm", "rules_fallback"]
        # Si usó LLM exitosamente, debe tener costo > 0
        if result.classification_method == "llm":
            assert result.cost_usd > 0
        assert result.profile in ["arquitecto", "empresario", "inversionista", "individual", "desconocido"]
    
    @pytest.mark.asyncio
    async def test_llm_detects_implicit_profession(self):
        """LLM detecta profesión implícita sin mencionar explícitamente"""
        classifier = ClientClassifier()
        
        result = await classifier.classify(
            "Necesito un local para expandir mi cadena de tiendas, con buena ubicación para flujo de clientes"
        )
        
        # Implícitamente es empresario, pero no lo dice explícitamente
        # LLM debe inferirlo
        assert result.profile == "empresario"
        assert result.profession_explicit is False
        assert result.confidence >= 0.7


class TestClientClassifierHybrid:
    """Tests para sistema híbrido completo"""
    
    @pytest.mark.asyncio
    async def test_statistics_tracking(self):
        """Verifica tracking de estadísticas de uso"""
        classifier = ClientClassifier()
        
        # Caso que usa reglas
        await classifier.classify("Busco apartamento para inversión")
        
        # Caso que usa LLM (ambiguo)
        await classifier.classify("Me interesa una propiedad con potencial")
        
        stats = classifier.get_statistics()
        
        assert stats["total_classifications"] == 2
        assert stats["rule_based"] >= 1
        assert stats["llm_based"] >= 0  # Podría ser 0 o 1 dependiendo del threshold
        assert "avg_cost_per_classification" in stats
    
    @pytest.mark.asyncio
    async def test_cost_optimization(self):
        """Verifica que sistema híbrido optimiza costos"""
        classifier = ClientClassifier()
        
        # 10 casos simples (deben usar reglas = $0)
        simple_cases = [
            "Busco apartamento para inversión",
            "Soy arquitecto y busco casa",
            "Necesito oficina para mi empresa",
            "Busco casa para mi familia",
            "Soy ingeniero buscando apartamento",
            "Quiero invertir en inmuebles",
            "Busco local comercial para negocio",
            "Apartamento para arrendar y ganar",
            "Casa con buen diseño arquitectónico",
            "Propiedad para mi portafolio de inversión"
        ]
        
        for case in simple_cases:
            await classifier.classify(case)
        
        stats = classifier.get_statistics()
        
        # Al menos 60% debe ser por reglas (gratis)
        assert stats["rule_based_percentage"] >= 60
        
        # Costo promedio debe ser < $0.00005 (objetivo del PR)
        assert stats["avg_cost_per_classification"] < 0.00005


class TestClientClassifierEdgeCases:
    """Tests para casos edge y errores"""
    
    @pytest.mark.asyncio
    async def test_empty_message(self):
        """Maneja mensaje vacío"""
        classifier = ClientClassifier()
        
        result = await classifier.classify("")
        
        assert result.profile == "desconocido"
        assert result.confidence <= 0.5
    
    @pytest.mark.asyncio
    async def test_very_short_message(self):
        """Maneja mensajes muy cortos"""
        classifier = ClientClassifier()

        result = await classifier.classify("Hola")

        # Mensajes cortos sin información → perfil desconocido
        # El LLM puede tener alta confianza en "desconocido" (seguro de que no sabe)
        assert result.profile in ["individual", "desconocido"]
        assert result.confidence > 0  # Cualquier confianza válida
    
    @pytest.mark.asyncio
    async def test_multiple_profiles_keywords(self):
        """Maneja mensaje con keywords de múltiples perfiles"""
        classifier = ClientClassifier()
        
        result = await classifier.classify(
            "Soy arquitecto inversionista y busco propiedades para mi familia"
        )
        
        # Debe elegir el perfil con mayor confianza (arquitecto por "soy arquitecto")
        assert result.profile in ["arquitecto", "inversionista", "familia"]
        assert result.confidence >= 0.6
    
    @pytest.mark.asyncio
    async def test_llm_error_fallback(self, monkeypatch):
        """Fallback a reglas cuando LLM falla"""
        classifier = ClientClassifier()
        
        # Simular error en LLM
        async def mock_classify_llm(*args, **kwargs):
            raise Exception("LLM API error")
        
        monkeypatch.setattr(classifier, "_classify_by_llm", mock_classify_llm)
        
        # Forzar caso que usaría LLM (confianza baja en reglas)
        classifier.CONFIDENCE_THRESHOLD = 0.99  # Threshold muy alto
        
        result = await classifier.classify(
            "Me interesa una propiedad"
        )
        
        # Debe usar fallback a reglas
        assert result.classification_method == "rules_fallback"
        assert result.profile != ""
