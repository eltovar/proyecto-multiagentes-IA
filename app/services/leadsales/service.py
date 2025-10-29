"""
Servicio orquestador de Leadsales CRM.
Responsabilidad: Coordinar client, scoring, metadata y visualization.
"""
import logging
from typing import Dict, Any, Optional, List

from .client import LeadsalesClient
from .scoring import LeadScoringIntegrator
from .metadata import LeadMetadataExtractor
from .visualization import CRMVisualizationBuilder
from app.services.client_classifier import ClientClassifier, ClientClassification
from app.services.lead_analyzer import LeadAnalyzer, LeadAnalysis

logger = logging.getLogger(__name__)


class LeadsalesService:
    """
    Servicio principal de Leadsales CRM.
    Orquesta componentes especializados para crear/gestionar leads.
    """

    def __init__(self):
        """Inicializa servicio con componentes especializados"""
        self.client = LeadsalesClient()
        self.scoring = LeadScoringIntegrator()
        self.metadata_extractor = LeadMetadataExtractor()
        self.visualization = CRMVisualizationBuilder()
        self.client_classifier = ClientClassifier()
        self.lead_analyzer = LeadAnalyzer()  # ✅ NUEVO (PR005)

        self.is_demo_mode = self.client.is_demo_mode
        self.initialized = True  # Compatibilidad con código anterior

        logger.info("✅ LeadsalesService inicializado (6 componentes cargados)")

    def initialize(self) -> bool:
        """
        Inicializa el servicio (backward compatibility).
        El servicio ya se inicializa en __init__, este método existe para compatibilidad.

        Returns:
            True si inicialización exitosa
        """
        return self.initialized

    def _score_lead(self, customer_needs: str, additional_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Calcula scoring de un lead (backward compatibility) """
        return self.scoring.score_lead(customer_needs, additional_data)

    async def create_lead(
        self,
        customer_name: str,
        whatsapp: str,
        customer_needs: str,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Crea lead en CRM (produccion) o simulacion (demo).

        Orquesta:
        1. Scoring (quality, tags, priority)
        2. Client classification (profile, sophistication)
        3. Metadata extraction (location, budget, etc.)
        4. Lead analysis (composite score, insights, recommendations) ✅ NUEVO
        5. Data enrichment (normalización, timestamps)
        6. Visualization generation (CRM preview enriquecido) ✅ MEJORADO
        7. API call (producción) o mock (demo)
        """
        logger.info(f"📝 Creando lead: {customer_name} ({whatsapp})")

        # 1. Calcular scoring
        scoring_result = self.scoring.score_lead(customer_needs, additional_data)

        # 2. Clasificar cliente
        classification_result = await self.client_classifier.classify(
            customer_message=customer_needs,
            additional_context=additional_data
        )

        # 3. Extraer metadata
        metadata = self.metadata_extractor.extract_metadata(customer_needs, additional_data or {})

        # 4. Analizar lead (NUEVO) ✅
        lead_analysis = self.lead_analyzer.analyze(
            scoring_result=scoring_result,
            classification_result=classification_result.__dict__ if hasattr(classification_result, '__dict__') else classification_result,
            metadata=metadata
        )

        logger.info(
            f"🎯 Lead analizado: Segment={lead_analysis.lead_segment}, "
            f"Composite Score={lead_analysis.composite_score:.1f}, "
            f"Conversion Prob={lead_analysis.conversion_probability:.2f}"
        )

        # 5. Enriquecer datos (ahora incluye análisis completo) ✅
        enriched_data = self.metadata_extractor.enrich_customer_data(
            customer_name,
            whatsapp,
            customer_needs,
            scoring_result,
            metadata,
            classification_result,
            lead_analysis  # ✅ NUEVO parámetro
        )

        # 6. Modo demo o produccion
        if self.is_demo_mode:
            return self._create_lead_demo(enriched_data, lead_analysis)
        else:
            return await self._create_lead_production(enriched_data, lead_analysis)

    async def _create_lead_production(
        self,
        enriched_data: Dict[str, Any],
        lead_analysis: LeadAnalysis  # ✅ NUEVO parámetro
    ) -> Dict[str, Any]:
        """Crea lead en CRM real (modo produccion)"""
        # Preparar payload para API (incluye análisis)
        payload = {
            "customer_name": enriched_data["name"],
            "whatsapp": enriched_data["whatsapp"],
            "customer_needs": enriched_data["needs"],
            "source": "whatsapp_bot",

            # Scoring
            "priority": lead_analysis.priority,  # ✅ Prioridad ajustada por perfil
            "priority_numeric": lead_analysis.priority_numeric,  # ✅ NUEVO
            "quality_score": enriched_data["quality_score"],
            "composite_score": lead_analysis.composite_score,  # ✅ NUEVO
            "tags": enriched_data["tags"],

            # Classification
            "profile": lead_analysis.profile,
            "sophistication_level": lead_analysis.sophistication_level,

            # Analysis
            "lead_segment": lead_analysis.lead_segment,  # ✅ NUEVO
            "conversion_probability": lead_analysis.conversion_probability,  # ✅ NUEVO
            "estimated_value": lead_analysis.estimated_value,  # ✅ NUEVO

            # Metadata
            "metadata": enriched_data["metadata"]
        }

        # Enviar a API
        api_response = await self.client.create_lead_api(payload)

        # Construir visualizacion enriquecida
        preview = self.visualization.build_crm_preview(
            enriched_data,
            lead_analysis  # ✅ NUEVO parámetro
        )

        return {
            "lead_id": api_response["lead_id"],
            "status": "created",
            "customer_data": enriched_data,
            "lead_analysis": lead_analysis.__dict__,  # ✅ NUEVO
            "crm_preview": preview,
            "mode": "production"
        }

    def _create_lead_demo(
        self,
        enriched_data: Dict[str, Any],
        lead_analysis: LeadAnalysis  # ✅ NUEVO parámetro
    ) -> Dict[str, Any]:
        """Crea simulacion de lead (modo demo) con análisis enriquecido"""
        # Construir simulacion completa con análisis
        simulation = self.visualization.build_demo_simulation(
            enriched_data,
            lead_analysis  # ✅ NUEVO parámetro
        )

        logger.info("✅ Lead demo creado (simulacion enriquecida)")

        return simulation

    async def get_lead(self, lead_id: str) -> Dict[str, Any]:
        """ Obtiene lead desde CRM. """
        if self.is_demo_mode:
            raise RuntimeError("get_lead() no disponible en modo demo")

        return await self.client.get_lead_api(lead_id)

    async def update_lead(self, lead_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """ Actualiza lead en CRM. """
        if self.is_demo_mode:
            raise RuntimeError("update_lead() no disponible en modo demo")

        return await self.client.update_lead_api(lead_id, update_data)

    async def list_leads(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """ Lista leads desde CRM """
        if self.is_demo_mode:
            raise RuntimeError("list_leads() no disponible en modo demo")

        return await self.client.list_leads_api(filters)

    async def close(self):
        """Cierra recursos"""
        await self.client.close()
