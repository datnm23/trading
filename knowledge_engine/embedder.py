"""Lightweight embedder using TF-IDF + SVD (no heavy dependencies)."""

import re

import numpy as np
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer


class SimpleEmbedder:
    """Create dense embeddings from text using TF-IDF + SVD."""

    def __init__(self, n_components: int = 128):
        self.n_components = n_components
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words="english",
            ngram_range=(1, 2),
            min_df=2,
        )
        self.svd = TruncatedSVD(n_components=n_components)
        self.is_fitted = False

    def _preprocess(self, text: str) -> str:
        """Clean markdown and normalize text."""
        # Remove markdown links, headings, code blocks
        text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
        text = re.sub(r"#+", "", text)
        text = re.sub(r"`{1,3}[^`]*`{1,3}", "", text)
        text = re.sub(r"[^\w\s]", " ", text)
        text = re.sub(r"\s+", " ", text).lower().strip()
        return text

    def fit_transform(self, texts: list[str]) -> np.ndarray:
        """Fit on texts and return embeddings."""
        cleaned = [self._preprocess(t) for t in texts]
        tfidf = self.vectorizer.fit_transform(cleaned)
        embeddings = self.svd.fit_transform(tfidf)
        self.is_fitted = True
        return embeddings

    def transform(self, texts: list[str]) -> np.ndarray:
        """Transform new texts using fitted model."""
        if not self.is_fitted:
            raise RuntimeError("Embedder not fitted. Call fit_transform first.")
        cleaned = [self._preprocess(t) for t in texts]
        tfidf = self.vectorizer.transform(cleaned)
        return self.svd.transform(tfidf)

    def save(self, path: str):
        """Save fitted model."""
        import pickle

        with open(path, "wb") as f:
            pickle.dump(
                {
                    "vectorizer": self.vectorizer,
                    "svd": self.svd,
                    "is_fitted": self.is_fitted,
                    "n_components": self.n_components,
                },
                f,
            )

    def load(self, path: str):
        """Load fitted model."""
        import pickle

        with open(path, "rb") as f:
            data = pickle.load(f)
        self.vectorizer = data["vectorizer"]
        self.svd = data["svd"]
        self.is_fitted = data["is_fitted"]
        self.n_components = data["n_components"]
