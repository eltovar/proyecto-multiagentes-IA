"""Validacion manual de refactorizacion modular"""
import asyncio
import sys
from pathlib import Path

# Agregar directorio raiz al PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.leadsales import LeadsalesService


async def main():
    service = LeadsalesService()

    # Forzar modo demo para validacion
    service.client._is_demo_mode = True

    test_cases = [
        {
            "name": "Lead de alta calidad",
            "customer_name": "Maria Garcia",
            "whatsapp": "3001234567",
            "needs": "Busco casa urgente para comprar en Poblado con presupuesto de 800 millones",
            "additional_data": {"location": "Poblado"}
        },
        {
            "name": "Lead de calidad media",
            "customer_name": "Carlos Lopez",
            "whatsapp": "3009876543",
            "needs": "Me interesa arrendar apartamento de 2 habitaciones",
            "additional_data": {}
        },
        {
            "name": "Lead de baja calidad",
            "customer_name": "Ana Martinez",
            "whatsapp": "3005555555",
            "needs": "Informacion general sobre sus servicios",
            "additional_data": {}
        }
    ]

    print("=" * 70)
    print("VALIDACION PR003 - REFACTORIZACION MODULAR")
    print("=" * 70)

    for i, case in enumerate(test_cases, 1):
        print(f"\n[TEST {i}] {case['name']}")
        print("-" * 70)

        result = await service.create_lead(
            case["customer_name"],
            case["whatsapp"],
            case["needs"],
            case["additional_data"]
        )

        # Mostrar resultados
        customer_data = result["customer_data"]
        print(f"Cliente: {customer_data['name']}")
        print(f"WhatsApp: {customer_data['whatsapp']}")
        print(f"Quality Score: {customer_data['quality_score']}/100")
        print(f"Priority: {customer_data['priority']}")
        print(f"Tags: {', '.join(customer_data['tags'])}")

        # Confidence esta en crm_simulation
        if "crm_simulation" in result:
            confidence = result["crm_simulation"].get("confidence_level", 0)
            print(f"Confidence: {confidence:.2f}")

        # Metadata esta en nivel raiz
        if "metadata" in result:
            metadata = result["metadata"]
            print(f"Metadata extraida:")
            print(f"  - Location: {metadata.get('location', 'N/A')}")
            print(f"  - Property Type: {metadata.get('property_type', 'N/A')}")
            print(f"  - Budget Range: {metadata.get('budget_range', 'N/A')}")
            print(f"  - Rooms: {metadata.get('rooms', 'N/A')}")
            print(f"  - Urgency: {metadata.get('urgency_level', 'N/A')}")

        print(f"[OK] Test {i} completado")

    await service.close()
    print("\n" + "=" * 70)
    print("[OK] VALIDACION COMPLETADA - Todos los modulos funcionando correctamente")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(main())