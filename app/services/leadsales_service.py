"""Servicio de Leadsales CRM.
    Creacion de leads y trasferencia a asesores humanos
"""

from typing import Dict, Any, Optional, List
from app.services.leadsales_client import LeadsalesClient
from app.config import settings

class LeadsalesService:
    """
    Usa LeadsalesClient para toda la logica HTTP.
    """

    def __init__(self):
        self.client = LeadsalesClient()
        self.initialized = False

    def initialize(self) -> bool:
        """Inicializa el servicio verificando configuracion"""
        try:
            # Verificar que el cliente tenga configuracion
            if not self.client.api_url or not self.client.api_token:
                print("[LeadsalesService] Configuracion incompleta")
                return False

            self.initialized = True
            print("[LeadsalesService] Servicio inicializado correctamente")
            return True

        except Exception as e:
            print(f"[LeadsalesService] Error inicializando: {e}")
            return False

    async def create_lead(
        self,
        customer_name: str,
        whatsapp_id: str,
        customer_needs: str,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Crea lead usando cliente HTTP"""
        if not self.initialized:
            print("[LeadsalesService] Servicio no inicializado")
            return {"success": False, "error": "Servicio no inicializado"}

        # DEMO MODE DETECTION
        if self._is_demo_mode():
            return await self._create_mock_lead(customer_name, whatsapp_id, customer_needs, additional_data)

        # Preparar datos del lead
        lead_data = {
            "name": customer_name,
            "whatsapp_id": whatsapp_id,
            "phone": whatsapp_id,
            "needs": customer_needs,
            "source": "WhatsApp_Multiagent_Bot",
            "status": "nuevo",
            "priority": "normal",
            "created_by": "sistema_multiagente"
        }

        # Agregar datos adicionales
        if additional_data:
            lead_data.update(additional_data)

        # Enviar via cliente
        result = await self.client.post_lead(lead_data)

        # Manejar lead duplicado
        if not result["success"] and result.get("code") == "DUPLICATE":
            existing_lead = await self.client.get_lead(whatsapp_id)
            if existing_lead:
                return {
                    "success": True,
                    "lead_id": existing_lead.get("id"),
                    "data": existing_lead,
                    "already_exists": True
                }

        return result

    async def update_lead_status(self, lead_id: str, new_status: str, notes: Optional[str] = None) -> bool:
        """Actualiza estado del lead"""
        if not self.initialized:
            return False

        update_data = {"status": new_status}
        if notes:
            update_data["notes"] = notes

        return await self.client.update_lead(lead_id, update_data)

    async def assign_advisor(self, lead_id: str, advisor_criteria: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Asigna asesor especializado al lead"""
        if not self.initialized:
            return {"success": False, "error": "Servicio no inicializado"}

        return await self.client.assign_advisor(lead_id, advisor_criteria)

    async def health_check(self) -> Dict[str, Any]:
        """Verifica salud del servicio"""
        if not self.initialized:
            return {"status": "unhealthy", "reason": "Servicio no inicializado"}

        return await self.client.health_check()

    def _is_demo_mode(self) -> bool:
        """Detecta si está en modo demo por token de prueba"""
        demo_indicators = [
            "test_token", "demo_token", "mock_token",
            "https://api.leadsales.test/", "localhost"
        ]
        api_url = settings.leadsales_api_url.lower()
        api_token = settings.leadsales_api_token.lower()

        return any(indicator in api_url or indicator in api_token
                  for indicator in demo_indicators)

    async def _create_mock_lead(self, customer_name: str, whatsapp_id: str,
                               customer_needs: str, additional_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simula creación exitosa de lead con metadata rica y visualización CRM completa"""
        import uuid
        import time

        mock_lead_id = f"DEMO-{uuid.uuid4().hex[:8]}"

        # ACCIÓN 3.1-3.2: Enriquecimiento completo de metadata
        enriched_metadata = self._extract_rich_metadata(customer_needs, additional_data or {})

        return {
            "success": True,
            "lead_id": mock_lead_id,
            "demo_mode": True,
            "customer_data": {
                "name": customer_name,
                "whatsapp": whatsapp_id,
                "needs": customer_needs,
                "quality_score": self._calculate_demo_quality_score(customer_needs),
                "tags": self._generate_demo_tags(customer_needs, additional_data),
                "priority": self._determine_demo_priority(customer_needs),
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                # METADATA RICA del flujo de 10 pasos
                **enriched_metadata
            },
            "crm_simulation": self._generate_crm_preview(customer_name, customer_needs),
            # ACCIÓN 5.1-5.5: Simulación visual completa
            "visual_crm_simulation": self._generate_visual_crm_simulation(customer_name, customer_needs, enriched_metadata),
            "filtro_inteligente": self._determine_filtro(customer_needs, enriched_metadata),
            "asignacion_inteligente": self._generate_smart_assignment(customer_needs, enriched_metadata),
            "tabla_comparativa": self._generate_comparative_table(customer_needs, enriched_metadata)
        }

    def _calculate_demo_quality_score(self, needs: str) -> int:
        """Calcula score de calidad basado en keywords"""
        quality_keywords = {
            "high": ["comprar", "vender", "presupuesto", "millones", "urgente", "casa", "apartamento"],
            "medium": ["arrendar", "alquilar", "busco", "necesito", "zona"],
            "low": ["información", "consulta", "pregunta"]
        }

        needs_lower = needs.lower()
        high_score = sum(2 for keyword in quality_keywords["high"] if keyword in needs_lower)
        medium_score = sum(1 for keyword in quality_keywords["medium"] if keyword in needs_lower)

        total_score = min(100, max(30, (high_score * 20) + (medium_score * 10) + 40))
        return total_score

    def _generate_demo_tags(self, needs: str, additional_data: Dict[str, Any]) -> List[str]:
        """Genera tags automáticas para el CRM"""
        tags = []
        needs_lower = needs.lower()

        # Tags por tipo transacción
        if any(word in needs_lower for word in ["comprar", "compra"]):
            tags.append("COMPRA")
        if any(word in needs_lower for word in ["vender", "venta"]):
            tags.append("VENTA")
        if any(word in needs_lower for word in ["arrendar", "arriendo"]):
            tags.append("ARRIENDO")

        # Tags por tipo propiedad
        if "casa" in needs_lower:
            tags.append("CASA")
        if any(word in needs_lower for word in ["apartamento", "apto"]):
            tags.append("APARTAMENTO")

        # Tags por urgencia/presupuesto
        if any(word in needs_lower for word in ["urgente", "rápido", "pronto"]):
            tags.append("URGENTE")
        if any(word in needs_lower for word in ["millones", "presupuesto"]):
            tags.append("PRESUPUESTO_DEFINIDO")

        # Tags por información adicional
        if additional_data and additional_data.get("tiene_solicitud_libertador"):
            tags.append("LIBERTADOR_APROBADO")

        return tags[:5]  # Máximo 5 tags

    def _determine_demo_priority(self, needs: str) -> str:
        """Determina prioridad del lead para demo"""
        needs_lower = needs.lower()

        if any(word in needs_lower for word in ["urgente", "rápido", "ya", "inmediato"]):
            return "ALTA - Contacto inmediato"
        elif any(word in needs_lower for word in ["presupuesto", "millones", "definido"]):
            return "MEDIA-ALTA - Contacto 24h"
        elif any(word in needs_lower for word in ["información", "consulta"]):
            return "MEDIA - Contacto 48h"
        else:
            return "MEDIA - Contacto 24-48h"

    def _extract_rich_metadata(self, needs: str, additional_data: Dict[str, Any]) -> Dict[str, Any]:
        """ACCIÓN 3.1-3.2: Extrae metadata rica del flujo de 10 pasos"""
        metadata = {
            # Información del flujo de recepción (mantener keys originales para consistencia)
            "tiene_contrato_inmobiliaria": additional_data.get("tiene_contrato_inmobiliaria", "No especificado"),
            "inmobiliaria_actual": additional_data.get("inmobiliaria_actual", "Ninguna"),
            "tiene_solicitud_libertador": additional_data.get("tiene_solicitud_libertador", "No especificado"),
            "fecha_necesidad": additional_data.get("fecha_necesidad", "No especificada"),

            # Análisis inteligente del texto
            "tipo_transaccion": self._extract_transaction_type(needs),
            "tipo_propiedad": self._extract_property_type(needs),
            "zona_interes": self._extract_zone_interest(needs),
            "presupuesto_estimado": self._extract_budget_range(needs),
            "urgencia_nivel": self._extract_urgency_level(needs),
            "habitaciones_deseadas": self._extract_room_count(needs),

            # Metadatos de calidad
            "lead_quality": additional_data.get("lead_quality", "high"),
            "capture_method": additional_data.get("capture_method", "conversational_ai"),
            "information_completeness": additional_data.get("information_completeness", "complete"),
            "conversion_agent": additional_data.get("conversion_agent", "LeadsalesAgent"),
            "customer_engagement": additional_data.get("customer_engagement", "active")
        }

        return metadata

    def _extract_transaction_type(self, needs: str) -> str:
        """Extrae tipo de transacción del texto"""
        needs_lower = needs.lower()
        if any(word in needs_lower for word in ["comprar", "compra", "adquirir"]):
            return "Compra"
        elif any(word in needs_lower for word in ["vender", "venta"]):
            return "Venta"
        elif any(word in needs_lower for word in ["arrendar", "arriendo", "alquilar"]):
            return "Arriendo"
        else:
            return "No especificado"

    def _extract_property_type(self, needs: str) -> str:
        """Extrae tipo de propiedad del texto"""
        needs_lower = needs.lower()
        if any(word in needs_lower for word in ["apartamento", "apto"]):
            return "Apartamento"
        elif "casa" in needs_lower:
            return "Casa"
        elif any(word in needs_lower for word in ["local", "comercial"]):
            return "Local comercial"
        elif any(word in needs_lower for word in ["oficina"]):
            return "Oficina"
        else:
            return "No especificado"

    def _extract_zone_interest(self, needs: str) -> str:
        """Extrae zona de interés del texto"""
        needs_lower = needs.lower()
        zonas_medellin = ["poblado", "laureles", "envigado", "sabaneta", "itagui", "bello", "copacabana",
                         "la estrella", "caldas", "centro", "norte", "sur", "oriente", "occidente"]

        for zona in zonas_medellin:
            if zona in needs_lower:
                return zona.title()
        return "Área metropolitana"

    def _extract_budget_range(self, needs: str) -> str:
        """Extrae rango de presupuesto del texto"""
        import re
        numbers = re.findall(r'\d+', needs)
        if numbers:
            amount = int(numbers[0])
            if amount >= 500:
                return f"${amount}M - Alto"
            elif amount >= 200:
                return f"${amount}M - Medio-Alto"
            elif amount >= 100:
                return f"${amount}M - Medio"
            else:
                return f"${amount}M - Económico"
        return "Por definir"

    def _extract_urgency_level(self, needs: str) -> str:
        """Extrae nivel de urgencia del texto"""
        needs_lower = needs.lower()
        if any(word in needs_lower for word in ["urgente", "rápido", "ya", "inmediato"]):
            return "Alta"
        elif any(word in needs_lower for word in ["pronto", "este mes"]):
            return "Media-Alta"
        else:
            return "Media"

    def _extract_room_count(self, needs: str) -> str:
        """Extrae número de habitaciones del texto"""
        import re
        # Buscar patrones como "3 habitaciones", "2 hab", etc.
        room_patterns = re.findall(r'(\d+)\s*(?:habitacion|hab|cuarto|alcoba)', needs.lower())
        if room_patterns:
            return f"{room_patterns[0]} habitaciones"
        return "No especificado"

    def _generate_crm_preview(self, customer_name: str, needs: str) -> Dict[str, str]:
        """Genera preview de cómo se vería en el CRM real"""
        return {
            "Pipeline": "Leads Entrantes > Contacto Inicial",
            "Asesor Asignado": "Por asignar automáticamente",
            "Fuente": "WhatsApp Business - Bot Sofia",
            "Estado": "Nuevo - Requiere contacto 24h",
            "Seguimiento": "Llamada + WhatsApp oficial",
            "Notas": f"Lead capturado por IA. Cliente: {customer_name}. Interés: {needs[:50]}...",
            "Próxima Acción": f"Contactar {customer_name} en próximas 2 horas"
        }

    def _generate_visual_crm_simulation(self, customer_name: str, needs: str, metadata: Dict[str, Any]) -> str:
        """ACCIÓN 5.1: Genera simulación visual completa del CRM"""
        return f"""
╔══════════════════════════════════════════════════════════════════════════════════╗
║                           🏢 LEADSALES CRM - SIMULACIÓN VISUAL                   ║
╠══════════════════════════════════════════════════════════════════════════════════╣
║ LEAD ID: {self._get_mock_lead_id()}                                               ║
║ CLIENTE: {customer_name}                                                         ║
║ ESTADO: ✅ NUEVO LEAD - ALTA PRIORIDAD                                           ║
║ CAPTURADO: {metadata.get('created_at', 'Ahora')}                                ║
╠══════════════════════════════════════════════════════════════════════════════════╣
║ 📊 ANÁLISIS INTELIGENTE:                                                        ║
║ • Transacción: {metadata.get('tipo_transaccion', 'N/A')}                       ║
║ • Propiedad: {metadata.get('tipo_propiedad', 'N/A')}                           ║
║ • Zona: {metadata.get('zona_interes', 'N/A')}                                  ║
║ • Presupuesto: {metadata.get('presupuesto_estimado', 'N/A')}                   ║
║ • Urgencia: {metadata.get('urgencia_nivel', 'N/A')}                            ║
║ • Habitaciones: {metadata.get('habitaciones_deseadas', 'N/A')}                 ║
╠══════════════════════════════════════════════════════════════════════════════════╣
║ 🎯 FILTRADO INTELIGENTE APLICADO:                                               ║
║ {self._describe_filtro_applied(metadata)}                                       ║
╚══════════════════════════════════════════════════════════════════════════════════╝
"""

    def _determine_filtro(self, needs: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """ACCIÓN 5.2: Determina filtros inteligentes para el lead"""
        filtros = {
            "tipo_cliente": self._classify_client_type(needs, metadata),
            "segmento_mercado": self._determine_market_segment(metadata),
            "canal_preferido": self._determine_preferred_channel(metadata),
            "nivel_interes": self._calculate_interest_level(needs, metadata),
            "probabilidad_conversion": self._calculate_conversion_probability(metadata)
        }
        return filtros

    def _classify_client_type(self, needs: str, metadata: Dict[str, Any]) -> str:
        """Clasifica tipo de cliente"""
        if metadata.get('contrato_inmobiliaria') == 'Sí':
            return "Cliente Profesional (Con inmobiliaria)"
        elif metadata.get('solicitud_libertador') == 'Sí':
            return "Cliente Calificado (Libertador aprobado)"
        elif metadata.get('urgencia_nivel') == 'Alta':
            return "Cliente Urgente (Decisión rápida)"
        else:
            return "Cliente Estándar (Proceso normal)"

    def _determine_market_segment(self, metadata: Dict[str, Any]) -> str:
        """Determina segmento de mercado"""
        presupuesto = metadata.get('presupuesto_estimado', '')
        if 'Alto' in presupuesto:
            return "Segmento Premium (>500M)"
        elif 'Medio-Alto' in presupuesto:
            return "Segmento Medio-Alto (200-500M)"
        elif 'Medio' in presupuesto:
            return "Segmento Medio (100-200M)"
        else:
            return "Segmento Económico (<100M)"

    def _determine_preferred_channel(self, metadata: Dict[str, Any]) -> str:
        """Determina canal preferido de contacto"""
        urgencia = metadata.get('urgencia_nivel', '')
        if urgencia == 'Alta':
            return "Llamada inmediata + WhatsApp"
        elif urgencia == 'Media-Alta':
            return "WhatsApp oficial + Seguimiento telefónico"
        else:
            return "WhatsApp oficial + Email de seguimiento"

    def _calculate_interest_level(self, needs: str, metadata: Dict[str, Any]) -> str:
        """Calcula nivel de interés"""
        score = 0
        if metadata.get('presupuesto_estimado') != 'Por definir':
            score += 30
        if metadata.get('zona_interes') != 'Área metropolitana':
            score += 20
        if metadata.get('habitaciones_deseadas') != 'No especificado':
            score += 25
        if metadata.get('urgencia_nivel') == 'Alta':
            score += 25

        if score >= 80:
            return "🔥 MUY ALTO (Listo para cerrar)"
        elif score >= 60:
            return "⭐ ALTO (Muy interesado)"
        elif score >= 40:
            return "👍 MEDIO (Explorando opciones)"
        else:
            return "💭 BAJO (Información inicial)"

    def _calculate_conversion_probability(self, metadata: Dict[str, Any]) -> str:
        """Calcula probabilidad de conversión"""
        factors = [
            metadata.get('solicitud_libertador') == 'Sí',  # +40%
            metadata.get('presupuesto_estimado') != 'Por definir',  # +30%
            metadata.get('urgencia_nivel') in ['Alta', 'Media-Alta'],  # +20%
            metadata.get('zona_interes') != 'Área metropolitana'  # +10%
        ]

        probability = sum([40, 30, 20, 10][i] for i, factor in enumerate(factors) if factor)

        if probability >= 80:
            return f"🎯 {probability}% - CONVERSIÓN INMEDIATA"
        elif probability >= 60:
            return f"✅ {probability}% - ALTA PROBABILIDAD"
        elif probability >= 40:
            return f"⚡ {probability}% - BUENA OPORTUNIDAD"
        else:
            return f"📈 {probability}% - SEGUIMIENTO NECESARIO"

    def _describe_filtro_applied(self, metadata: Dict[str, Any]) -> str:
        """Describe el filtrado aplicado"""
        filtro_data = self._determine_filtro("", metadata)
        return f"""• Tipo: {filtro_data['tipo_cliente']}
║ • Segmento: {filtro_data['segmento_mercado']}
║ • Canal: {filtro_data['canal_preferido']}
║ • Interés: {filtro_data['nivel_interes']}
║ • Conversión: {filtro_data['probabilidad_conversion']}"""

    def _generate_smart_assignment(self, needs: str, metadata: Dict[str, Any]) -> Dict[str, str]:
        """ACCIÓN 5.3: Genera asignación inteligente de asesor"""
        # Determinar asesor basado en especialización
        asesor_data = self._select_specialized_advisor(needs, metadata)

        return {
            "asesor_asignado": asesor_data['nombre'],
            "especializacion": asesor_data['especializacion'],
            "razon_asignacion": asesor_data['razon'],
            "experiencia": asesor_data['experiencia'],
            "contacto": asesor_data['contacto'],
            "disponibilidad": asesor_data['disponibilidad'],
            "match_score": asesor_data['match_score']
        }

    def _select_specialized_advisor(self, needs: str, metadata: Dict[str, Any]) -> Dict[str, str]:
        """Selecciona asesor especializado"""
        advisors = {
            "premium": {
                "nombre": "María Rodríguez",
                "especializacion": "Propiedades Premium y Luxury",
                "experiencia": "8 años - Especialista en Poblado y Envigado",
                "contacto": "WhatsApp: +57 324 551 6105",
                "disponibilidad": "Disponible ahora",
            },
            "comercial": {
                "nombre": "Carlos Mendoza",
                "especializacion": "Propiedades Comerciales",
                "experiencia": "6 años - Experto en locales y oficinas",
                "contacto": "WhatsApp: +57 324 551 6105",
                "disponibilidad": "Disponible en 1 hora",
            },
            "residencial": {
                "nombre": "Ana García",
                "especializacion": "Propiedades Residenciales",
                "experiencia": "5 años - Especialista en familias",
                "contacto": "WhatsApp: +57 324 551 6105",
                "disponibilidad": "Disponible ahora",
            },
            "inversion": {
                "nombre": "Luis Herrera",
                "especializacion": "Inversión y Rentabilidad",
                "experiencia": "10 años - Experto en ROI inmobiliario",
                "contacto": "WhatsApp: +57 324 551 6105",
                "disponibilidad": "Disponible en 30 min",
            }
        }

        # Lógica de asignación
        presupuesto = metadata.get('presupuesto_estimado', '')
        tipo_propiedad = metadata.get('tipo_propiedad', '')

        if 'Alto' in presupuesto or 'Premium' in presupuesto:
            selected = advisors['premium']
            razon = "Alto presupuesto - Requiere asesor premium"
            match_score = "95%"
        elif 'comercial' in tipo_propiedad.lower() or 'local' in tipo_propiedad.lower():
            selected = advisors['comercial']
            razon = "Propiedad comercial - Especialista en sector"
            match_score = "90%"
        elif metadata.get('contrato_inmobiliaria') == 'Sí':
            selected = advisors['inversion']
            razon = "Cliente con experiencia - Enfoque en inversión"
            match_score = "88%"
        else:
            selected = advisors['residencial']
            razon = "Propiedad residencial - Asesor generalista"
            match_score = "85%"

        selected['razon'] = razon
        selected['match_score'] = match_score
        return selected

    def _generate_comparative_table(self, needs: str, metadata: Dict[str, Any]) -> str:
        """ACCIÓN 5.4-5.5: Genera tabla comparativa Chatling vs IA Sistema"""
        return f"""
╔══════════════════════════════════════════════════════════════════════════════════╗
║                        📊 COMPARATIVA: CHATLING vs IA SISTEMA                   ║
╠══════════════════════════════════════════════════════════════════════════════════╣
║ ASPECTO                    │ CHATLING          │ IA SISTEMA INMOBILIARIA        ║
╠════════════════════════════╪═══════════════════╪════════════════════════════════╣
║ Captura de Información     │ ❌ Básica          │ ✅ Rica y estructurada         ║
║ Análisis Inteligente       │ ❌ No disponible   │ ✅ 10+ campos automáticos      ║
║ Asignación de Asesor       │ ❌ Manual/Random   │ ✅ Inteligente por perfil      ║
║ Filtrado de Leads          │ ❌ Sin filtros     │ ✅ 5 criterios automáticos     ║
║ Simulación CRM             │ ❌ Sin preview     │ ✅ Vista previa completa       ║
║ Metadata de Flujo          │ ❌ Solo texto      │ ✅ 15+ campos estructurados    ║
║ Probabilidad Conversión    │ ❌ No calcula      │ ✅ Algoritmo predictivo        ║
║ Especialización Asesor     │ ❌ Genérico        │ ✅ Match por especialidad      ║
║ Canal de Contacto          │ ❌ Estándar        │ ✅ Optimizado por urgencia     ║
║ Tabla Comparativa          │ ❌ Inexistente     │ ✅ Esta misma tabla 😊         ║
╠══════════════════════════════════════════════════════════════════════════════════╣
║ RESULTADO:                 │ ❌ Lead básico     │ ✅ Lead premium listo          ║
║ TIEMPO ASESOR:             │ ⏰ 15+ min setup   │ ⚡ 2 min contacto directo      ║
║ CONVERSIÓN ESTIMADA:       │ 📉 15-25%          │ 📈 {metadata.get('probabilidad_conversion', '85%')}   ║
╚══════════════════════════════════════════════════════════════════════════════════╝
"""

    def _get_mock_lead_id(self) -> str:
        """Helper para obtener ID consistente en la sesión"""
        import uuid
        return f"DEMO-{uuid.uuid4().hex[:8]}"

# Singleton para uso global
leadsales_service = LeadsalesService()