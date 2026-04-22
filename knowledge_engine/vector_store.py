"""Simple vector store using numpy (no ChromaDB required)."""

import json
from pathlib import Path
from typing import List, Optional

import numpy as np


class NumpyVectorStore:
    """In-memory vector store with cosine similarity search."""

    def __init__(self, dim: int = 128, persist_dir: Optional[str] = None):
        self.dim = dim
        self.vectors = np.zeros((0, dim), dtype=np.float32)
        self.documents = []
        self.persist_dir = Path(persist_dir) if persist_dir else None

    def add(self, embeddings: np.ndarray, documents: List[dict]):
        """Add embeddings and associated documents."""
        if embeddings.shape[1] != self.dim:
            raise ValueError(f"Expected dim {self.dim}, got {embeddings.shape[1]}")
        self.vectors = np.vstack([self.vectors, embeddings]) if self.vectors.size else embeddings
        self.documents.extend(documents)

    def search(self, query_embedding: np.ndarray, top_k: int = 5) -> List[dict]:
        """Return top-k most similar documents."""
        if len(self.vectors) == 0:
            return []

        # Cosine similarity
        query_norm = query_embedding / (np.linalg.norm(query_embedding) + 1e-10)
        vectors_norm = self.vectors / (np.linalg.norm(self.vectors, axis=1, keepdims=True) + 1e-10)
        similarities = vectors_norm @ query_norm.T  # shape: (N, 1)
        similarities = similarities.flatten()

        top_indices = np.argsort(similarities)[::-1][:top_k]
        results = []
        for idx in top_indices:
            results.append({
                "score": float(similarities[idx]),
                "document": self.documents[idx],
            })
        return results

    def save(self, path: Optional[str] = None):
        """Persist vectors and documents."""
        save_dir = self.persist_dir or Path(path).parent
        save_dir.mkdir(parents=True, exist_ok=True)

        np.save(save_dir / "vectors.npy", self.vectors)
        with open(save_dir / "documents.json", "w", encoding="utf-8") as f:
            json.dump(self.documents, f, ensure_ascii=False, indent=2)

    def load(self, path: Optional[str] = None):
        """Load persisted vectors and documents."""
        load_dir = self.persist_dir or Path(path).parent
        vectors_path = load_dir / "vectors.npy"
        docs_path = load_dir / "documents.json"

        if vectors_path.exists() and docs_path.exists():
            self.vectors = np.load(vectors_path)
            with open(docs_path, "r", encoding="utf-8") as f:
                self.documents = json.load(f)
            self.dim = self.vectors.shape[1]
