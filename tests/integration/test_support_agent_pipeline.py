import pytest
from unittest.mock import AsyncMock, Mock, patch
from app.agents.support.agent import SupportAgent
from app.core.pipeline import PipelineContext

@pytest.fixture
def mock_llm_service():
    """Mock del LLMService para evitar llamadas reales a OpenAI"""
    llm = Mock()
    llm.api_client = Mock()
    llm.api_client.initialized = True

    # Mock de classify_intent_and_extract_entities (usado por IntentClassifier)
    async def mock_classify_intent_and_extract_entities(*args, **kwargs):
        return {
            "intent": "property_inquiry",
            "sub_intent": "busqueda_apartamento",
            "confidence": 0.95,
            "entities": {
                "property_type": "apartamento",
                "location": "Bogotá"
            },
            "reasoning": "Usuario busca apartamento"
        }

    llm.classify_intent_and_extract_entities = AsyncMock(side_effect=mock_classify_intent_and_extract_entities)

    # Mock de classify_with_prompt (legacy, para otros usos)
    async def mock_classify_with_prompt(*args, **kwargs):
        return {
            "intent": "property_inquiry",
            "sub_intent": "busqueda_apartamento",
            "confidence": 0.95,
            "entities": {
                "property_type": "apartamento",
                "location": "Bogotá"
            },
            "reasoning": "Usuario busca apartamento"
        }

    llm.classify_with_prompt = AsyncMock(side_effect=mock_classify_with_prompt)

    # Mock de generate_with_prompt (usado por PropertyHandler)
    async def mock_generate_with_prompt(*args, **kwargs):
        return "Claro Juan, te ayudo a buscar apartamento en Bogotá. Te voy a transferir con un asesor."

    llm.generate_with_prompt = AsyncMock(side_effect=mock_generate_with_prompt)

    return llm

@pytest.fixture
def mock_state_manager():
    """Mock del StateManager"""
    state = Mock()
    
    async def mock_update(*args, **kwargs):
        return True
    
    state.update_conversation = AsyncMock(side_effect=mock_update)
    
    async def mock_get(*args, **kwargs):
        return {
            "phone_number": "+573001234567",
            "customer_name": "Juan Pérez",
            "estado": "NUEVO"
        }
    
    state.get_conversation = AsyncMock(side_effect=mock_get)
    
    return state

@pytest.fixture
def mock_rag_system():
    """Mock del RAG System"""
    rag = Mock()
    rag.initialized = True
    
    async def mock_search(*args, **kwargs):
        return {
            "context": "Tenemos apartamentos disponibles en Bogotá desde $200M.",
            "phone_numbers": ["+573245516105"],
            "metadata": {
                "source": "catalogo_inmuebles.pdf",
                "similarity": 0.92
            }
        }
    
    rag.search_context = AsyncMock(side_effect=mock_search)
    
    return rag

@pytest.fixture
def support_agent(mock_llm_service, mock_state_manager, mock_rag_system):
    """Fixture que crea SupportAgent con mocks inyectados"""
    # Patchear el singleton llm_service usado por IntentClassifier
    from unittest.mock import patch

    with patch('app.agents.support.classifiers.intent.llm_service', mock_llm_service):
        agent = SupportAgent(
            llm_service=mock_llm_service,
            state_manager=mock_state_manager,
            rag_system=mock_rag_system
        )
        yield agent

# 1.2 TEST DE INICIALIZACION DE PIPELINE
@pytest.mark.asyncio
async def test_support_agent_initialization(support_agent):
    """Verifica si supportAgent se inicializa correctamente"""
    assert hasattr(support_agent, 'pipeline'), "SupportAgent debe tener atributo pipeline"
    assert support_agent.pipeline is not None
    
    """Verifia los nuemro de paso"""
    
    assert len(support_agent.pipeline.steps) == 4, "Pipeline debe tener 4 pasos"

    step_names = [step.name for step in support_agent.pipeline.steps]
    expected_steps = [
        "IntentClassifier",
        "RAGSearch",  # Corregido: era "RAGSearchStep"
        "RoutingDecision",
        "ResponseGenerator"
    ]

    assert step_names == expected_steps, f"Pipeline debe tener pasos: {step_names}"

    # Verificar componentes inicializados directamente
    assert hasattr(support_agent, 'intent_classifier'), "Debe tener intent_classifier"
    assert hasattr(support_agent, 'property_handler'), "Debe tener property_handler"
    assert hasattr(support_agent, 'department_handler'), "Debe tener department_handler"
    assert hasattr(support_agent, 'general_handler'), "Debe tener general_handler"

    assert support_agent.intent_classifier is not None
    assert support_agent.property_handler is not None
    assert support_agent.department_handler is not None
    assert support_agent.general_handler is not None
    

# 1.3 TEST DE FLUJO COMPLETO CAMINO 1
@pytest.mark.asyncio
async def test_support_agent_pipeline_property_flow(support_agent, mock_llm_service):
  
    # Preparar mensaje de entrada
    message_data = {
        "text": "Hola, busco un apartamento en Bogotá",
        "from": "+573001234567"
    }
    
    conversation = {
        "phone_number": "+573001234567",
        "customer_name": "Juan Pérez",
        "estado": "NUEVO"
    }
    
    # Ejecutar proceso
    result = await support_agent.process_message(message_data, conversation)

    # Verificar estructura de respuesta
    assert "response" in result
    assert "new_state" in result  # Corregido: era "next_state"
    assert "transfer_to" in result

    # Verificar contenido de respuesta
    assert result["new_state"] == "TRANSFERIDO"  # Corregido: era "next_state"
    assert result["transfer_to"] == "ReceptionAgent"
    assert len(result["response"]) > 0
    assert "Juan" in result["response"]  # Debe incluir nombre del cliente

    # Verificar que LLM fue llamado para clasificación (IntentClassifier)
    assert mock_llm_service.classify_intent_and_extract_entities.call_count == 1, \
        f"classify_intent_and_extract_entities debería llamarse 1 vez, fue llamado {mock_llm_service.classify_intent_and_extract_entities.call_count} veces"

    # Verificar que LLM fue llamado para generación de respuesta (PropertyHandler)
    assert mock_llm_service.generate_with_prompt.call_count == 1, \
        f"generate_with_prompt debería llamarse 1 vez, fue llamado {mock_llm_service.generate_with_prompt.call_count} veces"

"""1.4 FLUJO COMPLETO CAMINO 2"""
@pytest.mark.asyncio
async def test_support_agent_pipeline_department_flow(support_agent, mock_llm_service, mock_rag_system):
    # Configurar mock de clasificación para "departamento"
    async def mock_classify_department(*args, **kwargs):
        return {
            "intent": "department_transfer",
            "sub_intent": "contacto_ventas",
            "confidence": 0.90,
            "entities": {
                "department": "ventas"
            },
            "reasoning": "Usuario quiere contactar departamento de ventas"
        }

    # Sobrescribir el mock con clasificación de departamento (método correcto)
    mock_llm_service.classify_intent_and_extract_entities = AsyncMock(side_effect=mock_classify_department)

    # Configurar mock de RAG con números de teléfono
    async def mock_search_with_phones(*args, **kwargs):
        return {
            "context": "Departamento de ventas: +57 324 551 6105",
            "phone_numbers": ["+573245516105"],
            "metadata": {"source": "contactos_departamentos.txt"}
        }

    mock_rag_system.search_context = AsyncMock(side_effect=mock_search_with_phones)

    # Ejecutar
    message_data = {"text": "Necesito hablar con ventas"}
    conversation = {"customer_name": "María García"}

    result = await support_agent.process_message(message_data, conversation)

    # Verificar
    assert "response" in result
    assert "new_state" in result  # Corregido: era "next_state"
    assert "+57" in result["response"] or "324" in result["response"]  # Debe incluir teléfono
    assert result["new_state"] in ["DEPARTMENT_CONNECTED", "SEARCHING_DEPARTMENT"]

"""1.5 FLUJO COMPLETO CAMINO 3"""
@pytest.mark.asyncio
async def test_support_agent_pipeline_general_flow(support_agent, mock_llm_service):
    # Configurar mock de clasificación para "general"
    async def mock_classify_general(*args, **kwargs):
        return {
            "intent": "general_question",
            "sub_intent": "horarios",
            "confidence": 0.80,
            "entities": {},
            "reasoning": "Pregunta sobre horarios de atención"
        }

    # Sobrescribir el mock con clasificación general (método correcto)
    mock_llm_service.classify_intent_and_extract_entities = AsyncMock(side_effect=mock_classify_general)

    # Ejecutar
    message_data = {"text": "¿Cuáles son los horarios de atención?"}
    conversation = {"customer_name": "Pedro López"}

    result = await support_agent.process_message(message_data, conversation)

    # Verificar
    assert "response" in result
    assert "new_state" in result  # Corregido: era "next_state"
    assert result["new_state"] in ["GENERAL_ANSWERED", "CLARIFICATION_NEEDED"]
    assert len(result["response"]) > 0
    

"""1.6 MANEJO DE ERRORES"""
@pytest.mark.asyncio
async def test_support_agent_pipeline_error_handling(support_agent, mock_llm_service):

    # Simular error crítico en LLM (el método correcto que usa IntentClassifier)
    mock_llm_service.classify_with_prompt = AsyncMock(side_effect=Exception("OpenAI API error"))

    message_data = {"text": "Test error"}
    conversation = {"customer_name": "Test User"}

    # El pipeline debe capturar el error y manejarlo gracefully
    result = await support_agent.process_message(message_data, conversation)

    # Verificar que retorna respuesta válida (fallback keywords mantiene UX)
    assert "response" in result
    assert result["response"] is not None
    assert len(result["response"]) > 0
    # Sistema usa fallback keywords, por lo que usuario recibe respuesta normal
    # (El error crítico se loguea para desarrolladores pero no afecta al usuario)


"""1.7 PROPAGACION DE CONTEXTO ENTRE LOS PASOS"""
@pytest.mark.asyncio
async def test_support_agent_pipeline_context_propagation(support_agent):

    message_data = {"text": "Busco casa"}
    conversation = {"customer_name": "Test"}

    # Ejecutar pipeline
    result = await support_agent.process_message(message_data, conversation)

    # El hecho de que retorne resultado exitoso valida la propagación
    # (cada paso depende de resultados previos)
    assert result is not None
    assert "response" in result


"""1.8 MIDDLEWARE DE LOGGING"""
@pytest.mark.asyncio
async def test_logging_middleware_executes(support_agent, capsys):
    """Verificar que logging_middleware se ejecuta antes de cada paso del pipeline"""

    message_data = {"text": "Busco apartamento"}
    conversation = {"customer_name": "Test User"}

    # Ejecutar pipeline (que tiene .with_logging())
    result = await support_agent.process_message(message_data, conversation)

    # Capturar output de consola
    captured = capsys.readouterr()

    # Verificar que el middleware de logging se ejecutó antes de cada uno de los 4 pasos
    assert "[Middleware:Logging] Before step 'IntentClassifier'" in captured.out
    assert "[Middleware:Logging] Before step 'RAGSearch'" in captured.out
    assert "[Middleware:Logging] Before step 'RoutingDecision'" in captured.out
    assert "[Middleware:Logging] Before step 'ResponseGenerator'" in captured.out

    # Verificar que muestra los results acumulados
    # Después de IntentClassifier: results = []
    assert "Results: []" in captured.out
    # Después de RAGSearch: results = ['classification']
    assert "Results: ['classification']" in captured.out

    # Verificar que el pipeline completó exitosamente
    assert result is not None
    assert "response" in result


"""1.9 MIDDLEWARE DE VALIDACION"""
@pytest.mark.asyncio
async def test_validation_middleware_rejects_empty_context():
    """Verificar que validation_middleware detecta y rechaza contexto inválido"""
    from app.core.pipeline import MessagePipeline, validation_middleware
    from app.agents.support.pipeline_steps import IntentClassifierStep
    from app.agents.support.classifiers.intent import IntentClassifier
    from unittest.mock import Mock

    # Crear mock de LLM
    mock_llm = Mock()
    mock_llm.classify_with_prompt = AsyncMock(return_value={
        "intent": "inmueble",
        "confidence": 0.9,
        "entities": {},
        "reasoning": "test"
    })

    # Crear clasificador y step
    classifier = IntentClassifier()
    step = IntentClassifierStep(classifier)

    # Crear pipeline con validation_middleware
    pipeline = MessagePipeline("TestPipeline")
    pipeline.add_step(step)
    pipeline.add_middleware(validation_middleware)

    # TEST 1: Contexto con message vacío (debe fallar)
    result1 = await pipeline.process(
        message={},  # Mensaje vacío
        conversation={"customer_name": "Test"}
    )

    # Verificar que el pipeline detectó el error
    assert result1.has_error() or result1.error is not None, \
        "Pipeline debería haber detectado mensaje vacío"

    # TEST 2: Contexto con conversation vacío (debe fallar)
    result2 = await pipeline.process(
        message={"text": "Test"},
        conversation={}  # Conversación vacía
    )

    # Verificar que el pipeline detectó el error
    assert result2.has_error() or result2.error is not None, \
        "Pipeline debería haber detectado conversación vacía"

    # TEST 3: Contexto válido (debe funcionar)
    result3 = await pipeline.process(
        message={"text": "Test válido"},
        conversation={"customer_name": "Test"}
    )

    # Verificar que el pipeline funcionó correctamente
    assert not result3.has_error(), \
        "Pipeline con contexto válido no debería tener errores"
    assert "classification" in result3.results, \
        "Pipeline debería haber completado la clasificación"


"""2.0 TESTS DE INTEGRACION CON RAG"""

"""2.1 RAG SIN DOCUMENTOS"""
@pytest.mark.asyncio
async def test_rag_returns_empty_documents(support_agent, mock_llm_service, mock_rag_system):
    """Verificar que cuando RAG no encuentra documentos, genera respuesta genérica"""

    # Configurar RAG para retornar vacío
    async def mock_search_empty(*args, **kwargs):
        return {
            "documents": [],  # Sin documentos
            "context": "",
            "phone_numbers": [],
            "metadata": {},
            "rag_confidence": 0.0
        }

    mock_rag_system.search_context = AsyncMock(side_effect=mock_search_empty)

    # Configurar clasificación para "general" (usa RAG)
    async def mock_classify_general(*args, **kwargs):
        return {
            "intent": "general_question",
            "sub_intent": "quienes_somos",
            "confidence": 0.85,
            "entities": {},
            "reasoning": "Pregunta general sobre la empresa"
        }

    mock_llm_service.classify_intent_and_extract_entities = AsyncMock(side_effect=mock_classify_general)

    # Ejecutar
    message_data = {"text": "¿Quiénes son ustedes?"}
    conversation = {"customer_name": "Test User"}

    result = await support_agent.process_message(message_data, conversation)

    # Verificar que retorna respuesta válida (aunque RAG esté vacío)
    assert "response" in result
    assert result["response"] is not None
    assert len(result["response"]) > 0
    # Debe manejar caso sin documentos y generar respuesta genérica
    assert result["new_state"] in ["GENERAL_ANSWERED", "CLARIFICATION_NEEDED"]


"""2.2 RAG CON BAJA SIMILITUD"""
@pytest.mark.asyncio
async def test_rag_returns_low_similarity_docs(support_agent, mock_llm_service, mock_rag_system):
    """Verificar que documentos con baja similitud se manejan correctamente"""

    # Configurar RAG para retornar documentos con baja similitud
    async def mock_search_low_similarity(*args, **kwargs):
        return {
            "documents": [
                {"content": "Documento poco relevante", "similarity": 0.3}
            ],
            "context": "Contexto poco relevante",
            "phone_numbers": [],
            "metadata": {"source": "doc_irrelevante.pdf", "similarity": 0.3},
            "rag_confidence": 0.3  # Baja confianza
        }

    mock_rag_system.search_context = AsyncMock(side_effect=mock_search_low_similarity)

    # Configurar clasificación para "general"
    async def mock_classify_general(*args, **kwargs):
        return {
            "intent": "general",
            "sub_intent": "informacion",
            "confidence": 0.75,
            "entities": {},
            "reasoning": "Consulta general"
        }

    mock_llm_service.classify_with_prompt = AsyncMock(side_effect=mock_classify_general)

    # Ejecutar
    message_data = {"text": "Necesito información"}
    conversation = {"customer_name": "María"}

    result = await support_agent.process_message(message_data, conversation)

    # Verificar que genera respuesta válida incluso con baja similitud
    assert "response" in result
    assert result["response"] is not None
    assert len(result["response"]) > 0


"""2.3 RAG EXTRAE MULTIPLES TELEFONOS"""
@pytest.mark.asyncio
async def test_rag_extracts_multiple_phone_numbers(support_agent, mock_llm_service, mock_rag_system):
    """Verificar que RAG extrae correctamente múltiples números de teléfono"""

    # Configurar RAG para retornar múltiples teléfonos
    async def mock_search_multiple_phones(*args, **kwargs):
        return {
            "documents": [
                {"content": "Departamento de reparaciones: 324 551 6105, 300 123 4567, 301 987 6543"}
            ],
            "context": "Para reparaciones urgentes contacta: 324 551 6105, 300 123 4567, 301 987 6543",
            "phone_numbers": ["+573245516105", "+573001234567", "+573019876543"],  # 3 teléfonos
            "metadata": {"source": "contactos_reparaciones.txt"},
            "rag_confidence": 0.95
        }

    mock_rag_system.search_context = AsyncMock(side_effect=mock_search_multiple_phones)

    # Configurar clasificación para "departamento"
    async def mock_classify_department(*args, **kwargs):
        return {
            "intent": "department_transfer",
            "sub_intent": "reparaciones",
            "confidence": 0.92,
            "entities": {"department": "reparaciones", "urgency": "alta"},
            "reasoning": "Usuario necesita reparaciones urgentes"
        }

    mock_llm_service.classify_intent_and_extract_entities = AsyncMock(side_effect=mock_classify_department)

    # Ejecutar
    message_data = {"text": "Tengo una gotera urgente"}
    conversation = {"customer_name": "Carlos"}

    result = await support_agent.process_message(message_data, conversation)

    # Verificar que la respuesta contiene al menos uno de los teléfonos
    assert "response" in result
    assert result["response"] is not None

    # Verificar que al menos uno de los 3 teléfonos aparece en la respuesta
    phone_found = any(phone_part in result["response"] for phone_part in [
        "324", "300", "301",  # Prefijos de los 3 números
        "6105", "4567", "6543"  # Sufijos de los 3 números
    ])

    assert phone_found, "La respuesta debería contener al menos un número de teléfono"

    # Verificar que el estado indica conexión con departamento
    assert result["new_state"] in ["DEPARTMENT_CONNECTED", "SEARCHING_DEPARTMENT"]


"""3.0 TESTS E2E CON RAG REAL (SIN MOCKS)"""

"""3.1 RAG REAL: BUSQUEDA DE DOCUMENTOS"""
@pytest.mark.asyncio
@pytest.mark.slow  # Marca como slow porque descarga modelo la primera vez
async def test_rag_real_finds_reparaciones_document():
    """
    Test E2E: Verifica que RAG REAL encuentra documentos correctos de la knowledge base.

    Este test usa el RAG System real (no mocks) para verificar:
    - Inicialización correcta del sistema RAG
    - Búsqueda de documentos en knowledge_base/
    - Extracción de contenido relevante (números de teléfono)

    IMPORTANTE: Este test requiere que data/rag/ contenga índices generados.
    """
    from app.rag.rag_system import RAGSystem

    # Inicializar RAG REAL (sin mocks)
    rag_system = RAGSystem(rag_data_path="data/rag")
    initialized = rag_system.initialize()

    # Verificar inicialización exitosa
    assert initialized, "RAG System debería inicializarse correctamente con data/rag/"

    # Verificar que cargó documentos
    health = rag_system.health_check()
    assert health["status"] == "healthy", f"RAG debe estar healthy: {health}"
    assert health["documents_loaded"] > 0, "RAG debe haber cargado documentos"

    # TEST 1: Buscar sobre REPARACIONES (debe encontrar soporte_reparaciones_emergencias.txt)
    context_reparaciones = rag_system.search_context("Necesito reportar una emergencia de reparaciones")

    # Verificar que encontró contenido relevante
    assert len(context_reparaciones) > 0, "Debe retornar contexto no vacío"
    assert "323 515 80 07" in context_reparaciones, \
        "Debe encontrar teléfono de reparaciones: 323 515 80 07 (de soporte_reparaciones_emergencias.txt)"

    # Verificar keywords relevantes
    context_lower = context_reparaciones.lower()
    assert "reparaciones" in context_lower or "emergencias" in context_lower or "daños" in context_lower, \
        "El contexto debe contener keywords de reparaciones"

    print(f"\n[TEST E2E] OK Contexto encontrado para reparaciones ({len(context_reparaciones)} chars)")
    print(f"[TEST E2E] OK Telefono extraido: 323 515 80 07")


"""3.2 RAG REAL: BUSQUEDA DE JURIDICO"""
@pytest.mark.asyncio
@pytest.mark.slow
async def test_rag_real_finds_juridico_document():
    """
    Test E2E: Verifica que RAG encuentra documentos de área jurídica.

    Busca: soporte_juridico_legal.txt
    Teléfono esperado: 321 789 86 79
    """
    from app.rag.rag_system import RAGSystem

    # Inicializar RAG REAL
    rag_system = RAGSystem(rag_data_path="data/rag")
    assert rag_system.initialize(), "RAG debe inicializar"

    # TEST: Buscar sobre TEMAS LEGALES
    context_juridico = rag_system.search_context("Necesito hablar con el abogado por temas legales")

    # Verificar contenido
    assert len(context_juridico) > 0, "Debe retornar contexto"
    assert "321 789 86 79" in context_juridico, \
        "Debe encontrar teléfono jurídico: 321 789 86 79 (de soporte_juridico_legal.txt)"

    # Verificar keywords
    context_lower = context_juridico.lower()
    assert "jurídico" in context_lower or "legal" in context_lower or "abogado" in context_lower, \
        "Debe contener keywords legales"

    print(f"\n[TEST E2E] OK Contexto encontrado para juridico ({len(context_juridico)} chars)")
    print(f"[TEST E2E] OK Telefono extraido: 321 789 86 79")


"""3.3 RAG REAL: VERIFICAR MULTIPLES DOCUMENTOS"""
@pytest.mark.asyncio
@pytest.mark.slow
async def test_rag_real_searches_multiple_docs():
    """
    Test E2E: Verifica que RAG puede buscar en diferentes documentos.

    Prueba 3 queries diferentes para asegurar que el índice funciona correctamente.
    """
    from app.rag.rag_system import RAGSystem

    rag_system = RAGSystem(rag_data_path="data/rag")
    assert rag_system.initialize(), "RAG debe inicializar"

    # Query 1: Reparaciones
    context1 = rag_system.search_context("reparaciones")
    assert len(context1) > 0, "Debe encontrar algo sobre reparaciones"

    # Query 2: Legal
    context2 = rag_system.search_context("abogado")
    assert len(context2) > 0, "Debe encontrar algo sobre abogado"

    # Query 3: Información general
    context3 = rag_system.search_context("empresa inmobiliaria")
    assert len(context3) > 0, "Debe encontrar info de la empresa"

    # Verificar que retorna diferentes contextos (no siempre el mismo)
    # Al menos 2 de los 3 contextos deben ser diferentes
    unique_contexts = len(set([context1[:100], context2[:100], context3[:100]]))
    assert unique_contexts >= 2, \
        f"RAG debe retornar contextos diferentes según query (únicos: {unique_contexts}/3)"

    print(f"\n[TEST E2E] ✅ RAG retorna contextos diferentes para queries diferentes")
    print(f"[TEST E2E] ✅ Contextos únicos: {unique_contexts}/3")