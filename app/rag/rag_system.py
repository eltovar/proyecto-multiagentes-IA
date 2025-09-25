"""
Sistema RAG Coordinador: Interface principal para agentes.
Coordina entre RAGLoader y RAGSearchEngine para búsqueda de contexto.
"""

from typing import Dict, Any
from .rag_loader import RAGLoader
from .rag_search import RAGSearchEngine

class RAGSystem:

    def __init__(self, rag_data_path: str = "data/rag"):
        self.rag_data_path = rag_data_path
        self.loader = None
        self.search_engine = None
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
                model=components["model"]
            )

            self.metadata = components["metadata"]
            self.initialized = True

            print(f"[RAGSystem] Sistema inicializado: {len(components['documents'])} documentos")
            return True

        except Exception as e:
            print(f"[RAGSystem] Error inicializando: {e}")
            return False

    def search_context(self, query: str, max_results: int = 5) -> str:
        if not self.initialized:
            print("[RAGSystem] Error: Sistema no inicializado")
            return ""

        return self.search_engine.get_context_for_response(query, max_context=2000)

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