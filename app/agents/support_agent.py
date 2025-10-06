from typing import Dict, Any, List, Optional
import re
import json
from .base_agent import BaseAgent
from app.services.llm_service import LLMService
from app.rag.rag_system import rag_system
from app.config import DEPARTMENT_CONTACTS, STATE_TRANSFERIDO
from app.prompts import CLASSIFY_TRIPATH_INTENT


class SupportAgent(BaseAgent):
    """
    Agente principal con routing inteligente basado en RAG.
    RESPONSABILIDADES:
    1. Clasificar intención (LLM + RAG)
    2. CAMINO 1: Inmuebles → Transfer a ReceptionAgent
    3. CAMINO 2: Departamentos → Extraer números de RAG docs
    4. CAMINO 3: Info general → Respuesta RAG directa
    """

    def __init__(self):
        super().__init__("SupportAgent")

        # ✅ Reutilizar LLMService del singleton de BaseAgent (elimina duplicación)
        if not self.llm_service:
            self.llm_service = LLMService()

        # Inicializar LLM solo si necesario
        if self.llm_service and not self.llm_service.api_client.initialized:
            self.llm_service.initialize()

        # RAG system es singleton global
        self.rag_system = rag_system

        # Inicializar RAG solo si necesario
        if self.rag_system and not self.rag_system.initialized:
            self.rag_system.initialize()

        # ✅ Configuración routing DRY - Reutiliza DEPARTMENT_CONTACTS
        self.routing_config = {
            "inmueble_keywords": [
                "comprar", "vender", "apartamento", "casa", "arriendo",
                "local", "lote", "propiedad", "inmueble", "cita", "visita",
                "agendar", "alquilar", "arrendar"
            ],
            # ✅ Elimina duplicación - Usa keywords de DEPARTMENT_CONTACTS
            "departamento_keywords": {
                dept: config["keywords"]
                for dept, config in DEPARTMENT_CONTACTS.items()
            },
            "general_keywords": [
                "quiénes", "historia", "horario", "ubicación", "blog",
                "servicios", "empresa", "política"
            ]
        }

        # ✅ Regex mejorado - Soporta +57 y formatos variados
        self.phone_regex = re.compile(
            r'\+?57\s?'                          # +57 opcional
            r'[\(\[]?\s?'                        # ( o [ opcional
            r'(\d{3})'                           # 3 dígitos
            r'[\)\]]?\s?[\s\.\-]?\s?'           # separador flexible
            r'(\d{3})'                           # 3 dígitos
            r'[\s\.\-]?\s?'                     # separador
            r'(\d{4})\b'                         # 4 dígitos
        )

        self.log_action("SupportAgent inicializado", {
            "rag_initialized": self.rag_system.initialized if self.rag_system else False,
            "llm_initialized": self.llm_service.api_client.initialized if self.llm_service else False
        })

    async def can_handle(self, message_data: Dict[str, Any], conversation: Dict[str, Any]) -> bool:
        """
        SupportAgent maneja:
        1. Estados iniciales (NUEVO, ROUTING_ANALYSIS)
        2. Estados activos (SUPPORT_ACTIVE, DEPARTMENT_REDIRECT)
        3. Post-engagement (FLUJO_COMPLETADO)
        4. Transferencias explícitas a SupportAgent

        NO maneja:
        - TRANSFERIDO (handoff a humano)
        - Estados del flujo de ReceptionAgent (delegados a ReceptionAgent)
        """
        current_state = conversation.get("state", "NUEVO")

        # NO manejar si transferido a humano
        if current_state == STATE_TRANSFERIDO:
            transfer_metadata = conversation.get("transfer_metadata", {})
            # Solo si fue transferido DESDE otro agente A SupportAgent
            return transfer_metadata.get("to_agent") == "SupportAgent"

        # Manejar estados específicos donde SupportAgent es apropiado
        support_states = [
            "NUEVO",
            "ROUTING_ANALYSIS",
            "SUPPORT_ACTIVE",
            "DEPARTMENT_REDIRECT",
            "FLUJO_COMPLETADO"
        ]

        return current_state in support_states

    async def process_message(
        self,
        message_data: Dict[str, Any],
        conversation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Pipeline principal de routing (KISS - Keep It Simple, Stupid):

        1. Clasificación LLM (intent + entities)
        2. RAG Search (OBLIGATORIO - contexto + phones)
        3. Routing Decision (decision tree)
        4. Ejecución del camino elegido

        Complejidad Ciclomática: 12 (Alta pero justificada por routing)
        """
        user_message = message_data.get("text", {}).get("body", "").strip()
        customer_name = conversation.get("customer_name", "")
        current_state = conversation.get("state", "NUEVO")

        if not self.validate_message(user_message):
            return self.create_response("Por favor, envía un mensaje válido.")

        self.log_action("Pipeline tri-path iniciado", {
            "message_preview": user_message[:50],
            "state": current_state,
            "customer": customer_name or "Anónimo"
        })

        try:
            # ═══════════════════════════════════════════════════
            # PASO 1: Clasificación LLM
            # ═══════════════════════════════════════════════════
            classification = await self._classify_user_intent(user_message, conversation)
            intent = classification.get("intent", "unclear")
            confidence = classification.get("confidence", 0.0)

            self.log_action("Clasificación completada", {
                "intent": intent,
                "confidence": confidence,
                "sub_intent": classification.get("sub_intent")
            })

            # ═══════════════════════════════════════════════════
            # PASO 2: RAG Search (OBLIGATORIO)
            # ═══════════════════════════════════════════════════
            rag_result = await self._search_rag_for_routing(
                user_message=user_message,
                intent=intent,
                entities=classification.get("entities", {}),
                classification=classification
            )

            self.log_action("RAG search completado", {
                "docs_found": len(rag_result.get("documents", [])),
                "phones_found": len(rag_result.get("phone_numbers", [])),
                "context_length": len(rag_result.get("context", ""))
            })

            # ═══════════════════════════════════════════════════
            # PASO 3: Routing Decision
            # ═══════════════════════════════════════════════════
            routing_path = self._determine_routing_path(
                intent=intent,
                classification=classification,
                rag_result=rag_result,
                user_message=user_message
            )

            self.log_action("Routing decidido", {"path": routing_path})

            # ═══════════════════════════════════════════════════
            # PASO 4: Ejecución del camino
            # ═══════════════════════════════════════════════════
            if routing_path == "CAMINO_1_INMUEBLE":
                return await self._handle_camino_1_inmueble(
                    classification, rag_result, customer_name
                )
            elif routing_path == "CAMINO_2_DEPARTAMENTO":
                return await self._handle_camino_2_departamento(
                    classification, rag_result, customer_name
                )
            elif routing_path == "CAMINO_3_GENERAL":
                return await self._handle_camino_3_general(
                    user_message, rag_result, customer_name
                )
            else:
                return await self._handle_unclear_intent(user_message, customer_name)

        except Exception as e:
            self.log_error("Error en pipeline tri-path", e, {
                "message": user_message[:100],
                "state": current_state
            })
            return self.create_response(
                "Disculpa, hay un problema técnico. Un asesor se comunicará contigo pronto."
            )

    # ═══════════════════════════════════════════════════════════════
    # MÉTODOS DE CLASIFICACIÓN
    # ═══════════════════════════════════════════════════════════════

    async def _classify_user_intent(
        self,
        message: str,
        conversation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Clasificar intención usando LLM con prompt CLASSIFY_TRIPATH_INTENT.

        Returns:
            {
                "intent": "inmueble" | "departamento" | "general" | "unclear",
                "sub_intent": str | null,
                "confidence": float,
                "entities": {...},
                "reasoning": str
            }

        Fallback: Keywords si LLM falla
        Complejidad: 6 (Media)
        """
        try:
            # Preparar contexto para el prompt
            context = {
                "customer_name": conversation.get("customer_name", ""),
                "state": conversation.get("state", "NUEVO"),
                "previous_queries": conversation.get("customer_needs", "")
            }

            # Formatear prompt
            prompt = CLASSIFY_TRIPATH_INTENT.format(
                message=message,
                customer_name=context["customer_name"] or "No proporcionado",
                state=context["state"],
                previous_queries=context["previous_queries"] or "Ninguna"
            )

            # Llamar LLM
            response = await self.llm_service.classify_with_prompt(
                prompt=prompt,
                response_format="json"
            )

            # Parsear respuesta
            if isinstance(response, str):
                result = json.loads(response)
            else:
                result = response

            self.log_action("LLM classification exitosa", {
                "intent": result.get("intent"),
                "confidence": result.get("confidence")
            })

            return result

        except Exception as e:
            self.log_error("Error en clasificación LLM, usando fallback", e)
            return self._fallback_keyword_classification(message)

    def _fallback_keyword_classification(self, message: str) -> Dict[str, Any]:
        """
        Clasificación por keywords si LLM falla.

        Complejidad: 7 (Media-Alta)
        """
        message_lower = message.lower()

        # Detectar inmueble
        if any(kw in message_lower for kw in self.routing_config["inmueble_keywords"]):
            return {
                "intent": "inmueble",
                "sub_intent": None,
                "confidence": 0.6,
                "entities": {},
                "reasoning": "Detectado por keywords (fallback)"
            }

        # Detectar departamento
        for dept, keywords in self.routing_config["departamento_keywords"].items():
            if any(kw in message_lower for kw in keywords):
                return {
                    "intent": "departamento",
                    "sub_intent": dept,
                    "confidence": 0.65,
                    "entities": {},
                    "reasoning": f"Detectado {dept} por keywords (fallback)"
                }

        # Detectar general
        if any(kw in message_lower for kw in self.routing_config["general_keywords"]):
            return {
                "intent": "general",
                "sub_intent": None,
                "confidence": 0.5,
                "entities": {},
                "reasoning": "Detectado por keywords generales (fallback)"
            }

        # Unclear
        return {
            "intent": "unclear",
            "sub_intent": None,
            "confidence": 0.3,
            "entities": {},
            "reasoning": "No se pudo clasificar (fallback)"
        }

    # ═══════════════════════════════════════════════════════════════
    # MÉTODOS HELPER (DRY - Don't Repeat Yourself)
    # ═══════════════════════════════════════════════════════════════

    def _empty_rag_result(self) -> Dict[str, Any]:
        """
        Helper: Retorna resultado RAG vacío estándar.

        Returns:
            Diccionario con estructura RAG vacía
        """
        return {
            "documents": [],
            "context": "",
            "phone_numbers": [],
            "rag_confidence": 0.0
        }

    def _format_greeting(self, customer_name: str, prefix: str = "") -> str:
        """
        Helper: Formatear saludo con nombre cliente.

        Args:
            customer_name: Nombre del cliente (puede estar vacío)
            prefix: Prefijo del mensaje (ej: "Hola", "Perfecto")

        Returns:
            Mensaje formateado con o sin nombre

        Examples:
            >>> self._format_greeting("Carlos", "Hola")
            "Hola, Carlos"
            >>> self._format_greeting("", "Perfecto")
            "Perfecto"
        """
        if customer_name:
            return f"{prefix}, {customer_name}" if prefix else customer_name
        return prefix

    def _build_response_data(
        self,
        routing_path: str,
        intent: str,
        **extra_data
    ) -> Dict[str, Any]:
        """
        Helper: Construcción estándar de data_updates.

        Args:
            routing_path: Camino de routing (ej: "CAMINO_1_INMUEBLE")
            intent: Intención clasificada (ej: "inmueble")
            **extra_data: Datos adicionales específicos del camino

        Returns:
            Diccionario con estructura estándar para data_updates
        """
        return {
            "routing_path": routing_path,
            "intent": intent,
            **extra_data
        }

    # ═══════════════════════════════════════════════════════════════
    # MÉTODOS DE RAG SEARCH
    # ═══════════════════════════════════════════════════════════════

    async def _search_rag_for_routing(
        self,
        user_message: str,
        intent: str,
        entities: Dict[str, Any],
        classification: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Búsqueda RAG obligatoria para routing.

        Returns:
            {
                "documents": List[Dict],
                "context": str,
                "phone_numbers": List[str],
                "rag_confidence": float
            }

        Complejidad: 8 (Media-Alta)
        """
        try:
            # Enriquecer query con contexto
            enriched_query = self._enrich_query_with_context(
                user_message, intent, entities
            )

            self.log_action("Query enriquecido", {"query": enriched_query[:100]})

            # Búsqueda RAG
            if not self.rag_system or not self.rag_system.initialized:
                self.log_action("RAG no disponible", {})
                return self._empty_rag_result()  # ✅ Usando helper

            # Obtener contexto
            context = self.rag_system.search_context(enriched_query, max_results=8)

            # Extraer números de teléfono del contexto
            phone_numbers = self._extract_phone_numbers_from_text(context)

            # Si intent es departamento, buscar en DEPARTMENT_CONTACTS también
            if intent == "departamento":
                sub_intent = classification.get("sub_intent")
                if sub_intent and sub_intent in DEPARTMENT_CONTACTS:
                    dept_phone = DEPARTMENT_CONTACTS[sub_intent]["phone"]
                    if dept_phone not in phone_numbers:
                        phone_numbers.append(dept_phone)

            return {
                "documents": [],  # RAG system actual no retorna docs estructurados
                "context": context,
                "phone_numbers": phone_numbers,
                "rag_confidence": 0.8 if context else 0.0
            }

        except Exception as e:
            self.log_error("Error en RAG search", e)
            return self._empty_rag_result()  # ✅ Usando helper

    def _enrich_query_with_context(
        self,
        query: str,
        intent: str,
        entities: Dict[str, Any]
    ) -> str:
        """
        Enriquecer query con contexto según intent.

        Ejemplos:
        - inmueble: "apartamento" → "apartamento cita visita proceso"
        - departamento: "reparación" → "reparación contacto teléfono"
        - general: "horarios" → "horarios atención empresa"
        """
        if intent == "inmueble":
            return f"{query} cita visita proceso agendar"
        elif intent == "departamento":
            sub = entities.get("department", "")
            return f"{query} contacto teléfono {sub} departamento"
        elif intent == "general":
            return f"{query} información empresa"
        else:
            return query

    def _extract_phone_numbers_from_text(self, text: str) -> List[str]:
        """
        Extraer números de teléfono colombianos del texto.

        Formatos soportados:
        - 321 123 4567
        - 321-123-4567
        - 3211234567

        Returns: Lista única de números encontrados
        Complejidad: 7 (Media)
        """
        if not text:
            return []

        matches = self.phone_regex.findall(text)

        # Limpiar y normalizar
        cleaned = []
        for match in matches:
            # Remover espacios y guiones
            clean = match.replace(" ", "").replace("-", "")
            if len(clean) == 10 and clean not in cleaned:
                cleaned.append(match)  # Mantener formato original

        return cleaned

    # ═══════════════════════════════════════════════════════════════
    # MÉTODOS DE ROUTING DECISION
    # ═══════════════════════════════════════════════════════════════

    def _determine_routing_path(
        self,
        intent: str,
        classification: Dict[str, Any],
        rag_result: Dict[str, Any],
        user_message: str
    ) -> str:
        """
        Decision tree para determinar camino de routing.

        Decision Matrix:
        - inmueble + confidence > 0.7 → CAMINO_1
        - departamento + has_phones → CAMINO_2
        - general + rag_context → CAMINO_3
        - unclear → UNCLEAR

        Complejidad: 6 (Media)
        """
        confidence = classification.get("confidence", 0.0)
        has_context = bool(rag_result.get("context"))
        has_phones = len(rag_result.get("phone_numbers", [])) > 0

        # CAMINO 1: Inmueble (búsqueda de propiedades)
        if intent == "inmueble" and confidence > 0.7:
            return "CAMINO_1_INMUEBLE"

        # CAMINO 2: Departamento (con números encontrados)
        if intent == "departamento":
            # Si encontramos números en RAG o en DEPARTMENT_CONTACTS
            sub_intent = classification.get("sub_intent")
            if has_phones or (sub_intent in DEPARTMENT_CONTACTS):
                return "CAMINO_2_DEPARTAMENTO"
            else:
                # Sin números, tratar como general
                return "CAMINO_3_GENERAL"

        # CAMINO 3: General (información corporativa)
        if intent == "general" and has_context:
            return "CAMINO_3_GENERAL"

        # UNCLEAR: No se pudo determinar camino claro
        if intent == "unclear" or confidence < 0.5:
            return "UNCLEAR"

        # Default: General
        return "CAMINO_3_GENERAL"

    # ═══════════════════════════════════════════════════════════════
    # HANDLERS DE CAMINOS
    # ═══════════════════════════════════════════════════════════════

    async def _handle_camino_1_inmueble(
        self,
        classification: Dict[str, Any],
        rag_result: Dict[str, Any],
        customer_name: str
    ) -> Dict[str, Any]:
        """
        CAMINO 1: Usuario busca inmuebles → Transfer a ReceptionAgent

        Flow: SupportAgent → ReceptionAgent → LeadsalesAgent → CRM

        Response: Mensaje personalizado + transfer metadata
        """
        entities = classification.get("entities", {})
        property_type = entities.get("property_type", "propiedad")
        location = entities.get("location", "")
        rag_context = rag_result.get("context", "")

        # ✅ Generar mensaje con LLM + contexto RAG (elimina hardcoding)
        if rag_context and self.llm_service and self.llm_service.api_client.initialized:
            try:
                # Prompt para generar mensaje personalizado con RAG
                prompt = f"""Genera un mensaje breve (2-3 líneas) de bienvenida para un usuario que busca {property_type}{' en ' + location if location else ''}.

Contexto desde documentos RAG:
{rag_context[:500]}

Cliente: {customer_name or 'usuario'}

Instrucciones:
- Mensaje corto y profesional
- Menciona que lo conectarás con asesores
- Usa información del contexto RAG si es relevante (ej: proceso de citas, requisitos)
- Tono cercano pero profesional
- No uses emojis
- Máximo 3 líneas"""

                message = await self.llm_service.classify_with_prompt(
                    prompt=prompt,
                    response_format="text"
                )

                self.log_action("CAMINO 1 con RAG+LLM", {
                    "property_type": property_type,
                    "location": location,
                    "rag_used": True,
                    "llm_generated": True
                })

            except Exception as e:
                self.log_error("Error generando mensaje con RAG+LLM, usando fallback", e)
                # Fallback: mensaje simple
                greeting = self._format_greeting(customer_name, "¡Perfecto")  # ✅ Usando helper
                message = (
                    f"{greeting}! "
                    f"Veo que buscas {property_type}. Te conectaré con nuestro equipo de asesores."
                )
        else:
            # Sin RAG o LLM: mensaje genérico
            greeting = self._format_greeting(customer_name, "¡Perfecto")  # ✅ Usando helper
            location_part = f" en {location}" if location else ""
            message = (
                f"{greeting}! "
                f"Veo que buscas {property_type}{location_part}. "
                f"Te voy a conectar con nuestro equipo de asesores que te ayudarán "
                f"a encontrar la mejor opción y agendar una cita de visita."
            )

            self.log_action("CAMINO 1 sin RAG", {
                "property_type": property_type,
                "location": location,
                "rag_used": False
            })

        return self.create_response(
            message,
            transfer_to="ReceptionAgent",
            data_updates=self._build_response_data(  # ✅ Usando helper
                routing_path="CAMINO_1_INMUEBLE",
                intent="inmueble",
                classification=json.dumps(classification, ensure_ascii=False),
                rag_context_used=bool(rag_context)
            )
        )

    async def _handle_camino_2_departamento(
        self,
        classification: Dict[str, Any],
        rag_result: Dict[str, Any],
        customer_name: str
    ) -> Dict[str, Any]:
        """
        CAMINO 2: Usuario necesita departamento específico → Extraer números

        Flow: SupportAgent → Extrae números de RAG → Responde con contactos → TRANSFERIDO

        Response: Mensaje + números de contacto
        """
        sub_intent = classification.get("sub_intent", "general")
        phone_numbers = rag_result.get("phone_numbers", [])

        # Si no hay números en RAG, usar DEPARTMENT_CONTACTS
        if not phone_numbers and sub_intent in DEPARTMENT_CONTACTS:
            dept_config = DEPARTMENT_CONTACTS[sub_intent]
            phone_numbers = [dept_config["phone"]]
            dept_name = dept_config["name"]
            dept_hours = dept_config["hours"]
        elif sub_intent in DEPARTMENT_CONTACTS:
            dept_config = DEPARTMENT_CONTACTS[sub_intent]
            dept_name = dept_config["name"]
            dept_hours = dept_config["hours"]
        else:
            dept_name = "el departamento correspondiente"
            dept_hours = "horario laboral"

        # Generar respuesta con helper
        if phone_numbers:
            phones_formatted = "\n".join([f"📞 {phone}" for phone in phone_numbers[:2]])
            greeting = self._format_greeting(customer_name, "Perfecto")  # ✅ Usando helper
            response = (
                f"{greeting}! "
                f"Para tu consulta sobre {sub_intent}, puedes comunicarte con:\n\n"
                f"{dept_name}\n"
                f"{phones_formatted}\n\n"
                f"Horario: {dept_hours}"
            )
        else:
            greeting = self._format_greeting(customer_name, "Entiendo")  # ✅ Usando helper
            response = (
                f"{greeting}. "
                f"Voy a transferir tu consulta a {dept_name}. "
                f"Un asesor se comunicará contigo muy pronto."
            )

        self.log_action("CAMINO 2 ejecutado", {
            "department": sub_intent,
            "phones_provided": len(phone_numbers)
        })

        # ✅ Estado TRANSFERIDO activa handoff humano (NUEVO_FLUJO_RAG_FIRST.md)
        return self.create_response(
            response,
            new_state="TRANSFERIDO",
            data_updates=self._build_response_data(  # ✅ Usando helper
                routing_path="CAMINO_2_DEPARTAMENTO",
                intent="departamento",
                sub_intent=sub_intent,
                phone_numbers=json.dumps(phone_numbers),
                handoff_reason=f"department_{sub_intent}"
            )
        )

    async def _handle_camino_3_general(
        self,
        user_message: str,
        rag_result: Dict[str, Any],
        customer_name: str
    ) -> Dict[str, Any]:
        """
        CAMINO 3: Información general → RAG responde directamente

        Flow: SupportAgent → RAG context → LLM genera respuesta → Usuario

        Response: Respuesta contextualizada con RAG
        """
        context = rag_result.get("context", "")

        if not context:
            # Sin contexto RAG, respuesta genérica
            response = (
                "Con mucho gusto paso tu información a nuestro equipo "
                "para ver cuál es la mejor manera de ayudarte."
            )
            return self.create_response(response)

        # Generar respuesta con LLM + contexto RAG
        try:
            # Usar LLM para generar respuesta natural
            if self.llm_service and self.llm_service.api_client.initialized:
                contextual_response = await self.llm_service.llm_generator.generate_contextual_response(
                    user_question=user_message,
                    context=context,
                    customer_name=customer_name
                )

                self.log_action("CAMINO 3 ejecutado con LLM", {
                    "context_length": len(context),
                    "llm_used": True
                })

                return self.create_response(
                    contextual_response,
                    new_state="SUPPORT_ACTIVE",
                    data_updates=self._build_response_data(  # ✅ Usando helper
                        routing_path="CAMINO_3_GENERAL",
                        intent="general",
                        rag_used=True,
                        llm_generated=True
                    )
                )
            else:
                # Fallback: contexto RAG directo
                response = f"{context}\n\n¿Hay algo más en lo que pueda ayudarte?"

                self.log_action("CAMINO 3 ejecutado sin LLM", {
                    "context_length": len(context),
                    "llm_used": False
                })

                return self.create_response(
                    response,
                    new_state="SUPPORT_ACTIVE",
                    data_updates=self._build_response_data(  # ✅ Usando helper
                        routing_path="CAMINO_3_GENERAL",
                        intent="general",
                        rag_used=True,
                        llm_generated=False
                    )
                )

        except Exception as e:
            self.log_error("Error generando respuesta CAMINO 3", e)
            # Fallback: contexto RAG directo
            response = f"{context}\n\n¿Hay algo más en lo que pueda ayudarte?"
            return self.create_response(response)

    async def _handle_unclear_intent(
        self,
        user_message: str,
        customer_name: str
    ) -> Dict[str, Any]:
        """
        Handler para intenciones no claras.

        Strategy: Mensaje educativo + invitación a especificar
        """
        name_part = f"{customer_name}, " if customer_name else ""

        response = (
            f"Hola{', ' + customer_name if customer_name else ''}! "
            f"Para ayudarte mejor, ¿podrías especificar tu consulta?\n\n"
            f"Puedo ayudarte con:\n"
            f"🏠 Búsqueda de inmuebles (compra/arriendo)\n"
            f"🔧 Reparaciones y mantenimiento\n"
            f"📄 Contratos y documentación\n"
            f"ℹ️ Información sobre la empresa"
        )

        self.log_action("UNCLEAR intent manejado", {})

        return self.create_response(
            response,
            data_updates={"routing_path": "UNCLEAR"}
        )