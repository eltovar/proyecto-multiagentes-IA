"""
Information Analyzer for LeadsalesAgent
Extracted from leadsales_agent.py (lines 319-339, 360-385)
Handles information completeness analysis and key information extraction
"""

import re
from typing import Dict, Any


class InformationAnalyzer:
    """Analyzes and extracts key information from user messages for lead qualification"""

    @staticmethod
    def analyze_completeness(message: str) -> bool:
        """Analizar si el mensaje contiene información suficiente para crear lead de calidad"""

        message_lower = message.lower()

        # Criterios de completitud para lead de alta calidad
        quality_indicators = {
            "property_type": ["apartamento", "casa", "local", "oficina", "lote", "finca"],
            "transaction_type": ["comprar", "vender", "arrendar", "alquilar"],
            "location": ["zona", "sector", "barrio", "poblado", "centro", "norte", "sur"],
            "specs": ["habitacion", "baño", "metro", "piso", "parqueadero"],
            "budget": ["presupuesto", "precio", "valor", "millones", "pesos"]
        }

        categories_found = 0
        for category, keywords in quality_indicators.items():
            if any(keyword in message_lower for keyword in keywords):
                categories_found += 1

        # Considerar completo si tiene al menos 2 categorías de información
        return categories_found >= 2

    @staticmethod
    def extract_key_information(message: str) -> Dict[str, Any]:
        """Extraer información clave del mensaje para análisis"""

        message_lower = message.lower()
        extracted = {}

        # Extraer tipo de propiedad
        property_types = {
            "apartamento": ["apartamento", "apto"],
            "casa": ["casa", "vivienda"],
            "local": ["local", "comercial"],
            "oficina": ["oficina", "oficinas"]
        }

        for prop_type, keywords in property_types.items():
            if any(keyword in message_lower for keyword in keywords):
                extracted["property_type"] = prop_type
                break

        # Extraer números (posibles habitaciones, precio, etc.)
        numbers = re.findall(r'\d+', message)
        if numbers:
            extracted["numbers_mentioned"] = numbers

        return extracted