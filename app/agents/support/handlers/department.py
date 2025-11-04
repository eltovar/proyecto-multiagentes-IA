"""
DepartmentHandler - Camino 2: Redireccion a departamentos
Maneja consultas sobre departamentos especificos (ventas, administracion, etc.)
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class DepartmentHandlerResult:
    """Resultado del handler de departamentos"""
    response: str
    next_state: str
    department: Optional[str] = None
    contact_info: Optional[Dict[str, str]] = None
    data_updates: Optional[Dict[str, Any]] = None


class DepartmentHandler:
    """Maneja consultas relacionadas a departamentos"""
    def __init__(self, llm_service, state_manager, config: Dict[str, Any]):
        self.llm = llm_service
        self.state = state_manager
        self.departments = config.get("departments", {})

    async def handle_department_request(
        self,
        classification: Dict[str, Any],
        rag_result: Dict[str, Any],
        customer_name: str
    ) -> DepartmentHandlerResult:
        """
        Procesa consulta sobre departamentos.
        """

        # TODO: Implementar logica completa cuando se migre desde support_agent.py
        # Por ahora, respuesta basica

        department = classification.get("entities", {}).get("department", "general")

        # Buscar informacion de contacto en RAG
        contact_info = self._extract_contact_from_rag(rag_result, department)

        if contact_info:
            response = f"{customer_name}, te conecto con {department}. Contacto: {contact_info.get('phone')}"
            next_state = "DEPARTMENT_CONNECTED"
        else:
            response = f"{customer_name}, estoy buscando el contacto de {department}. Un momento por favor."
            next_state = "SEARCHING_DEPARTMENT"

        return DepartmentHandlerResult(
            response=response,
            next_state=next_state,
            department=department,
            contact_info=contact_info
        )

    def _extract_contact_from_rag(
        self,
        rag_result: Dict[str, Any],
        department: str
    ) -> Optional[Dict[str, str]]:
        """
        Extrae informacion de contacto del resultado RAG.

        Nota: La extracción de teléfonos por regex ocurre en RAGSystem
        sobre los top-3 documentos rerankeados.
        """

        # Extraer phone_numbers del RAG (ya extraídos por regex en RAGSystem)
        phone_numbers = rag_result.get("phone_numbers", [])
        documents = rag_result.get("documents", [])

        # Log de debugging
        print(f"[DepartmentHandler] Phone extraction: found {len(phone_numbers)} numbers in {len(documents)} docs")

        if phone_numbers:
            print(f"[DepartmentHandler] Using phone: {phone_numbers[0]}")
            return {
                "department": department,
                "phone": phone_numbers[0],
                "source": "rag"
            }

        print(f"[DepartmentHandler] No phone numbers found for {department}")
        return None