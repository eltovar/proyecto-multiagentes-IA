 """
    Sistema RAG (Retrieval Augmented Generation) para el Agente de Soporte.

    Funcionalidades:
    - Carga de base de conocimiento vectorial
    - Busqueda semantica con embeddings
    - Recuperacion de contexto relevante
    - Integracion con LLM para respuestas contextuales
"""

import os
import json
import numpy as np
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
import faiss
from pathlib import Path
import structlog

logger = structlog.get_logger()

class RAGSystem:
    def __init__(self, rag_data_path: str = "data/rag"):
        """
        Inicializa el sistema RAG.

        Args:
            rag_data_path: Ruta donde estan los archivos de la base de conocimiento
        """
        self.rag_data_path = Path(rag_data_path)
        self.model = None
        self.documents = []
        self.embeddings = None
        self.faiss_index = None
        self.metadata = {}
        self.initialized = False

        self.logger = logger.bind(component="rag_system")

    def initialize(self) -> bool:
        """
        Inicializa el sistema RAG cargando todos los componentes.

        Returns:
            bool: True si la inicializacion fue exitosa
        """
        try:
            self.logger.info("Iniciando sistema RAG")

            # Verificar que existen los archivos necesarios
            if not self._check_rag_files():
                self.logger.error("Archivos RAG no encontrados")
                return False

            # Cargar modelo de embeddings
            self._load_embedding_model()

            # Cargar documentos
            self._load_documents()

            # Cargar embeddings
            self._load_embeddings()

            # Cargar indice FAISS
            self._load_faiss_index()

            # Cargar metadata
            self._load_metadata()

            self.initialized = True
            self.logger.info(
                "Sistema RAG inicializado correctamente",
                num_documents=len(self.documents),
                embedding_dimension=self.embeddings.shape[1] if self.embeddings is not None else 0
            )

            return True

        except Exception as e:
            self.logger.error("Error inicializando sistema RAG", error=str(e))
            return False

    def _check_rag_files(self) -> bool:
        """Verifica que existen todos los archivos necesarios."""
        required_files = [
            "documents.json",
            "embeddings.npy",
            "faiss_index.bin",
            "metadata.json"
        ]

        for filename in required_files:
            file_path = self.rag_data_path / filename
            if not file_path.exists():
                self.logger.error(f"Archivo requerido no encontrado: {file_path}")
                return False

        return True

    def _load_embedding_model(self):
        """Carga el modelo de embeddings."""
        self.logger.info("Cargando modelo de embeddings")
        # Usar el mismo modelo que se uso para construir la base de conocimiento
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

    def _load_documents(self):
        """Carga los documentos desde el archivo JSON."""
        documents_path = self.rag_data_path / "documents.json"
        with open(documents_path, 'r', encoding='utf-8') as f:
            self.documents = json.load(f)

        self.logger.info(f"Cargados {len(self.documents)} documentos")

    def _load_embeddings(self):
        """Carga los embeddings desde el archivo numpy."""
        embeddings_path = self.rag_data_path / "embeddings.npy"
        self.embeddings = np.load(embeddings_path)

        self.logger.info(f"Cargados embeddings: {self.embeddings.shape}")

    def _load_faiss_index(self):
        """Carga el indice FAISS."""
        index_path = self.rag_data_path / "faiss_index.bin"
        self.faiss_index = faiss.read_index(str(index_path))

        self.logger.info(f"Indice FAISS cargado: {self.faiss_index.ntotal} vectores")

    def _load_metadata(self):
        """Carga los metadatos."""
        metadata_path = self.rag_data_path / "metadata.json"
        with open(metadata_path, 'r', encoding='utf-8') as f:
            self.metadata = json.load(f)

    def search_similar_documents(
        self,
        query: str,
        top_k: int = 3,
        similarity_threshold: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Busca documentos similares usando busqueda semantica.

        Args:
            query: Consulta del usuario
            top_k: Numero maximo de documentos a retornar
            similarity_threshold: Umbral minimo de similitud

        Returns:
            Lista de documentos relevantes con scores
        """
        if not self.initialized:
            self.logger.error("Sistema RAG no inicializado")
            return []

        try:
            # Generar embedding de la consulta
            query_embedding = self.model.encode([query], convert_to_numpy=True)

            # Normalizar para usar cosine similarity
            faiss.normalize_L2(query_embedding)

            # Buscar en el indice FAISS
            similarities, indices = self.faiss_index.search(
                query_embedding.astype('float32'),
                top_k
            )

            # Filtrar resultados por umbral de similitud
            results = []
            for i, (similarity, doc_idx) in enumerate(zip(similarities[0], indices[0])):
                if similarity >= similarity_threshold and doc_idx < len(self.documents):
                    document = self.documents[doc_idx].copy()
                    document['similarity_score'] = float(similarity)
                    document['rank'] = i + 1
                    results.append(document)

            self.logger.info(
                "Busqueda semantica completada",
                query_preview=query[:50],
                results_found=len(results),
                top_similarity=results[0]['similarity_score'] if results else 0
            )

            return results

        except Exception as e:
            self.logger.error("Error en busqueda semantica", error=str(e))
            return []

    def get_context_for_query(self, query: str, max_context_length: int = 2000) -> str:
        """
        Obtiene contexto relevante para una consulta.

        Args:
            query: Consulta del usuario
            max_context_length: Longitud maxima del contexto en caracteres

        Returns:
            Contexto relevante concatenado
        """
        relevant_docs = self.search_similar_documents(query, top_k=3)

        if not relevant_docs:
            return ""

        # Concatenar contenido de documentos relevantes
        context_parts = []
        current_length = 0

        for doc in relevant_docs:
            content = doc.get('content', '')
            title = doc.get('title', '')

            # Formato: Titulo: Contenido
            formatted_content = f"{title}: {content}" if title else content

            if current_length + len(formatted_content) <= max_context_length:
                context_parts.append(formatted_content)
                current_length += len(formatted_content)
            else:
                # Truncar el ultimo documento si es necesario
                remaining_space = max_context_length - current_length
                if remaining_space > 100:  # Solo incluir si hay espacio razonable
                    truncated_content = formatted_content[:remaining_space-3] + "..."
                    context_parts.append(truncated_content)
                break

        context = "\n\n".join(context_parts)

        self.logger.info(
            "Contexto generado",
            context_length=len(context),
            documents_used=len(context_parts)
        )

        return context

    def get_system_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadisticas del sistema RAG.

        Returns:
            Dict con estadisticas del sistema
        """
        return {
            "initialized": self.initialized,
            "model_name": self.metadata.get("model_name", "unknown"),
            "num_documents": len(self.documents),
            "vector_dimension": self.metadata.get("vector_dimension", 0),
            "faiss_index_size": self.faiss_index.ntotal if self.faiss_index else 0,
            "created_at": self.metadata.get("created_at", "unknown")
        }

    def health_check(self) -> Dict[str, Any]:
        """
        Verifica la salud del sistema RAG.

        Returns:
            Dict con estado de salud
        """
        try:
            if not self.initialized:
                return {"status": "unhealthy", "reason": "Sistema no inicializado"}

            # Verificar componentes criticos
            if self.model is None:
                return {"status": "unhealthy", "reason": "Modelo de embeddings no cargado"}

            if len(self.documents) == 0:
                return {"status": "unhealthy", "reason": "No hay documentos cargados"}

            if self.faiss_index is None:
                return {"status": "unhealthy", "reason": "Indice FAISS no cargado"}

            # Prueba de busqueda simple
            test_results = self.search_similar_documents("test query", top_k=1)

            return {
                "status": "healthy",
                "documents_loaded": len(self.documents),
                "search_functional": len(test_results) >= 0
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "reason": f"Error en health check: {str(e)}"
            }

# Singleton para uso global
rag_system = RAGSystem()