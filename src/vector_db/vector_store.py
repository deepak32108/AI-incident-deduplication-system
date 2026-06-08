from typing import List, Tuple
import logging
import json
import os

logger = logging.getLogger(__name__)


class VectorStore:
    """Simple in-memory vector store with pure Python"""

    def __init__(self, persist_path: str = "./data/vector_store.json"):
        self.persist_path = persist_path
        self.embeddings = []
        self.incident_ids = []
        self.metadata = {}

        os.makedirs(os.path.dirname(persist_path) or ".", exist_ok=True)
        self._load()

    def add(self, embeddings: List[List[float]], incident_ids: List[str],
            metadatas: List[dict] = None, documents: List[str] = None):
        """Add embeddings to store"""
        for emb, inc_id, meta, doc in zip(
                embeddings,
                incident_ids,
                metadatas or [None] * len(embeddings),
                documents or [None] * len(embeddings)
        ):
            self.embeddings.append(emb)
            self.incident_ids.append(inc_id)
            self.metadata[inc_id] = {'metadata': meta, 'document': doc}

        logger.info(f"Added {len(embeddings)} embeddings")
        self._save()

    def search(self, query_embedding: List[float], k: int = 5) -> Tuple[List[str], List[float]]:
        """Search similar incidents"""
        if not self.embeddings:
            return [], []

        try:
            similarities = []
            query_norm = self._norm(query_embedding)

            for emb in self.embeddings:
                sim = self._cosine_similarity(query_embedding, emb, query_norm)
                similarities.append(sim)

            top_indices = sorted(range(len(similarities)),
                                 key=lambda i: similarities[i],
                                 reverse=True)[:k]

            result_ids = [self.incident_ids[i] for i in top_indices]
            result_scores = [similarities[i] for i in top_indices]

            return result_ids, result_scores
        except Exception as e:
            logger.error(f"Search error: {e}")
            return [], []

    def get_index_size(self) -> int:
        """Get number of vectors"""
        return len(self.embeddings)

    def delete(self, incident_id: str):
        """Delete incident"""
        if incident_id in self.incident_ids:
            idx = self.incident_ids.index(incident_id)
            self.embeddings.pop(idx)
            self.incident_ids.pop(idx)
            if incident_id in self.metadata:
                del self.metadata[incident_id]
            self._save()

    def clear(self):
        """Clear all data"""
        self.embeddings = []
        self.incident_ids = []
        self.metadata = {}
        self._save()

    @staticmethod
    def _norm(vector: List[float]) -> float:
        """Calculate vector norm"""
        return sum(v * v for v in vector) ** 0.5

    @staticmethod
    def _cosine_similarity(v1: List[float], v2: List[float], v1_norm: float = None) -> float:
        """Calculate cosine similarity"""
        if v1_norm is None:
            v1_norm = VectorStore._norm(v1)
        v2_norm = VectorStore._norm(v2)

        if v1_norm == 0 or v2_norm == 0:
            return 0.0

        dot_product = sum(a * b for a, b in zip(v1, v2))
        return dot_product / (v1_norm * v2_norm)

    def _save(self):
        """Save to disk"""
        try:
            data = {
                'embeddings': self.embeddings,
                'incident_ids': self.incident_ids,
                'metadata': self.metadata
            }
            os.makedirs(os.path.dirname(self.persist_path) or ".", exist_ok=True)
            with open(self.persist_path, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            logger.warning(f"Save error: {e}")

    def _load(self):
        """Load from disk"""
        try:
            if os.path.exists(self.persist_path):
                with open(self.persist_path, 'r') as f:
                    data = json.load(f)
                    self.embeddings = data.get('embeddings', [])
                    self.incident_ids = data.get('incident_ids', [])
                    self.metadata = data.get('metadata', {})
                logger.info(f"Loaded {len(self.embeddings)} vectors")
        except Exception as e:
            logger.warning(f"Load error: {e}")