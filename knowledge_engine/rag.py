"""RAG-based knowledge engine using crawled wiki."""

from pathlib import Path

import yaml
from loguru import logger

from knowledge_engine.embedder import SimpleEmbedder
from knowledge_engine.vector_store import NumpyVectorStore


class WikiRAG:
    """Retrieve relevant concepts from Turtle Trading Wiki using vector search."""

    def __init__(
        self,
        wiki_dir: str = "./crawl-wiki/concepts",
        persist_dir: str = "./knowledge/vector_store",
        top_k: int = 5,
    ):
        self.wiki_dir = Path(wiki_dir)
        self.persist_dir = Path(persist_dir)
        self.top_k = top_k
        self.embedder = SimpleEmbedder(n_components=128)
        self.store = NumpyVectorStore(dim=128, persist_dir=persist_dir)
        self._is_built = False

        # Try to load existing index
        if (self.persist_dir / "vectors.npy").exists() and (
            self.persist_dir / "embedder.pkl"
        ).exists():
            self.store.load()
            self.embedder.load(self.persist_dir / "embedder.pkl")
            self._is_built = True
            logger.info(f"Loaded existing index: {len(self.store.documents)} documents")

    def build_index(self, force: bool = False):
        """Build vector index from all wiki concepts."""
        if self._is_built and not force:
            logger.info("Index already built. Use force=True to rebuild.")
            return

        if not self.wiki_dir.exists():
            logger.warning(f"Wiki dir not found: {self.wiki_dir}")
            return

        texts = []
        documents = []

        for md_file in sorted(self.wiki_dir.glob("*.md")):
            content = md_file.read_text(encoding="utf-8")
            title = md_file.stem

            # Parse frontmatter and body
            body = content
            if content.startswith("---"):
                try:
                    _, fm, body = content.split("---", 2)
                    meta = yaml.safe_load(fm)
                    title = meta.get("title", title)
                except Exception:
                    pass

            # Use title + first 800 chars of body as embedding text
            text = f"{title}\n{body[:2000]}"
            texts.append(text)
            documents.append(
                {
                    "id": md_file.stem,
                    "title": title,
                    "source_url": meta.get("source_url", "") if "meta" in dir() else "",
                    "content": body[:3000],
                }
            )

        logger.info(f"Building index from {len(texts)} concepts...")
        embeddings = self.embedder.fit_transform(texts)
        self.store.add(embeddings, documents)
        self.store.save()
        self.embedder.save(self.persist_dir / "embedder.pkl")
        self._is_built = True
        logger.info(f"Index built: {len(documents)} documents")

    def search(self, query: str) -> list[dict]:
        """Semantic search over wiki concepts."""
        if not self._is_built:
            self.build_index()
        if not self._is_built:
            return []

        query_embedding = self.embedder.transform([query])[0]
        results = self.store.search(query_embedding, top_k=self.top_k)
        return results

    def get_context(self, query: str, max_chars: int = 3000) -> str:
        """Return formatted context string for LLM prompting."""
        results = self.search(query)
        if not results:
            return ""

        parts = []
        total_chars = 0
        for r in results:
            doc = r["document"]
            chunk = f"### {doc['title']} (relevance: {r['score']:.3f})\n{doc['content'][:800]}"
            if total_chars + len(chunk) > max_chars:
                break
            parts.append(chunk)
            total_chars += len(chunk)

        return "\n\n".join(parts)

    def query(self, question: str, llm_client=None) -> str:
        """Full RAG query: retrieve + (optionally) LLM generate."""
        context = self.get_context(question)
        if not llm_client:
            return context

        prompt = f"""Bạn là một chuyên gia giao dịch. Dựa trên kiến thức sau:

{context}

Hãy trả lợi câu hỏi: {question}
"""
        return llm_client.complete(prompt)


if __name__ == "__main__":
    rag = WikiRAG()
    rag.build_index(force=True)
    print("\n=== Sample Query: 'drawdown' ===")
    ctx = rag.get_context("drawdown")
    print(ctx[:1500])

    print("\n=== Sample Query: 'trend following' ===")
    ctx = rag.get_context("trend following")
    print(ctx[:1500])
