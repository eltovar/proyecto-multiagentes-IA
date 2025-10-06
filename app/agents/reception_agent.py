'''
    ReceptionAgent - Refactorizado con nuevo prompt
    Responsabilidades: Flujo obligatorio de captación de datos (Etapas 1 y 2)
    Personalidad: Sofía, humana, empática, profesional
'''

from typing import Dict, Any, Optional
import json
from datetime import datetime
from app.agents.base_agent import BaseAgent
from app.config import (
    STATE_NUEVO, STATE_POLITICAS_PRESENTADAS, STATE_RECOPILANDO_NOMBRE,
    STATE_NOMBRE_OBTENIDO, STATE_PREGUNTA_CONTRATO_INMOBILIARIA,
    STATE_PREGUNTA_CUAL_INMOBILIARIA, STATE_PREGUNTA_SOLICITUD_LIBERTADOR,
    STATE_PREGUNTA_FECHA_NECESIDAD, STATE_FLUJO_COMPLETADO
)
from app.services.llm_service import LLMService
from app.config.business_hours import BusinessHoursConfig

class ReceptionAgent(BaseAgent):
    """
    Agente encargado de la recepción y el flujo obligatorio de captura
    de datos iniciales del cliente. Ahora usa LLM para extracción de nombre
    e intenciones y maneja la validación de horarios.
    """
    def __init__(self):
        """Constructor: Inicializa el servicio LLM y las constantes de negocio."""
        super().__init__("reception")
        # Nota: self.interaction_count eliminado, se obtiene de la conversación

        # Links obligatorios para el flujo
        self.youtube_link = "https://www.youtube.com/watch?v=xyz"
        self.solicitud_gratis_link = "https://inmobiliariaproteger.com/solicitud-gratis"
        self.politicas_link = "https://inmobiliariaproteger.com/main-contenido-cat-6.htm"
        self.whatsapp_oficial = "324 551 6105"

        # Inicializar LLM Service para extracción de intenciones y entidades
        self.llm_service = LLMService()
        self.llm_service.initialize()

    async def can_handle(self, message_data: Dict[str, Any], conversation: Dict[str, Any]) -> bool:
        """El ReceptionAgent maneja todos los estados del flujo obligatorio"""
        valid_states = [
            STATE_NUEVO, STATE_POLITICAS_PRESENTADAS, STATE_RECOPILANDO_NOMBRE,
            STATE_NOMBRE_OBTENIDO, STATE_PREGUNTA_CONTRATO_INMOBILIARIA,
            STATE_PREGUNTA_CUAL_INMOBILIARIA, STATE_PREGUNTA_SOLICITUD_LIBERTADOR,
            STATE_PREGUNTA_FECHA_NECESIDAD
        ]
        current_state = conversation.get("state", STATE_NUEVO)
        # Usar el interaction_count de la conversación
        interaction_count = conversation.get("interaction_count", 0)
        return current_state in valid_states and interaction_count < 10

    async def process_message(self, message_data: Dict[str, Any], conversation: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa mensaje siguiendo el flujo obligatorio estricto"""
        message = message_data.get("text", {}).get("body", "").strip()
        whatsapp_id = message_data.get("from")

        # Incrementar contador de interacciones (local para este proceso)
        self.interaction_count = conversation.get("interaction_count", 0) + 1
        
        # La validación de mensaje básico se mantiene si es de BaseAgent y es útil,
        # pero con el LLM, su relevancia disminuye. Se mantiene por ahora.
        
        if not self.validate_message(message):
             return self.create_response("Por favor, envía un mensaje válido.",
                                         data_updates={"interaction_count": self.interaction_count})

        current_state = conversation.get("state", STATE_NUEVO)
        self.log_action("Procesando flujo obligatorio", {
            "state": current_state,
            "interaction": self.interaction_count
        })

        # Verificar límite de interacciones
        if self.interaction_count >= 10:
            return await self._handle_limite_interacciones(conversation)

        # VALIDACIÓN DE HORARIOS (solo en primer contacto)
        
        if current_state == STATE_NUEVO:
            if not BusinessHoursConfig.is_business_hours():
                out_of_hours_msg = BusinessHoursConfig.get_out_of_hours_message(
                    customer_name=conversation.get("customer_name")
                )

                self.log_action("Mensaje fuera de horario", {
                    "horario_status": BusinessHoursConfig.get_current_status()
                })

                return self.create_response(
                    out_of_hours_msg,
                    new_state="FUERA_DE_HORARIO",
                    data_updates={
                        "business_hours_valid": 0,
                        "last_message_at": datetime.now().isoformat(),
                        "interaction_count": self.interaction_count
                    }
                )

        # EXTRACCIÓN LLM EN ESTADOS INICIALES (para saltos y routing)
        
        extraction_updates = {}
        extraction = {}

        #obtener el nombre del cliente y su intención en las primeras etapas de la conversación
        if current_state in [STATE_NUEVO, STATE_POLITICAS_PRESENTADAS, STATE_RECOPILANDO_NOMBRE]:
            self.log_action("Llamando a LLM para clasificación", {"state": current_state})

            extraction = await self.llm_service.classify_intent_and_extract_entities(
                message=message,
                context={
                    "state": current_state,
                    "customer_name": conversation.get("customer_name"),
                    "interaction_count": self.interaction_count
                }
            )

            self.log_action("LLM Result", {
                "intent": extraction.get("intent"),
                "confidence": extraction.get("confidence"),
                "nombre": extraction.get("nombre")
            })
            
            # SUB-PASO 1: Preparar updates de LLM
            extraction_updates = {
                "intent": extraction.get("intent"),
                "extracted_data": json.dumps(extraction, ensure_ascii=False),
                "last_message_at": datetime.now().isoformat(),
                "interaction_count": self.interaction_count
            }

            # SUB-PASO 2: Si nombre detectado, guardarlo y saltar estado
            extracted_name = extraction.get("nombre")
            if extracted_name and not conversation.get("customer_name"):
                self.log_action("✅ Nombre extraído por LLM", {"nombre": extracted_name})
                extraction_updates["customer_name"] = extracted_name

                # ✨ SALTAR estado RECOPILANDO_NOMBRE si ya tenemos el nombre
                if current_state in [STATE_POLITICAS_PRESENTADAS, STATE_RECOPILANDO_NOMBRE]:
                    self.log_action("🚀 Saltando estados de nombre", {})
                    # Llamar al método de éxito con los updates extraídos
                    return await self._handle_nombre_exitoso_with_updates(
                        extracted_name,
                        extraction_updates
                    )

            # SUB-PASO 3: Routing por intención (alta confianza)
            if extraction.get("confidence", 0) > 0.75:
                # INTENT: SUPPORT -> Transferir a SupportAgent
                if extraction["intent"] == "support":
                    self.log_action("🔀 Transfiriendo a SupportAgent", {
                        "reason": "support_intent_detected",
                        "confidence": extraction["confidence"]
                    })
                    
                    # Usar el nombre extraído o el existente para el mensaje
                    customer_name = extracted_name or conversation.get('customer_name') or ''
                    customer_name_part = f", {customer_name}" if customer_name else ""

                    return self.create_response(
                        f"Entiendo que tienes una consulta de soporte{customer_name_part}. Déjame transferirte con nuestro equipo especializado.",
                        transfer_to="SupportAgent",
                        data_updates=extraction_updates
                    )

                # INTENT: MEDIA_SENT -> Mensaje especial
                if extraction["intent"] == "media":
                    return self.create_response(
                        """Entiendo que compartiste un link o imagen.
Como asistente virtual no puedo procesar contenido multimedia,
pero un asesor humano podrá revisarlo. ¿Podrías describir brevemente qué necesitas?""",
                        data_updates=extraction_updates
                    )

        # ═══════════════════════════════════════════════════════════
        # MÁQUINA DE ESTADOS (Si no hubo salto ni transferencia)
        # ═══════════════════════════════════════════════════════════
        try:
            # Notar que los métodos _handle_* ahora reciben 'conversation'
            if current_state == STATE_NUEVO:
                return await self._handle_saludo_inicial(conversation)
            elif current_state == STATE_POLITICAS_PRESENTADAS:
                # El manejo de nombre ahora se basa en la extracción del LLM de arriba
                return await self._handle_recopilar_nombre_llm_fallback(conversation)
            elif current_state == STATE_RECOPILANDO_NOMBRE:
                # El manejo de nombre ahora se basa en la extracción del LLM de arriba
                return await self._handle_validar_nombre_llm_fallback(conversation)
            elif current_state == STATE_NOMBRE_OBTENIDO:
                return await self._handle_pregunta_contrato_inmobiliaria(conversation)
            elif current_state == STATE_PREGUNTA_CONTRATO_INMOBILIARIA:
                return await self._handle_respuesta_contrato(message, conversation)
            elif current_state == STATE_PREGUNTA_CUAL_INMOBILIARIA:
                return await self._handle_respuesta_cual_inmobiliaria(message, conversation)
            elif current_state == STATE_PREGUNTA_SOLICITUD_LIBERTADOR:
                return await self._handle_respuesta_solicitud_libertador(message, conversation)
            elif current_state == STATE_PREGUNTA_FECHA_NECESIDAD:
                return await self._handle_respuesta_fecha_necesidad(message, conversation)
            else:
                self.log_error(f"Estado no reconocido: {current_state}")
                return await self._handle_saludo_inicial(conversation)

        except Exception as e:
            self.log_error("Error en flujo obligatorio", e)
            return self.create_response(
                "Disculpa, ocurrió un error. Un asesor se pondrá en contacto contigo.",
                data_updates={"interaction_count": self.interaction_count}
            )

    # ═══════════════════════════════════════════════════════════
    # MÉTODOS DE MANEJO DE ESTADO (HANDLERS)
    # ═══════════════════════════════════════════════════════════

    async def _handle_saludo_inicial(self, conversation: Dict[str, Any]) -> Dict[str, Any]:
        """Etapa 1: Saludo inicial + Políticas de Privacidad"""
        response = f"""Hola, soy Sofia de Inmobiliaria Proteger

Al escribir aceptas nuestras Politicas de Privacidad ({self.politicas_link})

¿Me podrias indicar tu nombre por favor?"""

        return self.create_response(
            response,
            new_state=STATE_POLITICAS_PRESENTADAS,
            data_updates={
                "interaction_count": self.interaction_count,
                "last_message_at": datetime.now().isoformat()
            }
        )

    # 🚨 NUEVOS HANDLERS SIMPLIFICADOS (Solo insisten si no hubo salto de LLM) 🚨

    async def _handle_recopilar_nombre_llm_fallback(self, conversation: Dict[str, Any]) -> Dict[str, Any]:
        """Insiste si el LLM no extrajo el nombre y aún estamos en este estado."""
        response = "Para brindarte la mejor atención, necesito tu nombre. ¿Podrías indicármelo por favor?"
        return self.create_response(
            response,
            new_state=STATE_RECOPILANDO_NOMBRE, # Mueve al estado de recopilación para reintentar
            data_updates={
                "interaction_count": self.interaction_count,
                "last_message_at": datetime.now().isoformat()
            }
        )

    async def _handle_validar_nombre_llm_fallback(self, conversation: Dict[str, Any]) -> Dict[str, Any]:
        """Segunda insistencia en nombre si el LLM aún no lo ha extraído."""
        # Se asume que el LLM ya se corrió en process_message, si estamos aquí es porque falló la extracción
        response = "Tu nombre es clave para que nuestro asesor te brinde una atención personalizada. ¿Me lo puedes compartir?"
        return self.create_response(
            response,
            new_state=STATE_RECOPILANDO_NOMBRE, # Quedarse en el mismo estado para esperar otro intento
            data_updates={
                "interaction_count": self.interaction_count,
                "last_message_at": datetime.now().isoformat()
            }
        )

    # 🚨 NOTA: _handle_nombre_exitoso y _handle_nombre_exitoso_with_updates se mantienen
    # pero _handle_nombre_exitoso se podría eliminar si solo se usa la versión con updates

    async def _handle_nombre_exitoso(self, name: str) -> Dict[str, Any]:
        """Nombre obtenido exitosamente, continuar flujo (Versión simple)"""
        response = f"Perfecto {name}, ahora necesito hacerte unas preguntas rápidas para conectarte con el asesor ideal."
        return self.create_response(
            response,
            new_state=STATE_NOMBRE_OBTENIDO,
            data_updates={
                "customer_name": name,
                "interaction_count": self.interaction_count,
                "last_message_at": datetime.now().isoformat()
            }
        )

    async def _handle_nombre_exitoso_with_updates(self, name: str, extra_updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Nombre obtenido exitosamente con updates adicionales de LLM.
        Usado cuando el nombre fue extraído por LLM y queremos preservar extracted_data.
        """
        response = f"Perfecto {name}, ahora necesito hacerte unas preguntas rápidas para conectarte con el asesor ideal."

        # Combinar updates base con extra_updates
        all_updates = {
            "customer_name": name,
            "interaction_count": self.interaction_count,
            "last_message_at": datetime.now().isoformat()
        }
        all_updates.update(extra_updates)

        return self.create_response(
            response,
            new_state=STATE_NOMBRE_OBTENIDO,
            data_updates=all_updates
        )

    async def _handle_pregunta_contrato_inmobiliaria(self, conversation: Dict[str, Any]) -> Dict[str, Any]:
        """Pregunta obligatoria 1: Contrato con inmobiliaria"""
        response = "¿Actualmente tienes un contrato vigente con alguna inmobiliaria?"
        return self.create_response(
            response,
            new_state=STATE_PREGUNTA_CONTRATO_INMOBILIARIA,
            data_updates={
                "interaction_count": self.interaction_count,
                "last_message_at": datetime.now().isoformat()
            }
        )

    async def _handle_respuesta_contrato(self, message: str, conversation: Dict[str, Any]) -> Dict[str, Any]:
        """Manejar respuesta sobre contrato inmobiliaria"""
        respuesta_lower = message.lower().strip()

        if any(palabra in respuesta_lower for palabra in ["sí", "si", "yes", "tengo", "claro"]):
            # Tiene contrato -> Preguntar cuál inmobiliaria
            response = "¿Con cuál inmobiliaria tienes el contrato?"
            return self.create_response(
                response,
                new_state=STATE_PREGUNTA_CUAL_INMOBILIARIA,
                data_updates={
                    "tiene_contrato_inmobiliaria": True,
                    "interaction_count": self.interaction_count,
                    "last_message_at": datetime.now().isoformat()
                }
            )
        else:
            # No tiene contrato -> Continuar a solicitud Libertador
            response = "Perfecto. ¿Ya tienes una solicitud aprobada por EL LIBERTADOR?"
            return self.create_response(
                response,
                new_state=STATE_PREGUNTA_SOLICITUD_LIBERTADOR,
                data_updates={
                    "tiene_contrato_inmobiliaria": False,
                    "interaction_count": self.interaction_count,
                    "last_message_at": datetime.now().isoformat()
                }
            )

    async def _handle_respuesta_cual_inmobiliaria(self, message: str, conversation: Dict[str, Any]) -> Dict[str, Any]:
        """Manejar respuesta sobre cuál inmobiliaria"""
        # Registrar inmobiliaria y continuar
        response = "Entendido. ¿Ya tienes una solicitud aprobada por EL LIBERTADOR?"
        return self.create_response(
            response,
            new_state=STATE_PREGUNTA_SOLICITUD_LIBERTADOR,
            data_updates={
                "inmobiliaria_actual": message.strip(),
                "interaction_count": self.interaction_count,
                "last_message_at": datetime.now().isoformat()
            }
        )

    async def _handle_respuesta_solicitud_libertador(self, message: str, conversation: Dict[str, Any]) -> Dict[str, Any]:
        """Manejar respuesta sobre solicitud El Libertador"""
        respuesta_lower = message.lower().strip()

        if any(palabra in respuesta_lower for palabra in ["no", "nope", "aún no", "todavía no"]):
            # No tiene solicitud -> Mostrar orientación y links
            response = f"""Te oriento para que puedas aplicar:

Video explicativo: {self.youtube_link}
Solicitud GRATIS: {self.solicitud_gratis_link}

¿Para que fecha necesitas el nuevo inmueble?"""

            return self.create_response(
                response,
                new_state=STATE_PREGUNTA_FECHA_NECESIDAD,
                data_updates={
                    "tiene_solicitud_libertador": False,
                    "interaction_count": self.interaction_count,
                    "last_message_at": datetime.now().isoformat()
                }
            )
        else:
            # Sí tiene solicitud -> Continuar directamente
            response = "Excelente. ¿Para que fecha necesitas el nuevo inmueble?"
            return self.create_response(
                response,
                new_state=STATE_PREGUNTA_FECHA_NECESIDAD,
                data_updates={
                    "tiene_solicitud_libertador": True,
                    "interaction_count": self.interaction_count,
                    "last_message_at": datetime.now().isoformat()
                }
            )

    async def _handle_respuesta_fecha_necesidad(self, message: str, conversation: Dict[str, Any]) -> Dict[str, Any]:
        """Última pregunta del flujo - Transferir al siguiente agente"""
        # Obtener nombre directamente del objeto conversation
        name = conversation.get("customer_name", "")

        # Etapa 3: Gestión de Expectativas y Redirección
        response = f"""{name}, he registrado tu interés.

En breve, uno de nuestros asesores te contactará desde nuestro WhatsApp oficial, el {self.whatsapp_oficial}, para brindarte todos los detalles."""

        return self.create_response(
            response,
            new_state=STATE_FLUJO_COMPLETADO,
            transfer_to="LeadsalesAgent",  # Transfer al agente de ventas
            data_updates={
                "fecha_necesidad": message.strip(),
                "interaction_count": self.interaction_count,
                "flujo_recepcion_completado": True,
                "last_message_at": datetime.now().isoformat()
            }
        )

    async def _handle_limite_interacciones(self, conversation: Dict[str, Any]) -> Dict[str, Any]:
        """Manejar límite de 10 interacciones alcanzado"""
        response = f"""He registrado tu interés. Por favor contacta directamente a nuestro WhatsApp oficial {self.whatsapp_oficial} para continuar con tu consulta."""

        return self.create_response(
            response,
            new_state="LIMITE_ALCANZADO",
            transfer_to="LeadsalesAgent",
            data_updates={
                "interaction_count": self.interaction_count,
                "last_message_at": datetime.now().isoformat()
            }
        )

    def _mantener_flujo(self, estado_actual: str) -> str:
        """Mantener flujo si cliente se desvía"""
        flujo_messages = {
            STATE_POLITICAS_PRESENTADAS: "Primero necesito tu nombre para continuar. ¿Me lo puedes compartir?",
            STATE_RECOPILANDO_NOMBRE: "Tu nombre es importante para la atención personalizada. ¿Cuál es?",
            STATE_PREGUNTA_CONTRATO_INMOBILIARIA: "Por favor responde: ¿Tienes contrato vigente con alguna inmobiliaria?",
            STATE_PREGUNTA_SOLICITUD_LIBERTADOR: "Necesito saber: ¿Ya tienes solicitud aprobada por EL LIBERTADOR?",
            STATE_PREGUNTA_FECHA_NECESIDAD: "¿Para que fecha necesitas el nuevo inmueble?"
        }
        return flujo_messages.get(estado_actual, "Sigamos con el proceso paso a paso.")