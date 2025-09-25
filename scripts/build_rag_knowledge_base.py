#!/usr/bin/env python3
"""
Utilizado para desarrollo y despliegue.
Script para construir la base de conocimiento RAG del sistema multiagentes.

Este script:
1. Lee archivos de conocimiento desde knowledge_base/
2. Genera embeddings usando sentence-transformers
3. Crea índice FAISS para búsqueda semántica
4. Guarda la base de conocimiento para el Agente de Soporte
"""

import os
import json
import pickle
from pathlib import Path
from typing import List, Dict, Any
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss

# Configuración
KNOWLEDGE_BASE_DIR = "knowledge_base"
RAG_OUTPUT_DIR = "data/rag"
EMBEDDINGS_MODEL = "all-MiniLM-L6-v2"  # Modelo ligero y eficiente
VECTOR_DIMENSION = 384  # Dimensión del modelo MiniLM-L6-v2

class RAGKnowledgeBuilder:
    """
    Constructor de base de conocimiento RAG para el Agente de Soporte.

    Procesa documentos de texto y crea un índice vectorial para búsqueda semántica.
    """

    def __init__(self):
        self.model = None
        self.documents = []
        self.embeddings = None
        self.faiss_index = None

    def load_embedding_model(self):
        """Carga el modelo de embeddings de sentence-transformers."""
        print("🔄 Cargando modelo de embeddings...")
        self.model = SentenceTransformer(EMBEDDINGS_MODEL)
        print(f"✅ Modelo {EMBEDDINGS_MODEL} cargado correctamente")

    def load_knowledge_documents(self) -> List[Dict[str, Any]]:
        """
        Carga todos los documentos de la carpeta knowledge_base/.

        Soporta archivos:
        - .txt: Texto plano
        - .md: Markdown
        - .json: JSON con estructura {"title": "", "content": ""}

        Returns:
            List[Dict]: Lista de documentos con id, title, content, source
        """
        documents = []
        knowledge_path = Path(KNOWLEDGE_BASE_DIR)

        if not knowledge_path.exists():
            print(f"⚠️  Directorio {KNOWLEDGE_BASE_DIR} no existe. Creando...")
            knowledge_path.mkdir(parents=True, exist_ok=True)

            # Crear documento de ejemplo
            example_doc = knowledge_path / "empresa_info.txt"
            example_doc.write_text("""
Información sobre nuestra empresa:

Somos una empresa especializada en soluciones tecnológicas para automatización de procesos de ventas.

Nuestros servicios incluyen:
- Automatización de WhatsApp Business
- Integración con CRMs
- Sistemas de inteligencia artificial
- Consultoría en procesos de ventas

Horarios de atención:
- Lunes a Viernes: 8:00 AM - 6:00 PM
- Sábados: 9:00 AM - 2:00 PM
- Domingos: Cerrado

Contacto:
- Teléfono: +57 (1) 234-5678
- Email: info@empresa.com
- WhatsApp: +57 300 123 4567
            """, encoding='utf-8')

            print(f"📄 Documento de ejemplo creado: {example_doc}")

        print(f"🔍 Buscando documentos en {knowledge_path}...")

        doc_id = 0
        for file_path in knowledge_path.rglob("*"):
            if file_path.is_file() and file_path.suffix in ['.txt', '.md', '.json']:
                try:
                    doc_content = self._load_document_content(file_path)
                    if doc_content:
                        documents.append({
                            "id": doc_id,
                            "title": file_path.stem,
                            "content": doc_content,
                            "source": str(file_path),
                            "file_type": file_path.suffix
                        })
                        doc_id += 1
                        print(f"📖 Cargado: {file_path}")

                except Exception as e:
                    print(f"❌ Error cargando {file_path}: {e}")

        print(f"✅ {len(documents)} documentos cargados")
        return documents

    def _load_document_content(self, file_path: Path) -> str:
        """Carga el contenido de un archivo según su tipo."""
        try:
            if file_path.suffix == '.json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Esperamos formato {"title": "", "content": ""}
                    if isinstance(data, dict):
                        title = data.get('title', '')
                        content = data.get('content', '')
                        return f"{title}\n\n{content}" if title else content
                    return str(data)
            else:
                # .txt o .md
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read().strip()
        except Exception as e:
            print(f"Error leyendo {file_path}: {e}")
            return ""

    def generate_embeddings(self, documents: List[Dict[str, Any]]) -> np.ndarray:
        """
        Genera embeddings para todos los documentos.

        Args:
            documents: Lista de documentos con campo 'content'

        Returns:
            np.ndarray: Array de embeddings
        """
        print("🔄 Generando embeddings...")

        # Extraer contenido de documentos
        texts = [doc['content'] for doc in documents]

        # Generar embeddings
        embeddings = self.model.encode(
            texts,
            show_progress_bar=True,
            convert_to_numpy=True
        )

        print(f"✅ {len(embeddings)} embeddings generados")
        print(f"📏 Dimensión de embeddings: {embeddings.shape[1]}")

        return embeddings

    def build_faiss_index(self, embeddings: np.ndarray) -> faiss.Index:
        """
        Construye índice FAISS para búsqueda vectorial eficiente.

        Args:
            embeddings: Array de embeddings

        Returns:
            faiss.Index: Índice FAISS construido
        """
        print("🔄 Construyendo índice FAISS...")

        dimension = embeddings.shape[1]

        # Usar IndexFlatIP (Inner Product) para similarity search
        index = faiss.IndexFlatIP(dimension)

        # Normalizar embeddings para usar cosine similarity
        faiss.normalize_L2(embeddings)

        # Agregar embeddings al índice
        index.add(embeddings.astype('float32'))

        print(f"✅ Índice FAISS construido con {index.ntotal} vectores")
        return index

    def save_knowledge_base(
        self,
        documents: List[Dict[str, Any]],
        embeddings: np.ndarray,
        faiss_index: faiss.Index
    ):
        """
        Guarda la base de conocimiento completa.

        Args:
            documents: Lista de documentos
            embeddings: Array de embeddings
            faiss_index: Índice FAISS
        """
        print("💾 Guardando base de conocimiento...")

        # Crear directorio de salida
        output_path = Path(RAG_OUTPUT_DIR)
        output_path.mkdir(parents=True, exist_ok=True)

        # Guardar documentos
        documents_path = output_path / "documents.json"
        with open(documents_path, 'w', encoding='utf-8') as f:
            json.dump(documents, f, ensure_ascii=False, indent=2)

        # Guardar embeddings
        embeddings_path = output_path / "embeddings.npy"
        np.save(embeddings_path, embeddings)

        # Guardar índice FAISS
        index_path = output_path / "faiss_index.bin"
        faiss.write_index(faiss_index, str(index_path))

        # Guardar metadatos
        metadata = {
            "model_name": EMBEDDINGS_MODEL,
            "vector_dimension": VECTOR_DIMENSION,
            "num_documents": len(documents),
            "created_at": str(np.datetime64('now'))
        }

        metadata_path = output_path / "metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)

        print(f"✅ Base de conocimiento guardada en {output_path}")
        print(f"📊 Archivos creados:")
        print(f"   - {documents_path}")
        print(f"   - {embeddings_path}")
        print(f"   - {index_path}")
        print(f"   - {metadata_path}")

    def build_complete_knowledge_base(self):
        """Ejecuta el proceso completo de construcción de la base de conocimiento."""
        print("🚀 Iniciando construcción de base de conocimiento RAG")
        print("=" * 60)

        # 1. Cargar modelo
        self.load_embedding_model()

        # 2. Cargar documentos
        self.documents = self.load_knowledge_documents()

        if not self.documents:
            print("⚠️  No se encontraron documentos. Terminando...")
            return False

        # 3. Generar embeddings
        self.embeddings = self.generate_embeddings(self.documents)

        # 4. Construir índice FAISS
        self.faiss_index = self.build_faiss_index(self.embeddings)

        # 5. Guardar todo
        self.save_knowledge_base(self.documents, self.embeddings, self.faiss_index)

        print("=" * 60)
        print("🎉 Base de conocimiento RAG construida exitosamente")
        return True

def main():
    """Función principal del script."""
    builder = RAGKnowledgeBuilder()
    success = builder.build_complete_knowledge_base()

    if success:
        print("\n🔧 Para usar la base de conocimiento:")
        print("   1. El Agente de Soporte cargará automáticamente estos archivos")
        print("   2. Puede agregar más documentos a knowledge_base/ y reconstruir")
        print("   3. Use 'python scripts/build_rag_knowledge_base.py' para actualizar")
        return 0
    else:
        print("\n❌ Error construyendo base de conocimiento")
        return 1

if __name__ == "__main__":
    exit(main())