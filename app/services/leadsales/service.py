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

        self.is_demo_mode = self.client.is_demo_mode
        self.initialized = True  # Compatibilidad con código anterior

        logger.info("LeadsalesService inicializado (4 componentes cargados)")

    def initialize(self) -> bool:
        """
        Inicializa el servicio (backward compatibility).
        El servicio ya se inicializa en __init__, este método existe para compatibilidad.

        Returns:
            True si inicialización exitosa
        """
        return self.initialized

    def _score_lead(self, customer_needs: str, additional_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Calcula scoring de un lead (backward compatibility).
        Wrapper que delega a self.scoring.score_lead().

        Args:
            customer_needs: Descripción de necesidades del cliente
            additional_data: Metadata adicional opcional

        Returns:
            Dict con quality_score, interest_score, conversion_probability, tags, priority, confidence, reasoning
        """
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
        2. Metadata extraction (location, budget, etc.)
        3. Data enrichment (normalizacion, timestamps)
        4. Visualization generation (CRM preview)
        5. API call (produccion) o mock (demo)

        Args:
            customer_name: Nombre del cliente
            whatsapp: Numero de WhatsApp
            customer_needs: Necesidades del cliente
            additional_data: Metadata adicional opcional

        Returns:
            Dict con lead creado + visualizacion
        """
        logger.info(f"Creando lead: {customer_name} ({whatsapp})")

        # 1. Calcular scoring
        scoring_result = self.scoring.score_lead(customer_needs, additional_data)

        # 2. Extraer metadata
        metadata = self.metadata_extractor.extract_metadata(customer_needs, additional_data or {})

        # 3. Enriquecer datos
        enriched_data = self.metadata_extractor.enrich_customer_data(
            customer_name,
            whatsapp,
            customer_needs,
            scoring_result,
            metadata
        )

        # 4. Modo demo o produccion
        if self.is_demo_mode:
            return self._create_lead_demo(enriched_data)
        else:
            return await self._create_lead_production(enriched_data)

    async def _create_lead_production(self, enriched_data: Dict[str, Any]) -> Dict[str, Any]:
        """Crea lead en CRM real (modo produccion)"""
        # Preparar payload para API
        payload = {
            "customer_name": enriched_data["name"],
            "whatsapp": enriched_data["whatsapp"],
            "customer_needs": enriched_data["needs"],
            "source": "whatsapp_bot",
            "priority": enriched_data["priority"],
            "quality_score": enriched_data["quality_score"],
            "tags": enriched_data["tags"],
            "metadata": enriched_data["metadata"]
        }

        # Enviar a API
        api_response = await self.client.create_lead_api(payload)

        # Construir visualizacion
        preview = self.visualization.build_crm_preview(enriched_data)

        return {
            "lead_id": api_response["lead_id"],
            "status": "created",
            "customer_data": enriched_data,
            "crm_preview": preview,
            "mode": "production"
        }

    def _create_lead_demo(self, enriched_data: Dict[str, Any]) -> Dict[str, Any]:
        """Crea simulacion de lead (modo demo)"""
        # Construir simulacion completa
        simulation = self.visualization.build_demo_simulation(enriched_data)

        logger.info("Lead demo creado (simulacion)")

        return simulation

    async def get_lead(self, lead_id: str) -> Dict[str, Any]:
        """
        Obtiene lead desde CRM.

        Args:
            lead_id: ID del lead

        Returns:
            Dict con datos del lead
        """
        if self.is_demo_mode:
            raise RuntimeError("get_lead() no disponible en modo demo")

        return await self.client.get_lead_api(lead_id)

    async def update_lead(self, lead_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Actualiza lead en CRM.

        Args:
            lead_id: ID del lead
            update_data: Campos a actualizar

        Returns:
            Dict con lead actualizado
        """
        if self.is_demo_mode:
            raise RuntimeError("update_lead() no disponible en modo demo")

        return await self.client.update_lead_api(lead_id, update_data)

    async def list_leads(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Lista leads desde CRM.

        Args:
            filters: Filtros de busqueda

        Returns:
            Lista de leads
        """
        if self.is_demo_mode:
            raise RuntimeError("list_leads() no disponible en modo demo")

        return await self.client.list_leads_api(filters)

    async def close(self):
        """Cierra recursos"""
        await self.client.close()
