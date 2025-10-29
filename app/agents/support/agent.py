""" SupportAgent - Versión refactorizada con Pipeline Pattern
    Reduce complejidad ciclomática mediante procesamiento secuencial """

from typing import Dict, Any
from app.agents.base_agent import BaseAgent
from app.core.pipeline import MessagePipeline, PipelineBuilder
from app.agents.support.pipeline_steps import (
    IntentClassifierStep,
    RAGSearchStep,
    RoutingDecisionStep,
    ResponseGeneratorStep
)
from app.agents.support.classifiers.intent import IntentClassifier
from app.agents.support.handlers.property import PropertyHandler
from app.agents.support.handlers.department import DepartmentHandler
from app.agents.support.handlers.general import GeneralHandler


class SupportAgent(BaseAgent):
    """
    Agente de soporte para consultas informativas (WhatsApp).
    """

    def __init__(self, llm_service=None, state_manager=None, rag_system=None):

        super().__init__("SupportAgent", llm_service=llm_service, state_manager=state_manager)

        # Servicios inyectados
        self.rag_system = rag_system

        # Validar e inicializar LLM
        if self.llm_service and hasattr(self.llm_service, 'api_client'):
            if not self.llm_service.api_client.initialized:
                self.llm_service.initialize()

        # Validar e inicializar RAG
        if self.rag_system and hasattr(self.rag_system, 'initialized'):
            if not self.rag_system.initialized:
                self.rag_system.initialize()

        # Crear componentes con DI
        self._initialize_components()

        # Construir pipeline
        self.pipeline = self._build_pipeline()

        self.log_action("SupportAgent inicializado con Pipeline Pattern", {
            "pipeline_steps": len(self.pipeline.steps),
            "llm_initialized": bool(self.llm_service),
            "rag_initialized": bool(self.rag_system)
        })

    def _initialize_components(self):
        """Inicializa clasificadores y handlers"""
        # Clasificador de intenciones
        self.intent_classifier = IntentClassifier()

        # Handlers especializados para cada camino
        self.property_handler = PropertyHandler(
            rag_system=self.rag_system,
            llm_service=self.llm_service
        )

        self.department_handler = DepartmentHandler(
            llm_service=self.llm_service,
            state_manager=self.state_manager,
            config={}
        )

        self.general_handler = GeneralHandler(
            llm_service=self.llm_service,
            state_manager=self.state_manager,
            config={}
        )

    def _build_pipeline(self) -> MessagePipeline:
        """
        Construye pipeline de procesamiento.

        Returns:
            MessagePipeline configurado
        """
        return (PipelineBuilder("SupportAgentPipeline")
                .add(IntentClassifierStep(self.intent_classifier))
                .add(RAGSearchStep(self.rag_system))
                .add(RoutingDecisionStep())
                .add(ResponseGeneratorStep(
                    property_handler=self.property_handler,
                    department_handler=self.department_handler,
                    general_handler=self.general_handler
                ))
                .with_logging()
                .build())

    async def process_message(
        self,
        message_data: Dict[str, Any],
        conversation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """ Procesa mensaje usando Pipeline Pattern. """
        try:
            # Ejecutar pipeline
            context = await self.pipeline.process(
                message=message_data,
                conversation=conversation
            )

            # Extraer resultado final
            final_response = context.get_result("final_response")

            if not final_response:
                self.log_error("Pipeline no generó respuesta final")
                return self.create_response(
                    "Disculpa, ocurrió un error procesando tu mensaje.",
                    new_state="ERROR"
                )

            # Construir respuesta estándar
            return self.create_response(
                response=final_response.get("response", ""),
                new_state=final_response.get("next_state"),
                transfer_to=final_response.get("transfer_to"),
                data_updates=final_response.get("data_updates")
            )

        except Exception as e:
            self.log_error("Error en pipeline de SupportAgent", e)
            return self.create_response(
                "Disculpa, hay un problema técnico. Un asesor se contactará contigo.",
                new_state="ERROR"
            )
