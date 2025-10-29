"""
Pipeline Steps para SupportAgent
Implementa pasos especficos del flujo RAG-first routing
"""

from typing import Dict, Any
from app.core.pipeline import PipelineStep, PipelineContext
from app.agents.support.classifiers.intent import IntentClassifier
from app.agents.support.handlers.property import PropertyHandler
from app.agents.support.handlers.department import DepartmentHandler
from app.agents.support.handlers.general import GeneralHandler


class IntentClassifierStep(PipelineStep):
    """
    Paso 1: Clasificar intencin del usuario con LLM."]
    """

    def __init__(self, classifier: IntentClassifier):
        super().__init__("IntentClassifier")
        self.classifier = classifier

    async def execute(self, context: PipelineContext) -> PipelineContext:
        """Clasifica intencin del mensaje"""
        # Manejar diferentes formatos de mensaje
        text = context.message.get("text", "")
        if isinstance(text, dict):
            # Formato WhatsApp: {"text": {"body": "mensaje"}}
            message = text.get("body", "")
        else:
            # Formato simple: {"text": "mensaje"}
            message = text

        # Clasificar con LLM
        classification = await self.classifier.classify(
            message=message,
            conversation=context.conversation
        )

        # Guardar resultado
        context.set_result("classification", {
            "intent": classification.intent,
            "sub_intent": classification.sub_intent,
            "confidence": classification.confidence,
            "entities": classification.entities,
            "reasoning": classification.reasoning
        })

        print(f"[IntentClassifierStep] Intent: {classification.intent}, Confidence: {classification.confidence}")

        return context


class RAGSearchStep(PipelineStep):
    """
    Paso 2: Buscar contexto relevante en RAG.

    """

    def __init__(self, rag_system):
        super().__init__("RAGSearch")
        self.rag = rag_system

    async def execute(self, context: PipelineContext) -> PipelineContext:
        """Busca contexto en RAG"""
        # Manejar diferentes formatos de mensaje
        text = context.message.get("text", "")
        if isinstance(text, dict):
            message = text.get("body", "")
        else:
            message = text

        # Buscar en RAG si est disponible
        if self.rag and hasattr(self.rag, 'search_context'):
            try:
                rag_result = self.rag.search_context(message)
                context.set_result("rag_result", rag_result)
                print(f"[RAGSearchStep] Found {len(rag_result.get('documents', []))} documents")
            except Exception as e:
                print(f"[RAGSearchStep] Error: {e}, usando contexto vaco")
                context.set_result("rag_result", self._empty_rag_result())
        else:
            context.set_result("rag_result", self._empty_rag_result())

        return context

    def _empty_rag_result(self) -> Dict[str, Any]:
        """Resultado RAG vaco"""
        return {
            "documents": [],
            "context": "",
            "phone_numbers": [],
            "rag_confidence": 0.0
        }


class RoutingDecisionStep(PipelineStep):
    """
    Paso 3: Decidir routing basado en clasificacin.

    """

    def __init__(self):
        super().__init__("RoutingDecision")

    async def execute(self, context: PipelineContext) -> PipelineContext:
        """Determina camino de routing"""
        classification = context.get_result("classification")

        if not classification:
            context.set_result("routing_path", "general")
            return context

        intent = classification.get("intent", "unclear")

        # Mapear intent a routing path
        routing_map = {
            # Intents legacy
            "inmueble": "property",
            "departamento": "department",
            "general": "general",
            "unclear": "general",
            # Intents de IntentClassifier
            "property_inquiry": "property",
            "department_transfer": "department",
            "general_question": "general",
            "complaint": "general",
            "information": "general",
            "other": "general"
        }

        routing_path = routing_map.get(intent, "general")
        context.set_result("routing_path", routing_path)

        print(f"[RoutingDecisionStep] Routing: {routing_path}")

        return context


class ResponseGeneratorStep(PipelineStep):
    """
    Paso 4: Generar respuesta usando handler apropiado.
    """

    def __init__(
        self,
        property_handler: PropertyHandler,
        department_handler: DepartmentHandler,
        general_handler: GeneralHandler
    ):
        super().__init__("ResponseGenerator")
        self.handlers = {
            "property": property_handler,
            "department": department_handler,
            "general": general_handler
        }

    async def execute(self, context: PipelineContext) -> PipelineContext:
        """Genera respuesta final usando handler apropiado"""
        routing_path = context.get_result("routing_path")
        classification = context.get_result("classification")
        rag_result = context.get_result("rag_result")

        # Obtener handler apropiado
        handler = self.handlers.get(routing_path)

        if not handler:
            print(f"[ResponseGeneratorStep] No handler for path: {routing_path}")
            context.set_result("final_response", {
                "response": "Lo siento, no pude procesar tu solicitud.",
                "next_state": "ERROR"
            })
            return context

        # Generar respuesta con handler
        customer_name = context.conversation.get("customer_name", "")

        try:
            if routing_path == "property":
                result = await handler.handle_property_request(
                    classification=classification,
                    rag_result=rag_result,
                    customer_name=customer_name
                )
                context.set_result("final_response", {
                    "response": result.response,
                    "next_state": result.next_state,
                    "transfer_to": result.transfer_to,
                    "data_updates": result.data_updates
                })

            elif routing_path == "department":
                result = await handler.handle_department_request(
                    classification=classification,
                    rag_result=rag_result,
                    customer_name=customer_name
                )
                context.set_result("final_response", {
                    "response": result.response,
                    "next_state": result.next_state,
                    "department": result.department,
                    "contact_info": result.contact_info
                })

            elif routing_path == "general":
                result = await handler.handle_general_query(
                    classification=classification,
                    rag_result=rag_result,
                    customer_name=customer_name
                )
                context.set_result("final_response", {
                    "response": result.response,
                    "next_state": result.next_state,
                    "clarification_needed": result.clarification_needed
                })

            print(f"[ResponseGeneratorStep] Response generated via {routing_path} handler")

        except Exception as e:
            print(f"[ResponseGeneratorStep] Error: {e}")
            context.error = e
            context.set_result("final_response", {
                "response": "Disculpa, ocurri un error. Un asesor se contactar contigo.",
                "next_state": "ERROR"
            })

        return context
