"""
Script de evaluación de RAG con Query Expansion + Re-ranking
Calcula métricas de precisión y recall comparando con/sin mejoras
"""

import json
import time
import sys
from typing import List, Dict, Any, Tuple
from pathlib import Path

# Agregar path del proyecto
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.rag.rag_system import RAGSystem
from app.rag.query_expander import QueryExpander
from app.rag.reranker import ReRanker
from app.services.llm_service import LLMService


class RAGEvaluator:
    """Evaluador de rendimiento del sistema RAG"""

    def __init__(self, dataset_path: str):
        """
        Inicializa evaluador con dataset de queries.

        Args:
            dataset_path: Ruta al archivo rag_eval_queries.json
        """
        self.dataset_path = dataset_path
        self.queries = self._load_dataset()
        self.results = []

    def _load_dataset(self) -> List[Dict[str, Any]]:
        """Carga dataset de evaluación desde JSON"""
        with open(self.dataset_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"[Evaluator] Cargadas {len(data)} queries de evaluacion")
        return data

    def evaluate_query(
        self,
        query_data: Dict[str, Any],
        rag_system: RAGSystem
    ) -> Dict[str, Any]:
        """
        Evalúa una query individual.

        Args:
            query_data: Diccionario con query y expected values
            rag_system: Sistema RAG a evaluar

        Returns:
            Dict con resultados de evaluación
        """
        query = query_data["query"]
        expected_filename = query_data["expected_doc_filename"]
        expected_phone = query_data.get("expected_phone")
        expected_keywords = query_data.get("expected_keywords", [])

        # Ejecutar búsqueda
        start_time = time.time()
        result = rag_system.search_context(query)
        latency_ms = (time.time() - start_time) * 1000

        docs = result.get("documents", [])
        phones = result.get("phone_numbers", [])

        # Verificar posición del documento esperado
        doc_position = None
        for i, doc in enumerate(docs[:3], 1):  # Solo top-3
            if doc.get("filename") == expected_filename:
                doc_position = i
                break

        # Verificar extracción de teléfono
        phone_extracted = expected_phone in phones if expected_phone else None

        # Verificar keywords en top-1
        keywords_found = 0
        if docs:
            top_doc_content = docs[0].get("content", "").lower()
            keywords_found = sum(
                1 for kw in expected_keywords
                if kw.lower() in top_doc_content
            )

        keyword_match_rate = (
            keywords_found / len(expected_keywords)
            if expected_keywords else 0.0
        )

        return {
            "query": query,
            "category": query_data["category"],
            "expected_filename": expected_filename,
            "doc_position": doc_position,
            "phone_extracted": phone_extracted,
            "keyword_match_rate": keyword_match_rate,
            "latency_ms": latency_ms,
            "docs_retrieved": len(docs)
        }

    def calculate_metrics(self, results: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Calcula métricas agregadas.

        Métricas:
        - Recall@3: % queries donde doc esperado está en top-3
        - MRR: Mean Reciprocal Rank (promedio de 1/posición)
        - Precision@1: % queries donde doc esperado está en posición 1
        - Phone Accuracy: % queries con teléfono extraído correctamente
        - Avg Latency: Latencia promedio en ms

        Args:
            results: Lista de resultados de evaluación

        Returns:
            Dict con métricas calculadas
        """
        total = len(results)

        # Recall@3: doc esperado en top-3
        recall_at_3 = sum(
            1 for r in results
            if r["doc_position"] is not None
        ) / total

        # MRR: Mean Reciprocal Rank
        reciprocal_ranks = [
            1.0 / r["doc_position"] if r["doc_position"] else 0.0
            for r in results
        ]
        mrr = sum(reciprocal_ranks) / total

        # Precision@1: doc esperado en posición 1
        precision_at_1 = sum(
            1 for r in results
            if r["doc_position"] == 1
        ) / total

        # Phone Accuracy (solo queries que esperan teléfono)
        phone_queries = [r for r in results if r["phone_extracted"] is not None]
        phone_accuracy = (
            sum(1 for r in phone_queries if r["phone_extracted"])
            / len(phone_queries)
            if phone_queries else 0.0
        )

        # Keyword Match Rate (promedio)
        avg_keyword_match = sum(
            r["keyword_match_rate"] for r in results
        ) / total

        # Latencia promedio
        avg_latency = sum(r["latency_ms"] for r in results) / total

        return {
            "recall_at_3": recall_at_3,
            "mrr": mrr,
            "precision_at_1": precision_at_1,
            "phone_accuracy": phone_accuracy,
            "avg_keyword_match": avg_keyword_match,
            "avg_latency_ms": avg_latency,
            "total_queries": total
        }

    def run_evaluation(
        self,
        rag_system: RAGSystem,
        mode: str = "with_improvements"
    ) -> Dict[str, Any]:
        """
        Ejecuta evaluación completa del sistema.

        Args:
            rag_system: Sistema RAG a evaluar
            mode: "with_improvements" o "baseline"

        Returns:
            Dict con métricas y resultados
        """
        print(f"\n[Evaluator] Iniciando evaluacion en modo: {mode}")
        print("=" * 80)

        results = []
        for i, query_data in enumerate(self.queries, 1):
            print(f"\rEvaluando query {i}/{len(self.queries)}: '{query_data['query'][:40]}...'", end="")

            result = self.evaluate_query(query_data, rag_system)
            results.append(result)

        print("\n")

        # Calcular métricas
        metrics = self.calculate_metrics(results)

        return {
            "mode": mode,
            "metrics": metrics,
            "results": results
        }

    def print_report(
        self,
        baseline: Dict[str, Any],
        improved: Dict[str, Any]
    ):
        """
        Imprime reporte comparativo en consola.

        Args:
            baseline: Resultados sin mejoras
            improved: Resultados con mejoras
        """
        print("\n" + "="*80)
        print("REPORTE DE EVALUACION RAG")
        print("="*80 + "\n")

        baseline_metrics = baseline["metrics"]
        improved_metrics = improved["metrics"]

        # Tabla comparativa
        print("METRICAS COMPARATIVAS:")
        print("-" * 80)
        print(f"{'Metrica':<25} | {'Baseline':<15} | {'Con Mejoras':<15} | {'Delta':<10}")
        print("-" * 80)

        metrics_to_show = [
            ("Recall@3", "recall_at_3", "%"),
            ("MRR", "mrr", ""),
            ("Precision@1", "precision_at_1", "%"),
            ("Phone Accuracy", "phone_accuracy", "%"),
            ("Avg Keyword Match", "avg_keyword_match", "%"),
            ("Avg Latency (ms)", "avg_latency_ms", "ms")
        ]

        for label, key, unit in metrics_to_show:
            baseline_val = baseline_metrics[key]
            improved_val = improved_metrics[key]
            delta = improved_val - baseline_val

            if unit == "%":
                baseline_str = f"{baseline_val*100:.1f}%"
                improved_str = f"{improved_val*100:.1f}%"
                delta_str = f"+{delta*100:.1f}%" if delta >= 0 else f"{delta*100:.1f}%"
            elif unit == "ms":
                baseline_str = f"{baseline_val:.0f}ms"
                improved_str = f"{improved_val:.0f}ms"
                delta_str = f"+{delta:.0f}ms" if delta >= 0 else f"{delta:.0f}ms"
            else:
                baseline_str = f"{baseline_val:.3f}"
                improved_str = f"{improved_val:.3f}"
                delta_str = f"+{delta:.3f}" if delta >= 0 else f"{delta:.3f}"

            print(f"{label:<25} | {baseline_str:<15} | {improved_str:<15} | {delta_str:<10}")

        print("-" * 80)

        # Casos exitosos/fallidos
        print("\nANALISIS POR CATEGORIA:")
        print("-" * 80)

        categories = set(q["category"] for q in self.queries)
        for category in categories:
            cat_results_baseline = [
                r for r in baseline["results"]
                if r["category"] == category
            ]
            cat_results_improved = [
                r for r in improved["results"]
                if r["category"] == category
            ]

            baseline_p1 = sum(1 for r in cat_results_baseline if r["doc_position"] == 1)
            improved_p1 = sum(1 for r in cat_results_improved if r["doc_position"] == 1)
            total = len(cat_results_baseline)

            print(f"{category:<25} | Baseline P@1: {baseline_p1}/{total} ({baseline_p1/total*100:.0f}%) | Con Mejoras: {improved_p1}/{total} ({improved_p1/total*100:.0f}%)")

        print("-" * 80)

        # Resumen
        print("\nRESUMEN:")
        print(f"Total queries evaluadas: {baseline_metrics['total_queries']}")
        print(f"Mejora en Recall@3: {(improved_metrics['recall_at_3'] - baseline_metrics['recall_at_3'])*100:.1f} puntos porcentuales")
        print(f"Mejora en Precision@1: {(improved_metrics['precision_at_1'] - baseline_metrics['precision_at_1'])*100:.1f} puntos porcentuales")

        print("\n" + "="*80)
        print("EVALUACION COMPLETADA")
        print("="*80 + "\n")


def main():
    """Función principal de evaluación"""

    print("\n" + "="*80)
    print("EVALUACION DE RAG: Query Expansion + Re-ranking")
    print("="*80 + "\n")

    # 1. Cargar dataset
    dataset_path = "tests/data/rag_eval_queries.json"
    evaluator = RAGEvaluator(dataset_path)

    # 2. Inicializar servicios
    print("[1/4] Inicializando servicios...")
    llm_service = LLMService()
    if not llm_service.initialize():
        print("ERROR: No se pudo inicializar LLMService")
        return

    query_expander = QueryExpander(llm_service)
    reranker = ReRanker()
    print("OK\n")

    # 3. Evaluación BASELINE (sin mejoras)
    print("[2/4] Evaluando BASELINE (sin Query Expansion ni Re-ranking)...")
    rag_baseline = RAGSystem(
        rag_data_path="data/rag",
        query_expander=None,  # Sin query expansion
        reranker=None  # Sin re-ranking
    )
    if not rag_baseline.initialize():
        print("ERROR: No se pudo inicializar RAGSystem baseline")
        return

    baseline_results = evaluator.run_evaluation(rag_baseline, mode="baseline")

    # 4. Evaluación CON MEJORAS
    print("[3/4] Evaluando CON MEJORAS (Query Expansion + Re-ranking)...")
    rag_improved = RAGSystem(
        rag_data_path="data/rag",
        query_expander=query_expander,
        reranker=reranker
    )
    if not rag_improved.initialize():
        print("ERROR: No se pudo inicializar RAGSystem improved")
        return

    improved_results = evaluator.run_evaluation(rag_improved, mode="with_improvements")

    # 5. Generar reporte
    print("[4/4] Generando reporte...")
    evaluator.print_report(baseline_results, improved_results)

    # Guardar resultados en JSON (opcional)
    output_file = "tests/data/evaluation_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "baseline": baseline_results,
            "improved": improved_results,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }, f, indent=2, ensure_ascii=False)

    print(f"Resultados guardados en: {output_file}")


if __name__ == "__main__":
    main()
