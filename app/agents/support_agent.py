'''
    SupportAgent - Refactorizado con nuevo prompt especializado
    Responsabilidades: Respuestas RAG y Base de Conocimiento, Redirección Administrativa
    Personalidad: Sofia (profesional, concisa, orientadora)
'''

from typing import Dict, Any
from .base_agent import BaseAgent
from app.rag.rag_system import rag_system

class SupportAgent(BaseAgent):

    def __init__(self):
        super().__init__("SupportAgent")
        self.rag_system = rag_system

        # Inicializar LLM service para generación contextual
        if self.llm_service and not self.llm_service.api_client.initialized:
            self.llm_service.initialize()

    async def can_handle(self, message_data: Dict[str, Any], conversation: Dict[str, Any]) -> bool:
        """
        SupportAgent maneja consultas cuando:
        1. Estado actual es TRANSFERIDO y se transfirió desde ReceptionAgent para pregunta
        2. Estado es uno de los específicos de soporte (cuando se implementen)
        3. Conversación tiene metadata de transferencia a SupportAgent
        """
        current_state = conversation.get("state", "")

        # CASO 1: Estado TRANSFERIDO + transferencia desde ReceptionAgent
        if current_state == "TRANSFERIDO":
            transfer_metadata = conversation.get("transfer_metadata", {})
            return transfer_metadata.get("to_agent") == "SupportAgent"

        # CASO 2: Estados específicos de soporte (futuro)
        support_states = [
            "CONSULTA_RAG_ACTIVA",
            "SOPORTE_ADMINISTRATIVO",
            "REDIRECCIÓN_ESPECIALIZADA"
        ]

        # CASO 3: Transferencia explícita (metadata en conversación)
        transferred_to_support = conversation.get("current_agent") == "SupportAgent"

        return current_state in support_states or transferred_to_support

    async def process_message(self, message_data: Dict[str, Any], conversation: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa consulta usando RAG y reglas de redirección"""
        user_message = message_data.get("text", {}).get("body", "").strip()
        whatsapp_id = message_data.get("from")
        customer_name = conversation.get("customer_name", "")

        if not self.validate_message(user_message):
            return self.create_response("Por favor, envía un mensaje válido.")

        self.log_action("SupportAgent procesando consulta", {
            "message_preview": user_message[:50],
            "customer": customer_name or "Anónimo"
        })

        try:
            # PASO 1: Clasificar tipo de consulta
            consultation_type = await self._classify_consultation_type(user_message)

            if consultation_type == "inmueble_especifico":
                # Prohibición inquebrantable: No dar información de inmuebles
                return await self._handle_inmueble_inquiry()

            elif consultation_type in ["pagos", "facturas", "cartera"]:
                # Redirección administrativa: Cartera
                return await self._handle_cartera_redirect()

            elif consultation_type in ["reparaciones", "mantenimiento"]:
                # Redirección administrativa: Mantenimiento
                return await self._handle_mantenimiento_redirect()

            else:
                # Consulta general: Usar RAG
                return await self._handle_rag_consultation(user_message, customer_name)

        except Exception as e:
            self.log_error("Error en SupportAgent", e)
            return self.create_response(
                "Con mucho gusto paso tu información a nuestro equipo para ver cuál es la mejor manera de ayudarte."
            )

    async def _classify_consultation_type(self, message: str) -> str:
        """Clasificar tipo de consulta para determinar flujo"""
        message_lower = message.lower()

        # PRIORIDAD 1: Detectar consultas de mantenimiento (más específicas)
        mantenimiento_keywords = [
            "reparacion", "dañado", "arreglar", "mantenimiento", "plomeria",
            "electricidad", "pintura", "puerta", "ventana", "aire", "dano", "se dano"
        ]
        if any(keyword in message_lower for keyword in mantenimiento_keywords):
            return "reparaciones"

        # PRIORIDAD 2: Detectar consultas de cartera/pagos
        cartera_keywords = ["pago", "factura", "cartera", "cuota", "deuda", "saldo", "cuenta"]
        if any(keyword in message_lower for keyword in cartera_keywords):
            return "pagos"

        # PRIORIDAD 3: Detectar consultas sobre inmuebles específicos (PROHIBIDO)
        # Solo si no es mantenimiento ni cartera
        inmueble_keywords = [
            "precio", "valor", "costo", "cuanto cuesta", "ubicacion", "donde queda",
            "direccion", "metros", "habitaciones", "baños", "caracteristicas",
            "disponible", "inmueble"
        ]

        if any(keyword in message_lower for keyword in inmueble_keywords):
            return "inmueble_especifico"

        # Por defecto: consulta general para RAG
        return "general"

    async def _handle_inmueble_inquiry(self) -> Dict[str, Any]:
        """Manejo de consultas sobre inmuebles específicos - PROHIBIDO"""
        response = "Esa información detallada la maneja directamente nuestro equipo de asesores. Ellos se pondrán en contacto contigo muy pronto para resolver todas tus dudas."

        return self.create_response(
            response,
            transfer_to="LeadsalesAgent",  # Transfer a ventas para manejo especializado
            data_updates={"consultation_type": "inmueble_especifico"}
        )

    async def _handle_cartera_redirect(self) -> Dict[str, Any]:
        """Redirección administrativa: Cartera/Pagos"""
        # TODO: Obtener número/link real de cartera desde base de conocimiento
        response = "Claro, puedes comunicarte con el área de Cartera al (321) 123-4567 o escribir a cartera@inmobiliariaproteger.com para gestionar tu consulta de pagos."

        return self.create_response(
            response,
            new_state="REDIRIGIDO_CARTERA",
            data_updates={"consultation_type": "cartera", "redirected_to": "cartera"}
        )

    async def _handle_mantenimiento_redirect(self) -> Dict[str, Any]:
        """Redirección administrativa: Mantenimiento"""
        # TODO: Obtener contacto real de mantenimiento desde base de conocimiento
        response = "Por supuesto, puedes escribir al área de Mantenimiento al WhatsApp (324) 987-6543 o al correo mantenimiento@inmobiliariaproteger.com para que gestionen tu solicitud."

        return self.create_response(
            response,
            new_state="REDIRIGIDO_MANTENIMIENTO",
            data_updates={"consultation_type": "mantenimiento", "redirected_to": "mantenimiento"}
        )

    async def _handle_rag_consultation(self, user_message: str, customer_name: str = "") -> Dict[str, Any]:
        """Manejo de consulta general usando sistema RAG"""

        # PASO 1: Obtener contexto RAG
        rag_context = self.rag_system.get_context_for_query(user_message)

        if not rag_context or rag_context.strip() == "":
            # No hay contexto RAG disponible
            response = "Con mucho gusto paso tu información a nuestro equipo para ver cuál es la mejor manera de ayudarte."
            return self.create_response(response)

        # PASO 2: Verificar si hay LLM disponible para generación contextual
        if not self.llm_service or not self.llm_service.api_client.initialized:
            # Fallback: usar contexto RAG directamente
            response = f"{rag_context}\n\n¿Hay algo más en lo que pueda ayudarte?"
            return self.create_response(response)

        # PASO 3: Generar respuesta contextual usando LLM
        try:
            contextual_response = await self.llm_service.llm_generator.generate_contextual_response(
                user_question=user_message,
                context=rag_context,
                customer_name=customer_name
            )

            return self.create_response(
                contextual_response,
                new_state="SOPORTE_ACTIVO",
                data_updates={
                    "consultation_type": "rag_consulta",
                    "rag_used": True,
                    "llm_generated": True
                }
            )

        except Exception as e:
            self.log_error("Error generando respuesta contextual", e)
            # Fallback: contexto RAG directo
            response = f"{rag_context}\n\n¿Hay algo más en lo que pueda ayudarte?"
            return self.create_response(
                response,
                data_updates={"consultation_type": "rag_consulta", "rag_used": True, "llm_generated": False}
            )

    def _detect_administrative_topic(self, message: str) -> str:
        """Detectar si la consulta es de tipo administrativo"""
        message_lower = message.lower()

        # Mapeo de palabras clave a tipos administrativos
        admin_mapping = {
            "cartera": ["pago", "factura", "cartera", "cuota", "deuda", "saldo"],
            "mantenimiento": ["reparacion", "dañado", "arreglar", "mantenimiento", "plomeria"],
            "juridico": ["contrato", "juridico", "legal", "clausula", "termino"],
            "general": []  # Catch-all
        }

        for admin_type, keywords in admin_mapping.items():
            if any(keyword in message_lower for keyword in keywords):
                return admin_type

        return "general"

    def _generate_fallback_response(self, consultation_type: str) -> str:
        """Generar respuesta de fallback según tipo de consulta"""
        fallback_responses = {
            "cartera": "Para consultas de pagos y cartera, nuestro equipo especializado te atenderá. Se pondrán en contacto contigo pronto.",
            "mantenimiento": "Para solicitudes de mantenimiento, nuestro equipo técnico te contactará a la brevedad.",
            "general": "Con mucho gusto paso tu información a nuestro equipo para ver cuál es la mejor manera de ayudarte."
        }

        return fallback_responses.get(consultation_type, fallback_responses["general"])