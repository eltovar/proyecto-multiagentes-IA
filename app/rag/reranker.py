"""
Re-Ranker: Re-ordena documentos candidatos usando CrossEncoder.
Mejora la precisión de recuperación mediante relevancia semántica profunda.
"""

from typing import List, Dict, Any, Optional
from sentence_transformers import CrossEncoder
import time


class ReRanker:
    """
    Re-ordena documentos candidatos usando CrossEncoder para mejorar precisión.

    Modelo: cross-encoder/ms-marco-MiniLM-L-6-v2
    - Rápido: ~50ms por doc en CPU
    - Entrenado para ranking
    - Compatible con español (multilingüe limitado)

    Optimizaciones:
    - Lazy loading: modelo se carga solo en primera llamada
    - Singleton pattern: una sola instancia del modelo en memoria (~90MB)
    - Fallback: retorna docs sin re-ranking si falla carga
    """

    _model_cache: Optional[CrossEncoder] = None  # Caché a nivel de clase
    _model_name_cache: Optional[str] = None
    _load_failed: bool = False  # Flag para evitar reintentos

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        """
        Inicializa el ReRanker con lazy loading y caché (singleton pattern).

        Args:
            model_name: Nombre del modelo CrossEncoder en HuggingFace

        Note:
            El modelo se carga en primera llamada a rerank(), no en __init__
        """
        self.model_name = model_name
        self.model: Optional[CrossEncoder] = None

    def _load_model(self) -> bool:
        """
        Carga el modelo CrossEncoder (lazy loading con caché).

        Returns:
            True si carga exitosa, False si falla

        Note:
            Primera llamada: ~2s (descarga + carga)
            Llamadas siguientes: <100ms (desde caché)
        """
        # Si ya falló previamente, no reintentar
        if ReRanker._load_failed:
            return False

        # Si modelo ya está en caché, reutilizar
        if ReRanker._model_cache is not None and ReRanker._model_name_cache == self.model_name:
            self.model = ReRanker._model_cache
            print(f"[ReRanker] Reutilizando modelo desde caché (singleton)")
            return True

        # Cargar modelo por primera vez
        try:
            print(f"[ReRanker] Cargando modelo: {self.model_name}")
            start_time = time.time()

            self.model = CrossEncoder(self.model_name, max_length=512)

            load_time = time.time() - start_time
            print(f"[ReRanker] ReRanker model loaded successfully ({load_time:.2f}s)")

            # Guardar en caché
            ReRanker._model_cache = self.model
            ReRanker._model_name_cache = self.model_name

            return True

        except Exception as e:
            print(f"[ReRanker] WARNING: Failed to load model: {e}")
            print(f"[ReRanker] Re-ranking deshabilitado, retornando docs sin re-ranking")
            ReRanker._load_failed = True
            return False

    def rerank(
        self,
        query: str,
        docs: List[Dict[str, Any]],
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Re-ordena documentos candidatos por relevancia usando CrossEncoder.

        Args:
            query: Consulta original del usuario
            docs: Lista de documentos candidatos de FAISS
            top_k: Número de documentos top a retornar (default: 3)

        Returns:
            Lista de documentos re-ordenados (top-k por score descendente)

        Example:
            >>> reranker = ReRanker()
            >>> docs = [{"content": "doc1"}, {"content": "doc2"}]
            >>> reranked = reranker.rerank("query", docs, top_k=3)
        """
        if not docs:
            return []

        # Lazy loading: cargar modelo solo en primera llamada
        if self.model is None:
            if not self._load_model():
                # Fallback: si falla carga, retornar docs sin re-ranking
                print(f"[ReRanker] Modelo no disponible, retornando top-{top_k} sin re-ranking")
                return docs[:top_k]

        if len(docs) <= top_k:
            # Si hay menos o igual docs que top_k, no tiene sentido re-rankear
            print(f"[ReRanker] Solo {len(docs)} docs, retornando todos sin re-ranking")
            return docs

        try:
            # Preparar pares (query, doc.content) para el modelo
            pairs = []
            for doc in docs:
                content = doc.get('content', '')
                title = doc.get('title', '')
                # Combinar título y contenido para mejor contexto
                full_text = f"{title} {content}" if title else content
                pairs.append([query, full_text])

            # Obtener scores de relevancia del CrossEncoder
            scores = self.model.predict(pairs)

            # Agregar scores a documentos
            for i, doc in enumerate(docs):
                doc['rerank_score'] = float(scores[i])

            # Ordenar por score descendente (mayor score = más relevante)
            reranked_docs = sorted(docs, key=lambda x: x['rerank_score'], reverse=True)

            # Retornar top-k
            top_docs = reranked_docs[:top_k]

            print(f"[ReRanker] Re-ranking completado: {len(docs)} docs -> top-{top_k}")

            # Log de top-3 scores
            top_3_scores = [f"{d['rerank_score']:.3f}" for d in top_docs[:3]]
            print(f"[ReRanker] Top-3 scores: {top_3_scores}")

            return top_docs

        except Exception as e:
            print(f"[ReRanker] Error en re-ranking: {e}")
            # Fallback: retornar top-k originales sin re-ranking
            return docs[:top_k]
