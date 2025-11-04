"""
RAG Search Engine: Búsqueda semántica y recuperación de contexto.
Responsable de realizar búsquedas vectoriales con FAISS.
"""

import numpy as np
import faiss
from typing import List, Dict, Any, Optional
from app.config import settings

class RAGSearchEngine:

    def __init__(
        self,
        faiss_index,
        documents,
        embeddings,
        model,
        query_expander: Optional['QueryExpander'] = None,
        reranker: Optional['ReRanker'] = None
    ):
        self.faiss_index = faiss_index
        self.documents = documents
        self.embeddings = embeddings
        self.model = model
        self.query_expander = query_expander
        self.reranker = reranker

    def search_similar_documents(
        self,
        query: str,
        top_k: int = 20,  # Incrementado de 3 a 20 para re-ranking
        similarity_threshold: float = 10.0  # Ajustado para distancia L2
    ) -> List[Dict[str, Any]]:
        try:
            # Query Expansion: expandir query antes de búsqueda vectorial
            expanded_query = query
            if self.query_expander:
                try:
                    expanded_query = self.query_expander.expand_sync(query)
                    print(f"[RAGSearch] Original: '{query}' | Expanded: '{expanded_query}'")
                except Exception as e:
                    print(f"[RAGSearch] Error en query expansion, usando query original: {e}")
                    expanded_query = query

            # Búsqueda vectorial con query expandida
            query_embedding = self._compute_query_embedding(expanded_query)
            similarities, indices = self.faiss_index.search(
                query_embedding.astype('float32'),
                top_k
            )

            results = self._rank_results(similarities[0], indices[0], similarity_threshold)

            print(f"[RAGSearch] FAISS búsqueda: {len(results)} resultados (top_k={top_k})")

            # Re-ranking: Re-ordenar top-20 de FAISS a top-3 con CrossEncoder
            if settings.reranker_enabled and self.reranker and len(results) > 0:
                # Métricas pre-reranking
                if results:
                    faiss_top_score = results[0].get('similarity_score', 'N/A')
                    print(f"[RAGSearch] FAISS top-1 score: {faiss_top_score}")

                # Aplicar re-ranking
                reranked_results = self.reranker.rerank(
                    query=query,  # Usar query original para re-ranking
                    docs=results,
                    top_k=settings.reranker_top_k
                )

                # Métricas post-reranking
                if reranked_results:
                    reranked_top_score = reranked_results[0].get('rerank_score', 'N/A')
                    print(f"[RAGSearch] Reranked top-1 score: {reranked_top_score}")
                    print(f"[RAGSearch] Final results: {len(reranked_results)} docs (after re-ranking)")

                return reranked_results
            else:
                # Feature flag deshabilitado o sin reranker: retornar top-3 de FAISS
                top_3_results = results[:3]
                print(f"[RAGSearch] Re-ranking deshabilitado, retornando top-{len(top_3_results)} de FAISS")
                return top_3_results

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
        relevant_docs = self.search_similar_documents(query, top_k=20)  # Incrementado a 20 para re-ranking

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