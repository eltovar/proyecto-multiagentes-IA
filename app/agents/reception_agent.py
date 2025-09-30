'''
    ReceptionAgent - Refactorizado con nuevo prompt
    Responsabilidades: Flujo obligatorio de captación de datos (Etapas 1 y 2)
    Personalidad: Sofía, humana, empática, profesional
'''

from typing import Dict, Any, Optional
from app.agents.base_agent import BaseAgent
from app.config import (
    STATE_NUEVO, STATE_POLITICAS_PRESENTADAS, STATE_RECOPILANDO_NOMBRE,
    STATE_NOMBRE_OBTENIDO, STATE_PREGUNTA_CONTRATO_INMOBILIARIA,
    STATE_PREGUNTA_CUAL_INMOBILIARIA, STATE_PREGUNTA_SOLICITUD_LIBERTADOR,
    STATE_PREGUNTA_FECHA_NECESIDAD, STATE_FLUJO_COMPLETADO
)

class ReceptionAgent(BaseAgent):

    def __init__(self):
        super().__init__("reception")
        self.interaction_count = 0  # Contador de interacciones (máximo 10)

        # Links obligatorios para el flujo
        self.youtube_link = "https://www.youtube.com/watch?v=xyz"
        self.solicitud_gratis_link = "https://inmobiliariaproteger.com/solicitud-gratis"
        self.politicas_link = "https://inmobiliariaproteger.com/main-contenido-cat-6.htm"
        self.whatsapp_oficial = "324 551 6105"

    async def can_handle(self, message_data: Dict[str, Any], conversation: Dict[str, Any]) -> bool:
        """El ReceptionAgent maneja todos los estados del flujo obligatorio"""
        valid_states = [
            STATE_NUEVO, STATE_POLITICAS_PRESENTADAS, STATE_RECOPILANDO_NOMBRE,
            STATE_NOMBRE_OBTENIDO, STATE_PREGUNTA_CONTRATO_INMOBILIARIA,
            STATE_PREGUNTA_CUAL_INMOBILIARIA, STATE_PREGUNTA_SOLICITUD_LIBERTADOR,
            STATE_PREGUNTA_FECHA_NECESIDAD
        ]
        current_state = conversation.get("state", STATE_NUEVO)
        return current_state in valid_states and self.interaction_count < 10

    async def process_message(self, message_data: Dict[str, Any], conversation: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa mensaje siguiendo el flujo obligatorio estricto"""
        message = message_data.get("text", {}).get("body", "").strip()
        whatsapp_id = message_data.get("from")

        # Guardar referencia a conversación para métodos auxiliares
        self._current_conversation = conversation

        # Incrementar contador de interacciones
        self.interaction_count = conversation.get("interaction_count", 0) + 1

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
            return await self._handle_limite_interacciones()

        try:
            # Máquina de estados del flujo obligatorio
            if current_state == STATE_NUEVO:
                return await self._handle_saludo_inicial()
            elif current_state == STATE_POLITICAS_PRESENTADAS:
                return await self._handle_recopilar_nombre(message)
            elif current_state == STATE_RECOPILANDO_NOMBRE:
                return await self._handle_validar_nombre(message)
            elif current_state == STATE_NOMBRE_OBTENIDO:
                return await self._handle_pregunta_contrato_inmobiliaria()
            elif current_state == STATE_PREGUNTA_CONTRATO_INMOBILIARIA:
                return await self._handle_respuesta_contrato(message)
            elif current_state == STATE_PREGUNTA_CUAL_INMOBILIARIA:
                return await self._handle_respuesta_cual_inmobiliaria(message)
            elif current_state == STATE_PREGUNTA_SOLICITUD_LIBERTADOR:
                return await self._handle_respuesta_solicitud_libertador(message)
            elif current_state == STATE_PREGUNTA_FECHA_NECESIDAD:
                return await self._handle_respuesta_fecha_necesidad(message)
            else:
                self.log_error(f"Estado no reconocido: {current_state}")
                return await self._handle_saludo_inicial()

        except Exception as e:
            self.log_error("Error en flujo obligatorio", e)
            return self.create_response(
                "Disculpa, ocurrió un error. Un asesor se pondrá en contacto contigo.",
                data_updates={"interaction_count": self.interaction_count}
            )

    async def _handle_saludo_inicial(self) -> Dict[str, Any]:
        """Etapa 1: Saludo inicial + Políticas de Privacidad"""
        response = f"""Hola, soy Sofia de Inmobiliaria Proteger

Al escribir aceptas nuestras Politicas de Privacidad ({self.politicas_link})

¿Me podrias indicar tu nombre por favor?"""

        return self.create_response(
            response,
            new_state=STATE_POLITICAS_PRESENTADAS,
            data_updates={"interaction_count": self.interaction_count}
        )

    async def _handle_recopilar_nombre(self, message: str) -> Dict[str, Any]:
        """Maneja respuesta después de presentar políticas"""
        # Si ya respondió algo, extraer nombre
        name = self._extract_name(message)
        if name:
            return await self._handle_nombre_exitoso(name)
        else:
            # Insistir en el nombre
            response = "Para brindarte la mejor atención, necesito tu nombre. ¿Podrías indicármelo por favor?"
            return self.create_response(
                response,
                new_state=STATE_RECOPILANDO_NOMBRE,
                data_updates={"interaction_count": self.interaction_count}
            )

    async def _handle_validar_nombre(self, message: str) -> Dict[str, Any]:
        """Validar nombre después de insistencia"""
        name = self._extract_name(message)
        if name:
            return await self._handle_nombre_exitoso(name)
        else:
            # Segunda insistencia (es clave para el asesor)
            response = "Tu nombre es clave para que nuestro asesor te brinde una atención personalizada. ¿Me lo puedes compartir?"
            return self.create_response(
                response,
                new_state=STATE_RECOPILANDO_NOMBRE,
                data_updates={"interaction_count": self.interaction_count}
            )

    async def _handle_nombre_exitoso(self, name: str) -> Dict[str, Any]:
        """Nombre obtenido exitosamente, continuar flujo"""
        response = f"Perfecto {name}, ahora necesito hacerte unas preguntas rápidas para conectarte con el asesor ideal."
        return self.create_response(
            response,
            new_state=STATE_NOMBRE_OBTENIDO,
            data_updates={
                "customer_name": name,
                "interaction_count": self.interaction_count
            }
        )

    async def _handle_pregunta_contrato_inmobiliaria(self) -> Dict[str, Any]:
        """Pregunta obligatoria 1: Contrato con inmobiliaria"""
        response = "¿Actualmente tienes un contrato vigente con alguna inmobiliaria?"
        return self.create_response(
            response,
            new_state=STATE_PREGUNTA_CONTRATO_INMOBILIARIA,
            data_updates={"interaction_count": self.interaction_count}
        )

    async def _handle_respuesta_contrato(self, message: str) -> Dict[str, Any]:
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
                    "interaction_count": self.interaction_count
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
                    "interaction_count": self.interaction_count
                }
            )

    async def _handle_respuesta_cual_inmobiliaria(self, message: str) -> Dict[str, Any]:
        """Manejar respuesta sobre cuál inmobiliaria"""
        # Registrar inmobiliaria y continuar
        response = "Entendido. ¿Ya tienes una solicitud aprobada por EL LIBERTADOR?"
        return self.create_response(
            response,
            new_state=STATE_PREGUNTA_SOLICITUD_LIBERTADOR,
            data_updates={
                "inmobiliaria_actual": message.strip(),
                "interaction_count": self.interaction_count
            }
        )

    async def _handle_respuesta_solicitud_libertador(self, message: str) -> Dict[str, Any]:
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
                    "interaction_count": self.interaction_count
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
                    "interaction_count": self.interaction_count
                }
            )

    async def _handle_respuesta_fecha_necesidad(self, message: str) -> Dict[str, Any]:
        """Última pregunta del flujo - Transferir al siguiente agente"""
        # Obtener nombre de los datos de conversación (no del mensaje)
        conversation = getattr(self, '_current_conversation', {})
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
                "flujo_recepcion_completado": True
            }
        )

    async def _handle_limite_interacciones(self) -> Dict[str, Any]:
        """Manejar límite de 10 interacciones alcanzado"""
        response = f"""He registrado tu interés. Por favor contacta directamente a nuestro WhatsApp oficial {self.whatsapp_oficial} para continuar con tu consulta."""

        return self.create_response(
            response,
            new_state="LIMITE_ALCANZADO",
            transfer_to="LeadsalesAgent",
            data_updates={"interaction_count": self.interaction_count}
        )

    def _extract_name(self, message: str) -> Optional[str]:
        """Extraer nombre del mensaje - Método mejorado"""
        clean_message = message.strip()
        words = clean_message.split()

        # Lista de respuestas inválidas
        invalid_responses = [
            "no", "nope", "na", "nada", "nunca", "ninguno", "ninguna",
            "si", "sí", "ok", "okay", "bueno", "bien", "vale",
            "hola", "que", "qué", "como", "cómo", "cuando", "cuándo",
            "información", "info", "inmueble", "casa", "apartamento"
        ]

        # Verificar si es una respuesta inválida
        if len(words) == 1 and words[0].lower() in invalid_responses:
            return None

        # Validar nombre simple (1-3 palabras, solo letras)
        if 1 <= len(words) <= 3 and all(word.isalpha() and len(word) >= 2 for word in words):
            return " ".join(word.title() for word in words)

        # Buscar patrones específicos
        lower_message = clean_message.lower()
        patterns = ["mi nombre es ", "me llamo ", "soy ", "nombre: "]
        for pattern in patterns:
            if pattern in lower_message:
                name_part = lower_message.split(pattern, 1)[1].strip()
                first_word = name_part.split()[0] if name_part.split() else ""
                if first_word.isalpha() and len(first_word) >= 2:
                    return first_word.title()

        return None

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