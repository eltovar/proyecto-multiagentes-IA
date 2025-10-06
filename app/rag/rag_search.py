"""
RAG Search Engine: Búsqueda semántica y recuperación de contexto.
Responsable de realizar búsquedas vectoriales con FAISS.
"""

import numpy as np
import faiss
from typing import List, Dict, Any

class RAGSearchEngine:

    def __init__(self, faiss_index, documents, embeddings, model):
        self.faiss_index = faiss_index
        self.documents = documents
        self.embeddings = embeddings
        self.model = model

    def search_similar_documents(
        self,
        query: str,
        top_k: int = 3,
        similarity_threshold: float = 10.0  # Ajustado para distancia L2
    ) -> List[Dict[str, Any]]:
        try:
            query_embedding = self._compute_query_embedding(query)
            similarities, indices = self.faiss_index.search(
                query_embedding.astype('float32'),
                top_k
            )

            results = self._rank_results(similarities[0], indices[0], similarity_threshold)

            print(f"[RAGSearch] Búsqueda completada: {len(results)} resultados para '{query[:50]}...'")
            return results

        except Exception as e:
            print(f"[RAGSearch] Error en búsqueda: {e}")
            return []

    def _compute_query_embedding(self, query: str):
        query_embedding = self.model.encode([query], convert_to_numpy=True)
        faiss.normalize_L2(query_embedding)
        return query_embedding

    def _rank_results(self, similarities, indices, similarity_threshold: float) -> List[Dict[str, Any]]:
        results = []
        for i, (similarity, doc_idx) in enumerate(zip(similarities, indices)):
            # Para IndexFlatL2, similarity es distancia (menor = más similar)
            if similarity <= similarity_threshold and doc_idx < len(self.documents):
                document = self.documents[doc_idx].copy()
                document['similarity_score'] = float(similarity)
                document['rank'] = i + 1
                results.append(document)

        return results

    def get_context_for_response(self, query: str, max_context: int = 2000) -> str:
        relevant_docs = self.search_similar_documents(query, top_k=8)  # Aumentado para mejor cobertura

        if not relevant_docs:
            return ""

        # Priorizar documentos con keywords relevantes del query
        query_words = query.lower().split()
        prioritized_docs = []

        # Primero documentos con matches exactos de filename o contenido
        for doc in relevant_docs:
            filename = doc.get('filename', '').lower()
            content = doc.get('content', '').lower()

            # Score por keywords en filename y contenido
            keyword_score = 0
            for word in query_words:
                if word in filename:
                    keyword_score += 3  # Filename match vale más
                if word in content:
                    keyword_score += 1

            doc['keyword_score'] = keyword_score
            prioritized_docs.append(doc)

        # Ordenar por keyword_score descendente, luego por similarity score ascendente
        prioritized_docs.sort(key=lambda x: (-x['keyword_score'], x['similarity_score']))

        context_parts = []
        current_length = 0

        for doc in prioritized_docs:
            content = doc.get('content', '')
            title = doc.get('title', '')

            formatted_content = f"{title}: {content}" if title else content

            if current_length + len(formatted_content) <= max_context:
                context_parts.append(formatted_content)
                current_length += len(formatted_content)
            else:
                remaining_space = max_context - current_length
                if remaining_space > 100:
                    truncated_content = formatted_content[:remaining_space-3] + "..."
                    context_parts.append(truncated_content)
                break

        context = "\n\n".join(context_parts)

        print(f"[RAGSearch] Contexto generado: {len(context)} caracteres de {len(context_parts)} documentos")
        return context

    def get_search_stats(self) -> Dict[str, Any]:
        return {
            "total_documents": len(self.documents),
            "vector_dimension": self.embeddings.shape[1] if self.embeddings is not None else 0,
            "faiss_index_size": self.faiss_index.ntotal if self.faiss_index else 0
        }