"""
Sistema RAG Coordinador: Interface principal para agentes.
Coordina entre RAGLoader y RAGSearchEngine para búsqueda de contexto.
"""

from typing import Dict, Any, Optional, List, Set
import re
from .rag_loader import RAGLoader
from .rag_search import RAGSearchEngine
from .query_expander import QueryExpander
from .reranker import ReRanker

class RAGSystem:

    # Regex mejorado compilado para eficiencia
    # Captura números colombianos en múltiples formatos:
    # - +57 310 123 4567
    # - (310) 123-4567
    # - 310 123 4567
    # - 310 123 45 67 (formato no estándar con espacios extra)
    # - 3101234567
    PHONE_REGEX = re.compile(
        r"\b(?:\+?57\s*)?\(?(3\d{2})\)?[\s\-]*(\d{3})[\s\-]*(\d{2})[\s\-]*(\d{2})\b"
    )

    def __init__(
        self,
        rag_data_path: str = "data/rag",
        query_expander: Optional[QueryExpander] = None,
        reranker: Optional[ReRanker] = None
    ):
        self.rag_data_path = rag_data_path
        self.loader = None
        self.search_engine = None
        self.query_expander = query_expander
        self.reranker = reranker
        self.initialized = False
        self.metadata = {}

    def initialize(self) -> bool:
        try:
            print("[RAGSystem] Iniciando sistema RAG")

            self.loader = RAGLoader(self.rag_data_path)
            components = self.loader.load_all_components()

            if not components["success"]:
                print(f"[RAGSystem] Error: {components['error']}")
                return False

            self.search_engine = RAGSearchEngine(
                faiss_index=components["faiss_index"],
                documents=components["documents"],
                embeddings=components["embeddings"],
                model=components["model"],
                query_expander=self.query_expander,
                reranker=self.reranker
            )

            self.metadata = components["metadata"]
            self.initialized = True

            print(f"[RAGSystem] Sistema inicializado: {len(components['documents'])} documentos")
            return True

        except Exception as e:
            print(f"[RAGSystem] Error inicializando: {e}")
            return False

    def _extract_phone_numbers(self, documents: List[Dict[str, Any]]) -> List[str]:
        """
        Extrae y normaliza números de teléfono de documentos usando regex mejorado.
        Los números se devuelven normalizados como solo dígitos (ej: "3101234567").

        Args:
            documents: Lista de documentos con campo 'content'

        Returns:
            Lista de números únicos normalizados
        """
        # Usar Set para deduplicación automática
        unique_normalized_phones: Set[str] = set()

        for doc in documents:
            content = doc.get('content', '')

            # Usar finditer para obtener grupos de captura
            for match in self.PHONE_REGEX.finditer(content):
                # match.groups() devuelve tupla: ('310', '123', '45', '67') o ('310', '123', '4567')
                # Normalización: unir grupos para obtener solo dígitos
                normalized_phone = "".join(match.groups())
                unique_normalized_phones.add(normalized_phone)

        print(f"[RAGSystem] Phone extraction: found {len(unique_normalized_phones)} numbers in {len(documents)} docs")

        return list(unique_normalized_phones)

    def search_context(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """
        Busca contexto relevante y extrae información estructurada.

        Args:
            query: Consulta del usuario
            max_results: Número máximo de resultados (no usado, se usa reranker_top_k)

        Returns:
            Dict con:
            - context: str (texto concatenado)
            - documents: List[Dict] (documentos recuperados top-3 rerankeados)
            - phone_numbers: List[str] (teléfonos extraídos de top-3)
            - rag_confidence: float
        """
        if not self.initialized:
            print("[RAGSystem] Error: Sistema no inicializado")
            return {
                "context": "",
                "documents": [],
                "phone_numbers": [],
                "rag_confidence": 0.0
            }

        # Obtener documentos rerankeados (top-3 por defecto con re-ranking)
        documents = self.search_engine.search_similar_documents(query, top_k=20)

        # Extraer teléfonos de top-3 rerankeados (después de re-ranking)
        phone_numbers = self._extract_phone_numbers(documents[:3])

        # Obtener contexto de texto
        context_text = self.search_engine.get_context_for_response(query, max_context=2000)

        # Calcular confianza promedio (basado en rerank_score si existe)
        confidence = 0.0
        if documents:
            scores = [doc.get('rerank_score', 0.0) for doc in documents if 'rerank_score' in doc]
            if scores:
                # Normalizar scores negativos a [0, 1]
                confidence = max(0.0, 1.0 + (sum(scores) / len(scores) / 10))
            else:
                confidence = 0.5

        return {
            "context": context_text,
            "documents": documents,
            "phone_numbers": phone_numbers,
            "rag_confidence": confidence
        }

    def is_initialized(self) -> bool:
        return self.initialized

    def health_check(self) -> Dict[str, Any]:
        if not self.initialized:
            return {"status": "unhealthy", "reason": "Sistema no inicializado"}

        try:
            stats = self.search_engine.get_search_stats()
            return {
                "status": "healthy",
                "documents_loaded": stats["total_documents"],
                "vector_dimension": stats["vector_dimension"]
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "reason": f"Error en health check: {str(e)}"
            }

    def get_context_for_query(self, query: str) -> str:
        return self.search_context(query)

rag_system = RAGSystem()