"""
Query Expander: Expande consultas para mejorar recuperación en RAG.
Transforma consultas coloquiales en queries optimizadas para búsqueda vectorial.
"""

from typing import Optional
from app.prompts.rag_prompts import QUERY_EXPANSION_SYSTEM, QUERY_EXPANSION_USER


class QueryExpander:
    """
    Expande consultas usando LLM para mejorar la recuperación de documentos relevantes.

    Estrategia: LLM-based expansion con límite de tokens adicionales.
    """

    def __init__(self, llm_service):
        """
        Inicializa el QueryExpander.

        Args:
            llm_service: Instancia de LLMService para generar expansiones
        """
        self.llm = llm_service

    async def expand(self, query: str) -> str:
        """
        Expande una consulta agregando sinónimos y términos relacionados.

        Args:
            query: Consulta original del usuario

        Returns:
            Query expandida con términos adicionales (máximo 20 tokens adicionales)

        Example:
            >>> expander = QueryExpander(llm_service)
            >>> await expander.expand("gotera urgente")
            "gotera urgente reparación mantenimiento daño agua filtración"
        """
        if not query or len(query.strip()) == 0:
            return query

        try:
            # Construir prompt con query original
            user_prompt = QUERY_EXPANSION_USER.format(query=query)

            # Llamar a LLM con prompt de expansión
            result = await self.llm.api_client.client.chat.completions.create(
                model="gpt-4o-mini",  # Modelo rápido para expansión
                messages=[
                    {"role": "system", "content": QUERY_EXPANSION_SYSTEM},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,  # Baja temperatura para consistencia
                max_tokens=100  # Suficiente para query expandida
            )

            # Extraer query expandida
            expanded_query = result.choices[0].message.content.strip()

            # Validar longitud (máximo 20 tokens adicionales)
            original_tokens = len(query.split())
            expanded_tokens = len(expanded_query.split())

            if expanded_tokens > original_tokens + 20:
                # Truncar a límite de tokens
                tokens = expanded_query.split()
                expanded_query = " ".join(tokens[:original_tokens + 20])

            print(f"[QueryExpander] Original: '{query}' → Expandida: '{expanded_query}'")

            return expanded_query

        except Exception as e:
            print(f"[QueryExpander] Error expandiendo query: {e}")
            # Fallback: retornar query original si falla expansión
            return query

    def expand_sync(self, query: str) -> str:
        """
        Versión síncrona de expand() para compatibilidad.

        Args:
            query: Consulta original del usuario

        Returns:
            Query expandida (o query original si no se puede expandir)
        """
        import asyncio

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Si ya hay un loop corriendo, usar run_until_complete puede fallar
                # En este caso, retornar query original
                print("[QueryExpander] Loop ya corriendo, retornando query original")
                return query
            else:
                return loop.run_until_complete(self.expand(query))
        except Exception as e:
            print(f"[QueryExpander] Error en expand_sync: {e}")
            return query
