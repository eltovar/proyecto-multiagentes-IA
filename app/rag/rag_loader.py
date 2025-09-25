"""
RAG Loader: Carga de documentos, embeddings y modelos.
Responsable de la inicialización de todos los componentes RAG.
"""

import os
import json
import numpy as np
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
import faiss
from pathlib import Path

class RAGLoader:

    def __init__(self, rag_data_path: str):
        self.rag_data_path = Path(rag_data_path)
        self.model = None
        self.documents = []
        self.embeddings = None
        self.faiss_index = None
        self.metadata = {}

    def _check_rag_files(self) -> bool:
        required_files = [
            "documents.json",
            "embeddings.npy",
            "faiss_index.bin",
            "metadata.json"
        ]

        for filename in required_files:
            file_path = self.rag_data_path / filename
            if not file_path.exists():
                print(f"[RAGLoader] Archivo requerido no encontrado: {file_path}")
                return False

        return True

    def _load_embedding_model(self):
        print("[RAGLoader] Cargando modelo de embeddings")
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        return self.model

    def _load_documents(self):
        documents_path = self.rag_data_path / "documents.json"
        with open(documents_path, 'r', encoding='utf-8') as f:
            self.documents = json.load(f)

        print(f"[RAGLoader] Cargados {len(self.documents)} documentos")
        return self.documents

    def _load_embeddings(self):
        embeddings_path = self.rag_data_path / "embeddings.npy"
        self.embeddings = np.load(embeddings_path)

        print(f"[RAGLoader] Cargados embeddings: {self.embeddings.shape}")
        return self.embeddings

    def _load_faiss_index(self):
        index_path = self.rag_data_path / "faiss_index.bin"
        self.faiss_index = faiss.read_index(str(index_path))

        print(f"[RAGLoader] Índice FAISS cargado: {self.faiss_index.ntotal} vectores")
        return self.faiss_index

    def _load_metadata(self):
        metadata_path = self.rag_data_path / "metadata.json"
        with open(metadata_path, 'r', encoding='utf-8') as f:
            self.metadata = json.load(f)
        return self.metadata

    def load_all_components(self) -> Dict[str, Any]:
        if not self._check_rag_files():
            return {"success": False, "error": "Archivos RAG no encontrados"}

        try:
            model = self._load_embedding_model()
            documents = self._load_documents()
            embeddings = self._load_embeddings()
            faiss_index = self._load_faiss_index()
            metadata = self._load_metadata()

            return {
                "success": True,
                "model": model,
                "documents": documents,
                "embeddings": embeddings,
                "faiss_index": faiss_index,
                "metadata": metadata
            }

        except Exception as e:
            print(f"[RAGLoader] Error cargando componentes: {e}")
            return {"success": False, "error": str(e)}