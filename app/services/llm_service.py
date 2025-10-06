import openai
import asyncio
import json
import time
from typing import Dict, Any, List, Optional
from app.config import settings
from .llm_classifier import LLMClassifier
from .llm_generator import LLMGenerator
from app.utils.error_logger import log_error, log_info

class LLMAPIClient:

    def __init__(self):
        self.client = None
        self.initialized = False

    def initialize(self) -> bool:
        try:
            self.client = openai.AsyncOpenAI( # permite que las llamadas al LLM no bloqueen el thread principal de la aplicación
                api_key=settings.openai_api_key
            )
            self.initialized = True
            log_info("LLMService", "OpenAI API inicializada correctamente")
            return True
        except Exception as e:
            log_error("LLMService", "Error inicializando OpenAI API", e)
            return False

class LLMService:

    def __init__(self):
        self.api_client = LLMAPIClient()
        self.classifier = None
        self.generator = None

    def initialize(self) -> bool:
        if not self.api_client.initialize():
            return False

        self.classifier = LLMClassifier(self.api_client)
        self.generator = LLMGenerator(self.api_client)
        return True

    def classify_intention(self, message: str) -> Dict[str, Any]:
        if not self.classifier:
            return {"type": "error", "confidence": 0.0}
        return self.classifier.classify_intention(message)

    def generate_contextual_response(
        self,
        user_question: str,
        context: str,
        customer_name: Optional[str] = None
    ) -> str:
        if not self.generator:
            return "Servicio no disponible"
        return self.generator.generate_contextual_response(user_question, context, customer_name)

    def generate_follow_up_options(self, user_question: str, response: str) -> List[str]:
        if not self.generator:
            return []
        return self.generator.generate_follow_up_options(user_question, response)

    def process_user_message(self, message: str, context: str = "") -> Dict[str, Any]:
        classification = self.classify_intention(message)

        result = {
            "classification": classification,
            "processed": True
        }

        if context and classification.get("type") == "question":
            response = self.generate_contextual_response(message, context)
            follow_ups = self.generate_follow_up_options(message, response)
            result.update({
                "response": response,
                "follow_ups": follow_ups
            })

        return result

    async def classify_intent(self, classification_prompt: str) -> str:
        """
        Clasificación específica para reception_agent: retorna 'pregunta' o 'necesidad'
        Migrado a OpenAI con mayor precisión.
        """
        if not self.api_client.initialized:
            return "necesidad"  # Fallback por defecto

        try:
            response = await self.api_client.client.chat.completions.create(
                model=settings.llm_model_name,
                messages=[
                    {"role": "system", "content": "Eres un clasificador preciso. Responde SOLO con 'pregunta' o 'necesidad'."},
                    {"role": "user", "content": classification_prompt}
                ],
                temperature=0.1,
                max_tokens=10
            )

            result = response.choices[0].message.content.strip().lower()

            # Validar que la respuesta sea correcta
            if result in ["pregunta", "necesidad"]:
                return result
            else:
                # Fallback: si contiene palabras clave de pregunta
                if any(word in classification_prompt.lower() for word in ["qué", "cómo", "cuándo", "dónde", "por qué", "cuál", "?"]):
                    return "pregunta"
                else:
                    return "necesidad"

        except Exception as e:
            log_error("LLMService", "Error en classify_intent", e)
            return "necesidad"  # Fallback por defecto

    async def classify_with_prompt(
        self,
        prompt: str,
        response_format: str = "json"
    ) -> Dict[str, Any] | str:
       
        if not self.api_client.initialized:
            log_error("LLMService", "API no inicializada en classify_with_prompt")
            raise RuntimeError("LLM API no inicializada")

        start_time = time.time()

        try:
            # Llamada a OpenAI con timeout
            response = await asyncio.wait_for(
                self.api_client.client.chat.completions.create(
                    model=settings.llm_model_name,
                    messages=[
                        {
                            "role": "system",
                            "content": "Eres un clasificador experto de intenciones. Responde SIEMPRE en formato JSON válido."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    response_format={"type": "json_object"} if response_format == "json" else None,
                    temperature=0.3,
                    max_tokens=500
                ),
                timeout=3.0  # Timeout de 3 segundos
            )

            # Extraer contenido
            content = response.choices[0].message.content.strip()

            # Calcular tiempo
            duration_ms = int((time.time() - start_time) * 1000)

            # Parsear según formato solicitado
            if response_format == "json":
                result = json.loads(content)

                # Validar estructura mínima esperada
                if "intent" not in result or "confidence" not in result:
                    log_error("LLMService", f"Respuesta JSON incompleta: {content[:100]}")
                    raise ValueError("Respuesta LLM sin campos requeridos (intent, confidence)")

                log_info(
                    "LLMService",
                    f"classify_with_prompt: {duration_ms}ms | Intent: {result['intent']} | Confidence: {result.get('confidence', 0):.2f}"
                )

                return result
            else:
                log_info("LLMService", f"classify_with_prompt (text): {duration_ms}ms")
                return content

        except asyncio.TimeoutError:
            duration_ms = int((time.time() - start_time) * 1000)
            log_error("LLMService", f"Timeout después de {duration_ms}ms en classify_with_prompt")
            raise

        except json.JSONDecodeError as e:
            log_error("LLMService", f"JSON inválido de LLM: {content[:100]}", e)
            raise

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            log_error("LLMService", f"Error en classify_with_prompt después de {duration_ms}ms", e)
            raise

    async def classify_intent_and_extract_entities(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        
        if not self.api_client.initialized:
            log_error("LLMService", "API no inicializada, usando fallback")
            return self._fallback_classification(message)

        start_time = time.time()

        try:
            # Importar prompt centralizado
            from app.prompts.extraction_prompts import EXTRACT_INTENT_AND_ENTITIES

            # Preparar contexto
            context_str = json.dumps(context) if context else "{}"

            # Construir prompt
            prompt = EXTRACT_INTENT_AND_ENTITIES.format(
                message=message,
                context=context_str
            )

            # Llamar a OpenAI con timeout
            response = await asyncio.wait_for(
                self.api_client.client.chat.completions.create(
                    model=settings.llm_model_name,
                    messages=[
                        {
                            "role": "system",
                            "content": "Eres un clasificador experto de intenciones inmobiliarias. Responde SIEMPRE en formato JSON válido."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.3,
                    max_tokens=300
                ),
                timeout=3.0  # Timeout de 3 segundos
            )

            # Parsear respuesta
            result = json.loads(response.choices[0].message.content.strip())

            # Calcular tiempo de respuesta
            duration_ms = int((time.time() - start_time) * 1000)

            # Logging estructurado
            log_info(
                "LLMService",
                f"classify_intent_and_extract_entities: {duration_ms}ms | Intent: {result.get('intent')} | Confidence: {result.get('confidence'):.2f}"
            )

            # Validar estructura mínima
            if "intent" not in result or "confidence" not in result:
                log_error("LLMService", "Respuesta LLM incompleta, usando fallback")
                return self._fallback_classification(message)

            return result

        except asyncio.TimeoutError:
            duration_ms = int((time.time() - start_time) * 1000)
            log_error("LLMService", f"Timeout después de {duration_ms}ms, usando fallback")
            return self._fallback_classification(message)

        except json.JSONDecodeError as e:
            log_error("LLMService", f"Error parseando JSON de LLM: {e}", e)
            return self._fallback_classification(message)

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            log_error("LLMService", f"Error en classify_intent_and_extract_entities después de {duration_ms}ms", e)
            return self._fallback_classification(message)

    def _fallback_classification(self, message: str) -> Dict[str, Any]:
        
        msg_lower = message.lower()

        # Inicializar resultado base
        result = {
            "nombre": None,
            "intent": "unclear",
            "confidence": 0.5,
            "entities": {
                "property_type": None,
                "location": None,
                "budget": None,
                "rooms": None,
                "bathrooms": None,
                "urgency": None,
                "current_situation": None
            },
            "reasoning": "Clasificación por fallback (LLM no disponible)"
        }

        # Detectar intención por keywords

        # SOPORTE
        support_keywords = ["problema", "ayuda", "error", "reparacion", "dañado", "arreglar"]
        if any(kw in msg_lower for kw in support_keywords):
            result["intent"] = "support"
            result["confidence"] = 0.65
            result["reasoning"] = "Detectado por keywords de soporte"
            return result

        # BÚSQUEDA DE PROPIEDAD
        property_keywords = ["busco", "apartamento", "casa", "arriendo", "comprar", "venta", "inmueble"]
        if any(kw in msg_lower for kw in property_keywords):
            result["intent"] = "property_search"
            result["confidence"] = 0.6
            result["reasoning"] = "Detectado por keywords de búsqueda de propiedad"

            # Intentar extraer tipo de propiedad
            if "apartamento" in msg_lower or "apto" in msg_lower:
                result["entities"]["property_type"] = "apartamento"
            elif "casa" in msg_lower:
                result["entities"]["property_type"] = "casa"
            elif "local" in msg_lower:
                result["entities"]["property_type"] = "local comercial"

            return result

        # BÚSQUEDA DE EMPLEO
        job_keywords = ["trabajo", "empleo", "vacante", "aplicar", "cv", "hoja de vida"]
        if any(kw in msg_lower for kw in job_keywords):
            result["intent"] = "job"
            result["confidence"] = 0.65
            result["reasoning"] = "Detectado por keywords de búsqueda de empleo"
            return result

        # SOLICITUD DE LLAMADA
        call_keywords = ["llamar", "llamen", "telefono", "hablar"]
        if any(kw in msg_lower for kw in call_keywords):
            result["intent"] = "call_request"
            result["confidence"] = 0.6
            result["reasoning"] = "Detectado por keywords de solicitud de llamada"
            return result

        # SALUDO
        greeting_keywords = ["hola", "buenos dias", "buenas tardes", "buenas noches", "saludos"]
        if any(kw in msg_lower for kw in greeting_keywords):
            result["intent"] = "greeting"
            result["confidence"] = 0.6
            result["reasoning"] = "Detectado por keywords de saludo"

            # Intentar extraer nombre simple con regex básico
            import re
            name_patterns = [
                r"soy\s+([A-Za-záéíóúñ]+)",
                r"me\s+llamo\s+([A-Za-záéíóúñ\s]+)",
                r"mi\s+nombre\s+es\s+([A-Za-záéíóúñ\s]+)"
            ]
            for pattern in name_patterns:
                match = re.search(pattern, message, re.IGNORECASE)
                if match:
                    result["nombre"] = match.group(1).strip().title()
                    break

            return result

        # Si no coincide con nada, mantener "unclear"
        result["intent"] = "unclear"
        result["confidence"] = 0.5
        result["reasoning"] = "Mensaje ambiguo, sin keywords reconocidos"

        return result

    def health_check(self) -> Dict[str, Any]:
        if not self.api_client.initialized:
            return {"status": "unhealthy", "reason": "API no inicializada"}

        try:
            # Note: Health check simplified for OpenAI
            return {
                "status": "healthy",
                "model": settings.llm_model_name,
                "provider": "OpenAI",
                "modules": {"classifier": "ok", "generator": "ok"}
            }
        except Exception as e:
            return {"status": "unhealthy", "reason": str(e)}

llm_service = LLMService()