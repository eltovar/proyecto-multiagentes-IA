"""
Genera reporte completo de un lead con análisis integrado.
Útil para testing manual y demos.
"""
import asyncio
import json
import sys
from pathlib import Path

# Agregar raíz del proyecto al sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.leadsales import LeadsalesService


async def generate_report(customer_name, whatsapp, needs, additional_data=None):
    """Genera reporte de lead"""
    service = LeadsalesService()
    service.is_demo_mode = True
    
    result = await service.create_lead(
        customer_name,
        whatsapp,
        needs,
        additional_data or {}
    )
    
    # Extraer datos clave
    customer_data = result["customer_data"]
    analysis = result.get("integrated_analysis", {})
    crm_sim = result.get("crm_simulation", {})
    
    # Generar reporte formateado
    print("\n" + "="*80)
    print(f"REPORTE DE LEAD - {customer_name}")
    print("="*80)
    
    print(f"\n📋 INFORMACIÓN BÁSICA:")
    print(f"  • Nombre: {customer_data['name']}")
    print(f"  • WhatsApp: {customer_data['whatsapp']}")
    print(f"  • Necesidad: {customer_data['needs'][:150]}...")
    
    print(f"\n📊 SCORING:")
    print(f"  • Quality Score: {customer_data['quality_score']}/100")
    print(f"  • Composite Score: {analysis.get('composite_score', 'N/A')}/100")
    print(f"  • Prioridad Base: {customer_data['priority']}")
    print(f"  • Prioridad Ajustada: {analysis.get('priority_adjusted', 'N/A')} (Numérico: {analysis.get('priority_numeric', 'N/A')}/10)")
    print(f"  • Tags: {', '.join(customer_data['tags'])}")
    
    print(f"\n🎯 CLASIFICACIÓN:")
    print(f"  • Perfil: {analysis.get('profile', 'N/A').capitalize()}")
    print(f"  • Sofisticación: {analysis.get('sophistication', 'N/A').capitalize()}")
    print(f"  • Segmento: {analysis.get('segment_description', 'N/A')}")
    
    print(f"\n📈 CONVERSIÓN:")
    print(f"  • Probabilidad: {analysis.get('conversion_probability', 0)*100:.0f}%")
    print(f"  • Valor Estimado: {analysis.get('estimated_value', 'N/A').upper()}")
    print(f"  • Confianza Análisis: {analysis.get('analysis_confidence', 0)*100:.0f}%")
    
    if analysis.get('key_insights'):
        print(f"\n💡 INSIGHTS CLAVE:")
        for insight in analysis['key_insights']:
            print(f"  {insight}")
    
    if analysis.get('recommended_actions'):
        print(f"\n✅ ACCIONES RECOMENDADAS:")
        for i, action in enumerate(analysis['recommended_actions'], 1):
            print(f"  {i}. {action}")
    
    if analysis.get('risk_factors'):
        print(f"\n⚠️  FACTORES DE RIESGO:")
        for risk in analysis['risk_factors']:
            print(f"  {risk}")
    
    print(f"\n🏢 CRM:")
    print(f"  • ID: {crm_sim.get('lead_id', 'N/A')}")
    print(f"  • Estado: {crm_sim.get('status', 'N/A')}")
    print(f"  • Próximo seguimiento: {crm_sim.get('next_followup', 'N/A')}")
    
    print("="*80 + "\n")
    
    # Guardar JSON
    filename = f"lead_report_{customer_name.replace(' ', '_').lower()}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Reporte guardado en: {filename}\n")


async def main():
    """Casos de prueba"""
    
    # Caso 1: Inversionista de alto valor
    await generate_report(
        "Carlos Investor Pro",
        "3001234567",
        "Busco apartamento para inversión en Poblado con análisis de ROI, proyección de plusvalía histórica y flujo de caja. Presupuesto de 800 millones.",
        {"location": "Poblado"}
    )
    
    # Caso 2: Familia casual
    await generate_report(
        "María Familia",
        "3009876543",
        "Busco casa para mi familia con 4 habitaciones cerca de colegios buenos",
        {}
    )
    
    # Caso 3: Arquitecto profesional
    await generate_report(
        "Ana Arquitecta",
        "3005555555",
        "Soy arquitecta y busco apartamento con buen diseño, distribución de espacios y planos para remodelar",
        {}
    )


if __name__ == "__main__":
    asyncio.run(main())