import google.generativeai as genai
from typing import Dict, Any, Optional, List
import structlog
from app.config import settings

logger = structlog.get_logger()

class LLMService:
    """
    Servicio de LLM usando API.

    Funcionalidades:
    - Generacion de respuestas contextuales
    - Clasificacion de intenciones
    - Respuestas con contexto RAG
    - Manejo de errores y reintentos
    """

    def __init__(self):
        """Inicializa el servicio LLM."""
        self.model = None
        self.initialized = False
        self.logger = logger.bind(component="llm_service")

    def initialize(self) -> bool:
        """
        Inicializa la conexion API.

        Returns:
            bool: True si la inicializacion fue exitosa
        """
        try:
            # Configurar API key
            genai.configure(api_key=settings.gemini_api_key)

            # Inicializar modelo
            self.model = genai.GenerativeModel(settings.gemini_model)

            self.initialized = True
            self.logger.info("Servicio LLM inicializado correctamente")
            return True

        except Exception as e:
            self.logger.error("Error inicializando servicio LLM", error=str(e))
            return False

    def classify_intention(self, message: str) -> Dict[str, Any]:
        """
        Clasifica la intencion de un mensaje usando la api.
        """
        if not self.initialized:
            self.logger.error("Servicio LLM no inicializado")
            return {"type": "error", "confidence": 0.0}

        prompt = f"""
        Clasifica el siguiente mensaje del usuario en una de estas categorias:

        CATEGORIAS:
        - "question": El usuario hace una pregunta o busca informacion
        - "need": El usuario expresa una necesidad, quiere contratar o comprar algo
        - "greeting": Solo es un saludo sin intencion clara
        - "unclear": El mensaje no es claro o no encaja en las otras categorias

        MENSAJE: "{message}"

        Responde SOLO con un JSON en este formato:
        {{"type": "categoria", "confidence": 0.8, "reasoning": "breve explicacion"}}
        """

        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=settings.gemini_temperature,
                    max_output_tokens=200
                )
            )

            # Parsear respuesta JSON
            import json
            result = json.loads(response.text.strip())

            self.logger.info(
                "Clasificacion de intencion completada",
                message_preview=message[:50],
                classification=result.get("type"),
                confidence=result.get("confidence")
            )

            return result

        except Exception as e:
            self.logger.error("Error clasificando intencion", error=str(e))
            return {"type": "error", "confidence": 0.0, "reasoning": str(e)}

    def generate_contextual_response(
        self,
        user_question: str,
        context: str,
        customer_name: Optional[str] = None
    ) -> str:
        """
        Genera una respuesta contextual usando RAG.
        """
        if not self.initialized:
            self.logger.error("Servicio LLM no inicializado")
            return "Lo siento, el servicio no esta disponible en este momento."

        # Preparar prompt con contexto
        customer_greeting = f", {customer_name}" if customer_name else ""

        prompt = f"""
        Eres un asistente virtual experto y amigable. Responde a la pregunta del usuario usando SOLO la informacion del contexto proporcionado.

        CONTEXTO DISPONIBLE:
        {context}

        PREGUNTA DEL USUARIO: "{user_question}"

        INSTRUCCIONES:
        - Responde de manera clara y concisa
        - Usa SOLO informacion del contexto
        - Si el contexto no contiene la informacion, di que no tienes esa informacion especifica
        - Manten un tono profesional pero amigable
        - Incluye el saludo al cliente si se proporciono su nombre
        - Al final, pregunta si necesita algo mas

        RESPUESTA:
        """

        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=settings.gemini_temperature,
                    max_output_tokens=settings.gemini_max_tokens
                )
            )

            generated_response = response.text.strip()

            # Agregar saludo personalizado si tenemos nombre
            if customer_name:
                generated_response = f"Hola{customer_greeting}!\n\n{generated_response}"

            self.logger.info(
                "Respuesta contextual generada",
                question_preview=user_question[:50],
                response_length=len(generated_response),
                context_used=len(context) > 0
            )

            return generated_response

        except Exception as e:
            self.logger.error("Error generando respuesta contextual", error=str(e))
            return f"Lo siento{customer_greeting}, ocurrio un error procesando tu consulta. Un especialista se pondra en contacto contigo pronto."

    def generate_follow_up_options(self, user_question: str, response: str) -> List[str]:
        """
        Genera opciones de seguimiento para la conversacion.
        """
        if not self.initialized:
            return []

        prompt = f"""
        Basado en esta conversacion, genera 3 preguntas de seguimiento que el usuario podria hacer.

        PREGUNTA ORIGINAL: "{user_question}"
        RESPUESTA DADA: "{response}"

        Genera 3 preguntas cortas y relevantes que el usuario podria hacer a continuacion.
        Responde SOLO con un JSON array:
        ["pregunta 1", "pregunta 2", "pregunta 3"]
        """

        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=300
                )
            )

            import json
            follow_ups = json.loads(response.text.strip())

            return follow_ups if isinstance(follow_ups, list) else []

        except Exception as e:
            self.logger.error("Error generando opciones de seguimiento", error=str(e))
            return []

    def health_check(self) -> Dict[str, Any]:
        """
        Verifica la salud del servicio LLM.
        """
        if not self.initialized:
            return {"status": "unhealthy", "reason": "Servicio no inicializado"}

        try:
            # Prueba simple de generacion
            test_response = self.model.generate_content(
                "Di solo 'OK'",
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=10
                )
            )

            return {
                "status": "healthy",
                "model": settings.gemini_model,
                "test_response_length": len(test_response.text)
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "reason": f"Error en prueba: {str(e)}"
            }

# Singleton para uso global
llm_service = LLMService()