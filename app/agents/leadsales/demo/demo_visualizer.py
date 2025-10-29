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
        """Muestra preview visual del CRM para demo con análisis enriquecido (PR005)"""
        customer_data = lead_result["customer_data"]
        crm_sim = lead_result["crm_simulation"]
        analysis = lead_result.get("integrated_analysis")  # ✅ NUEVO (PR005)

        print("\n" + "="*80)
        print("*** SIMULACION CRM LEADSALES - LEAD CREADO ***")
        print("="*80)

        # Información básica
        print(f"\n📋 INFORMACIÓN DEL CLIENTE:")
        print(f"  • Nombre: {customer_data['name']}")
        print(f"  • WhatsApp: {customer_data['whatsapp']}")
        print(f"  • Necesidad: {customer_data['needs'][:100]}...")

        # Scoring básico
        print(f"\n📊 SCORING BÁSICO:")
        print(f"  • Calidad: {customer_data['quality_score']}/100")
        print(f"  • Prioridad: {customer_data['priority']}")
        print(f"  • Etiquetas: {', '.join(customer_data['tags'])}")

        # Análisis integrado (NUEVO) ✅
        if analysis:
            print(f"\n🎯 ANÁLISIS INTEGRADO:")
            print(f"  • Composite Score: {analysis['composite_score']:.1f}/100")
            print(f"  • Prob. Conversión: {analysis['conversion_probability']*100:.0f}%")
            print(f"  • Valor Estimado: {analysis['estimated_value'].upper()}")
            print(f"  • Segmento: {analysis['segment_description']}")
            print(f"  • Perfil: {analysis['profile'].capitalize()}")
            print(f"  • Sofisticación: {analysis['sophistication'].capitalize()}")
            print(f"  • Prioridad Ajustada: {analysis['priority_adjusted']} (Numérico: {analysis['priority_numeric']}/10)")

            # Insights clave
            if analysis['key_insights']:
                print(f"\n💡 INSIGHTS CLAVE:")
                for insight in analysis['key_insights']:
                    print(f"  • {insight}")

            # Acciones recomendadas
            if analysis['recommended_actions']:
                print(f"\n✅ ACCIONES RECOMENDADAS:")
                for i, action in enumerate(analysis['recommended_actions'], 1):
                    print(f"  {i}. {action}")

            # Factores de riesgo
            if analysis['risk_factors']:
                print(f"\n⚠️  FACTORES DE RIESGO:")
                for risk in analysis['risk_factors']:
                    print(f"  • {risk}")

        # CRM Simulation
        print(f"\n🏢 CRM:")
        print(f"  • ID Lead: {crm_sim['lead_id']}")
        print(f"  • Estado: {crm_sim['status']}")
        print(f"  • Asignado a: {crm_sim['assigned_to']}")
        print(f"  • Próximo seguimiento: {crm_sim['next_followup']}")
        print(f"  • Valor estimado: {crm_sim['estimated_value']}")

        print("="*80 + "\n")

