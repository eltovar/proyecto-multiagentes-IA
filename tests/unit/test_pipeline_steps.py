'''Test unitarios para pipeline_steps.py. '''

import pytest
from unittest.mock import Mock, AsyncMock
from app.agents.support.pipeline_steps import (
    IntentClassifierStep,
    RAGSearchStep,
    RoutingDecisionStep,
    ResponseGeneratorStep
)

from app.core.pipeline import PipelineContext

#Fixtures para mocks

@pytest.fixture
def mock_context():
    """Contexto base para tests"""
    return PipelineContext(
        message={"text": "Busco apartamento"},
        conversation={"customer_name": "Juan"},
        metadata={}
    )

@pytest.fixture
def mock_classifier():
    """Mock de IntentClassifier"""
    classifier = Mock()
    classifier.classify = AsyncMock(return_value=Mock(
        intent="inmueble",
        sub_intent="busqueda",
        confidence=0.95,
        entities={"property_type": "apartamento"},
        reasoning="Búsqueda de inmueble"
    ))
    return classifier

#Test 1. InterntClassigierStep

class TestIntentClassifierStep:
    """Tests para IntentClassifierStep"""
    
    @pytest.mark.asyncio
    async def test_classify_simple_message(self, mock_classifier, mock_context):
        """Test: Clasifica mensaje simple correctamente"""
        step = IntentClassifierStep(mock_classifier)
        result_context = await step.execute(mock_context)
        
        # Verificar que guardó resultado
        assert "classification" in result_context.results
        classification = result_context.get_result("classification")
        assert classification["intent"] == "inmueble"
        assert classification["confidence"] == 0.95
    
    @pytest.mark.asyncio
    async def test_classify_whatsapp_format(self, mock_classifier):
        """Test: Maneja formato WhatsApp (texto anidado)"""
        context = PipelineContext(
            message={"text": {"body": "Busco casa"}},  # ← Formato WhatsApp
            conversation={},
            metadata={}
        )
        
        step = IntentClassifierStep(mock_classifier)
        result = await step.execute(context)
        
        # Verificar que extrajo el texto correctamente
        mock_classifier.classify.assert_called_once()
        call_args = mock_classifier.classify.call_args
        assert call_args.kwargs["message"] == "Busco casa"
    
    @pytest.mark.asyncio
    async def test_classify_empty_message(self, mock_classifier):
        """Test: Maneja mensaje vacío sin fallar"""
        context = PipelineContext(
            message={"text": ""},
            conversation={},
            metadata={}
        )
        
        step = IntentClassifierStep(mock_classifier)
        result = await step.execute(context)
        
        # Debe ejecutar sin error
        assert "classification" in result.results

#Test 2 RAGSearchStep

class TestRAGSearchStep:
    """Tests para RAGSearchStep"""
    
    @pytest.mark.asyncio
    async def test_search_with_valid_rag(self, mock_context):
        """Test: Busca en RAG correctamente"""
        mock_rag = Mock()
        mock_rag.search_context = AsyncMock(return_value={
            "documents": [{"content": "Doc1"}],
            "context": "Contexto relevante",
            "phone_numbers": ["321 123 4567"],
            "rag_confidence": 0.9
        })
        
        step = RAGSearchStep(mock_rag)
        result = await step.execute(mock_context)
        
        # Verificar resultado
        rag_result = result.get_result("rag_result")
        assert len(rag_result["documents"]) == 1
        assert "321 123 4567" in rag_result["phone_numbers"]
    
    @pytest.mark.asyncio
    async def test_search_with_no_rag(self, mock_context):
        """Test: Sin RAG, retorna resultado vacío"""
        step = RAGSearchStep(rag_system=None)
        result = await step.execute(mock_context)
        
        rag_result = result.get_result("rag_result")
        assert rag_result["documents"] == []
        assert rag_result["context"] == ""
        assert rag_result["phone_numbers"] == []
    
    @pytest.mark.asyncio
    async def test_search_handles_rag_error(self, mock_context):
        """Test: Maneja error de RAG gracefully"""
        mock_rag = Mock()
        mock_rag.search_context = AsyncMock(side_effect=Exception("RAG error"))
        
        step = RAGSearchStep(mock_rag)
        result = await step.execute(mock_context)
        
        # Debe retornar resultado vacío (no fallar)
        rag_result = result.get_result("rag_result")
        assert rag_result["documents"] == []


#Test 3 RoutingDecisionStep

class TestRoutingDecisionStep:
    """Tests para RoutingDecisionStep"""
    
    @pytest.mark.asyncio
    async def test_route_inmueble_to_property(self):
        """Test: inmueble → property"""
        context = PipelineContext(
            message={}, conversation={}, metadata={}
        )
        context.set_result("classification", {"intent": "inmueble"})
        
        step = RoutingDecisionStep()
        result = await step.execute(context)
        
        assert result.get_result("routing_path") == "property"
    
    @pytest.mark.asyncio
    async def test_route_departamento_to_department(self):
        """Test: departamento → department"""
        context = PipelineContext(
            message={}, conversation={}, metadata={}
        )
        context.set_result("classification", {"intent": "departamento"})
        
        step = RoutingDecisionStep()
        result = await step.execute(context)
        
        assert result.get_result("routing_path") == "department"
    
    @pytest.mark.asyncio
    async def test_route_unclear_to_general(self):
        """Test: unclear → general (fallback)"""
        context = PipelineContext(
            message={}, conversation={}, metadata={}
        )
        context.set_result("classification", {"intent": "unclear"})
        
        step = RoutingDecisionStep()
        result = await step.execute(context)
        
        assert result.get_result("routing_path") == "general"
    
    @pytest.mark.asyncio
    async def test_route_no_classification_defaults_to_general(self):
        """Test: Sin classification → general"""
        context = PipelineContext(
            message={}, conversation={}, metadata={}
        )
        # NO establecemos classification
        
        step = RoutingDecisionStep()
        result = await step.execute(context)
        
        assert result.get_result("routing_path") == "general"

#Test 4 ResponseGeneratorStep

class TestResponseGeneratorStep:
    """Tests para ResponseGeneratorStep"""
    
    @pytest.fixture
    def mock_handlers(self):
        """Mocks de los 3 handlers"""
        property_handler = Mock()
        property_handler.handle_property_request = AsyncMock(return_value=Mock(
            response="Busco apartamento response",
            next_state="TRANSFERIDO",
            transfer_to="ReceptionAgent",
            data_updates={}
        ))
        
        department_handler = Mock()
        department_handler.handle_department_request = AsyncMock(return_value=Mock(
            response="Contacto departamento",
            next_state="DEPARTMENT_CONNECTED",
            department="reparaciones",
            contact_info={"phone": "321 123 4567"}
        ))
        
        general_handler = Mock()
        general_handler.handle_general_query = AsyncMock(return_value=Mock(
            response="Respuesta general",
            next_state="GENERAL_ANSWERED",
            clarification_needed=False
        ))
        
        return property_handler, department_handler, general_handler
    
    @pytest.mark.asyncio
    async def test_generate_property_response(self, mock_handlers):
        """Test: Genera respuesta para property path"""
        property_h, dept_h, gen_h = mock_handlers
        
        context = PipelineContext(
            message={}, 
            conversation={"customer_name": "Juan"}, 
            metadata={}
        )
        context.set_result("routing_path", "property")
        context.set_result("classification", {"intent": "inmueble"})
        context.set_result("rag_result", {})
        
        step = ResponseGeneratorStep(property_h, dept_h, gen_h)
        result = await step.execute(context)
        
        # Verificar que llamó al property handler
        property_h.handle_property_request.assert_called_once()
        
        # Verificar respuesta
        final_response = result.get_result("final_response")
        assert "response" in final_response
        assert final_response["transfer_to"] == "ReceptionAgent"
    
    @pytest.mark.asyncio
    async def test_generate_department_response(self, mock_handlers):
        """Test: Genera respuesta para department path"""
        property_h, dept_h, gen_h = mock_handlers
        
        context = PipelineContext(
            message={}, conversation={}, metadata={}
        )
        context.set_result("routing_path", "department")
        context.set_result("classification", {})
        context.set_result("rag_result", {})
        
        step = ResponseGeneratorStep(property_h, dept_h, gen_h)
        result = await step.execute(context)
        
        # Verificar que llamó al department handler
        dept_h.handle_department_request.assert_called_once()
        
        final_response = result.get_result("final_response")
        assert final_response["department"] == "reparaciones"
    
    @pytest.mark.asyncio
    async def test_generate_handles_handler_error(self, mock_handlers):
        """Test: Maneja error del handler"""
        property_h, dept_h, gen_h = mock_handlers
        property_h.handle_property_request = AsyncMock(
            side_effect=Exception("Handler error")
        )
        
        context = PipelineContext(
            message={}, conversation={}, metadata={}
        )
        context.set_result("routing_path", "property")
        context.set_result("classification", {})
        context.set_result("rag_result", {})
        
        step = ResponseGeneratorStep(property_h, dept_h, gen_h)
        result = await step.execute(context)
        
        # Debe retornar respuesta de error (no fallar)
        final_response = result.get_result("final_response")
        assert "error" in final_response["response"].lower() or "disculpa" in final_response["response"].lower()
        assert result.error is not None

