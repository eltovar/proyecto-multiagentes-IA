"""
Demo Visualizer for LeadsalesAgent
Extracted from leadsales_agent.py (lines 386-409)
Handles CRM preview visualization for demo mode
"""

from typing import Dict, Any


class DemoVisualizer:
    """Handles demo visualization for CRM lead creation"""

    @staticmethod
    def display_crm_preview(customer_name: str, lead_result: Dict[str, Any]):
        """Muestra preview visual del CRM para demo"""
        customer_data = lead_result["customer_data"]
        crm_sim = lead_result["crm_simulation"]

        print("\n" + "="*60)
        print("*** SIMULACION CRM LEADSALES - LEAD CREADO ***")
        print("="*60)
        print(f"CLIENTE: {customer_data['name']}")
        print(f"WHATSAPP: {customer_data['whatsapp']}")
        print(f"NECESIDAD: {customer_data['needs'][:80]}...")
        print(f"CALIDAD: {customer_data['quality_score']}/100")
        print(f"ETIQUETAS: {', '.join(customer_data['tags'])}")
        print(f"PRIORIDAD: {customer_data['priority']}")
        print(f"CREADO: {customer_data['created_at']}")
        print(f"LEAD ID: {lead_result['lead_id']}")
        print("\nVISTA PREVIA CRM:")
        for key, value in crm_sim.items():
            if isinstance(value, list):
                print(f"   {key}: {', '.join(value)}")
            else:
                print(f"   {key}: {value}")
        print("="*60)
        print("*** DEMO: Lead enviado al pipeline de ventas ***")