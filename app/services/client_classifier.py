"""
Sistema híbrido de clasificación de clientes.
Responsabilidad: Clasificar perfil y sofisticación usando reglas (fast path) + LLM (complex path).
"""
import logging
import re
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass

from app.services.llm_service import LLMService
from app.prompts.client_classification_prompts import (
    CLIENT_CLASSIFICATION_SYSTEM,
    CLIENT_CLASSIFICATION_USER
)

logger = logging.getLogger(__name__)


@dataclass
class ClientClassification:
    """Resultado de clasificación de cliente"""
    profile: str  # inversionista, arquitecto, ingeniero, etc.
    sophistication_level: str  # alto, medio, bajo
    confidence: float  # 0-1
    reasoning: str
    detected_keywords: list
    profession_explicit: bool  # True si mencionó explícitamente su profesión
    classification_method: str  # "rules" o "llm"
    cost_usd: float  # Costo de clasificación ($0 para reglas, ~$0.00008 para LLM)
    latency_ms: float  # Latencia de clasificación


class ClientClassifier:

    # Keywords para clasificación por reglas
    PROFILE_KEYWORDS = {
        "inversionista": {
            "high_confidence": [
                "inversion", "inversión", "invertir", "roi", "rentabilidad",
                "flujo de caja", "plusvalía", "arrendar para ganar",
                "portafolio", "múltiples propiedades"
            ],
            "medium_confidence": [
                "negocio", "ganancia", "alquilar", "rentar", "valorización"
            ]
        },
        "arquitecto": {
            "high_confidence": [
                "soy arquitecto", "arquitecta", "diseño arquitectónico",
                "planos", "remodelación", "espacios", "distribución",
                "metros cuadrados", "especificaciones técnicas"
            ],
            "medium_confidence": [
                "diseño", "estética", "acabados", "iluminación natural"
            ]
        },
        "ingeniero": {
            "high_confidence": [
                "soy ingeniero", "ingeniera", "estructura", "cimientos",
                "materiales de construcción", "análisis técnico", "sismorresistente"
            ],
            "medium_confidence": [
                "construcción", "calidad estructural", "normativa"
            ]
        },
        "corredor": {
            "high_confidence": [
                "soy corredor", "agente inmobiliario", "comisión",
                "cartera de clientes", "captación", "intermediario"
            ],
            "medium_confidence": []
        },
        "empresario": {
            "high_confidence": [
                "para mi empresa", "local comercial", "oficinas",
                "sede", "expansión empresarial", "punto de venta",
                "cadena de tiendas", "expandir mi cadena"
            ],
            "medium_confidence": [
                "negocio", "empresa", "comercial", "tienda", "cadena"
            ]
        },
        "familia": {
            "high_confidence": [
                "para mi familia", "mis hijos", "colegio cerca",
                "zona familiar", "seguridad familiar", "parques infantiles",
                "habitaciones para niños"
            ],
            "medium_confidence": [
                "familia", "hijos", "escuela", "colegio", "seguridad"
            ]
        }
    }

    # Keywords de sofisticación
    SOPHISTICATION_KEYWORDS = {
        "alto": [
            "análisis financiero", "tir", "van", "flujo de caja descontado",
            "estudio de mercado", "comparables", "plusvalía histórica",
            "proyección", "roi", "cap rate"
        ],
        "medio": [
            "he investigado", "he visto varias", "conozco la zona",
            "presupuesto definido", "requisitos claros"
        ],
        "bajo": [
            "primera vez", "no sé mucho", "información general",
            "estoy empezando", "ayuda por favor"
        ]
    }

    # Threshold de confianza para usar reglas vs LLM
    CONFIDENCE_THRESHOLD = 0.7  # Si confianza < 0.7, usar LLM

    def __init__(self, llm_service: Optional[LLMService] = None):
        """
        Inicializa clasificador.

        Args:
            llm_service: Servicio LLM (opcional, se crea si no se provee)
        """
        if llm_service:
            self.llm_service = llm_service
        else:
            self.llm_service = LLMService()
            self.llm_service.initialize()  # Inicializar LLM automáticamente

        # Estadísticas de uso
        self.stats = {
            "total_classifications": 0,
            "rule_based": 0,
            "llm_based": 0,
            "total_cost_usd": 0.0,
            "avg_latency_ms": 0.0
        }

        logger.info("✅ ClientClassifier inicializado (modo híbrido: reglas + LLM)")

    async def classify(
        self,
        customer_message: str,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> ClientClassification:
        """
        Clasifica perfil y sofisticación del cliente (híbrido con fallback).

        Args:
            customer_message: Mensaje del cliente
            additional_context: Contexto adicional (historial, metadata)

        Returns:
            ClientClassification con perfil, sofisticación y metadata
        """
        import time
        start_time = time.perf_counter()

        self.stats["total_classifications"] += 1

        try:
            # 1. Intentar clasificación por reglas (fast path)
            rule_result = self._classify_by_rules(customer_message)

            # 2. Si confianza es alta, usar resultado de reglas
            if rule_result[1] >= self.CONFIDENCE_THRESHOLD:
                profile, confidence, keywords, sophistication = rule_result

                latency_ms = (time.perf_counter() - start_time) * 1000
                self.stats["rule_based"] += 1

                logger.info(
                    f"✅ Clasificación por REGLAS: {profile} "
                    f"(confianza: {confidence:.2f}, latencia: {latency_ms:.1f}ms, costo: $0)"
                )

                return ClientClassification(
                    profile=profile,
                    sophistication_level=sophistication,
                    confidence=confidence,
                    reasoning=f"Clasificación por reglas basada en keywords: {', '.join(keywords[:3])}",
                    detected_keywords=keywords,
                    profession_explicit=self._is_profession_explicit(customer_message, profile),
                    classification_method="rules",
                    cost_usd=0.0,
                    latency_ms=latency_ms
                )

            # 3. Si confianza baja, usar LLM (slow path, pero preciso)
            logger.info(f"⚠️  Confianza reglas baja ({rule_result[1]:.2f}), usando LLM...")

            llm_result = await self._classify_by_llm(customer_message, additional_context or {})

            latency_ms = (time.perf_counter() - start_time) * 1000
            self.stats["llm_based"] += 1
            self.stats["total_cost_usd"] += llm_result.cost_usd

            logger.info(
                f"✅ Clasificación por LLM: {llm_result.profile} "
                f"(confianza: {llm_result.confidence:.2f}, latencia: {latency_ms:.1f}ms, "
                f"costo: ${llm_result.cost_usd:.6f})"
            )

            # Actualizar latency en resultado LLM
            llm_result.latency_ms = latency_ms

            return llm_result

        except Exception as e:
            # Fallback: usar resultado de reglas sin importar threshold
            logger.error(f"❌ Error en clasificación (LLM/parsing): {e}, usando fallback de reglas")

            profile, confidence, keywords, sophistication = rule_result
            latency_ms = (time.perf_counter() - start_time) * 1000

            return ClientClassification(
                profile=profile if confidence >= 0.3 else "desconocido",
                sophistication_level=sophistication,
                confidence=max(0.3, confidence * 0.7),  # Reducir por ser fallback
                reasoning=f"Fallback de reglas (LLM falló): {', '.join(keywords[:3]) if keywords else 'sin keywords'}",
                detected_keywords=keywords,
                profession_explicit=self._is_profession_explicit(customer_message, profile),
                classification_method="rules_fallback",
                cost_usd=0.0,
                latency_ms=latency_ms
            )

    def _classify_by_rules(
        self,
        customer_message: str
    ) -> Tuple[str, float, list, str]:

        message_lower = customer_message.lower().strip()

        # Mensajes vacíos o muy cortos → desconocido
        if len(message_lower) == 0:
            return ("desconocido", 0.2, [], "bajo")

        best_profile = "individual"
        best_confidence = 0.3  # Confianza base para "individual"
        best_keywords = []

        # Buscar coincidencias de keywords por perfil
        for profile, keyword_dict in self.PROFILE_KEYWORDS.items():
            high_conf_matches = [
                kw for kw in keyword_dict["high_confidence"]
                if kw in message_lower
            ]
            medium_conf_matches = [
                kw for kw in keyword_dict["medium_confidence"]
                if kw in message_lower
            ]

            # Calcular confianza
            if high_conf_matches:
                confidence = 0.9  # Alta confianza si hay match de high_confidence
                keywords_found = high_conf_matches
            elif len(medium_conf_matches) >= 2:
                confidence = 0.6  # Confianza media si hay 2+ medium_confidence
                keywords_found = medium_conf_matches
            elif medium_conf_matches:
                confidence = 0.4  # Confianza baja si hay 1 medium_confidence
                keywords_found = medium_conf_matches
            else:
                continue  # Sin matches para este perfil

            # Actualizar mejor match
            if confidence > best_confidence:
                best_profile = profile
                best_confidence = confidence
                best_keywords = keywords_found

        # Detectar nivel de sofisticación
        sophistication = self._detect_sophistication_rules(message_lower)

        return (best_profile, best_confidence, best_keywords, sophistication)

    def _detect_sophistication_rules(self, message_lower: str) -> str:
        """Detecta nivel de sofisticación por reglas"""
        for level, keywords in self.SOPHISTICATION_KEYWORDS.items():
            if any(kw in message_lower for kw in keywords):
                return level

        # Default: medio (si no hay keywords claros)
        return "medio"

    async def _classify_by_llm(
        self,
        customer_message: str,
        additional_context: Dict[str, Any]
    ) -> ClientClassification:
        #Se usa LLM para clasificar
        
        context_str = "\n".join([
            f"- {key}: {value}"
            for key, value in additional_context.items()
            if value
        ]) or "No hay contexto adicional disponible"

        # Construir prompt
        user_prompt = CLIENT_CLASSIFICATION_USER.format(
            customer_message=customer_message,
            additional_context=context_str
        )

        # Llamar a LLM
        result = await self.llm_service.classify_with_system_prompt(
            user_message=user_prompt,
            system_prompt=CLIENT_CLASSIFICATION_SYSTEM,
            expected_format="json"
        )

        # Parsear respuesta JSON
        try:
            import json
            classification_data = json.loads(result["response"])
            estimated_cost = 0.00008

            return ClientClassification(
                profile=classification_data.get("profile", "desconocido"),
                sophistication_level=classification_data.get("sophistication_level", "medio"),
                confidence=float(classification_data.get("confidence", 0.7)),
                reasoning=classification_data.get("reasoning", "Clasificación mediante LLM"),
                detected_keywords=classification_data.get("detected_keywords", []),
                profession_explicit=classification_data.get("profession_explicit", False),
                classification_method="llm",
                cost_usd=estimated_cost,
                latency_ms=0.0  # Se actualizará en classify()
            )

        except Exception as e:
            logger.error(f"❌ Error parseando respuesta LLM: {e}")

            # Fallback a clasificación default
            return ClientClassification(
                profile="desconocido",
                sophistication_level="medio",
                confidence=0.3,
                reasoning=f"Error en clasificación LLM: {str(e)}",
                detected_keywords=[],
                profession_explicit=False,
                classification_method="llm_error",
                cost_usd=0.00008,
                latency_ms=0.0
            )

    def _is_profession_explicit(self, message: str, profile: str) -> bool:

        message_lower = message.lower()

        explicit_patterns = {
            "inversionista": ["soy inversionista", "trabajo en inversiones"],
            "arquitecto": ["soy arquitecto", "soy arquitecta", "trabajo como arquitecto"],
            "ingeniero": ["soy ingeniero", "soy ingeniera", "trabajo como ingeniero"],
            "corredor": ["soy corredor", "agente inmobiliario", "trabajo en bienes raíces"],
            "empresario": ["soy empresario", "tengo una empresa", "dueño de"],
        }

        patterns = explicit_patterns.get(profile, [])
        return any(pattern in message_lower for pattern in patterns)

    def get_statistics(self) -> Dict[str, Any]:

        total = self.stats["total_classifications"]

        if total == 0:
            return self.stats

        return {
            **self.stats,
            "rule_based_percentage": (self.stats["rule_based"] / total) * 100,
            "llm_based_percentage": (self.stats["llm_based"] / total) * 100,
            "avg_cost_per_classification": self.stats["total_cost_usd"] / total if total > 0 else 0
        }