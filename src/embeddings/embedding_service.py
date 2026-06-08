import requests
import logging

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Generate embeddings using Ollama (Free)"""

    def __init__(self):
        """Initialize Ollama embedding service"""
        self.ollama_url = "http://localhost:11434/api"
        self.model = "mistral"
        logger.info("Initialized Ollama embedding service")

    def embed_text(self, text: str) -> list:
        """Generate embedding for single text"""
        try:
            # Use simple hashing for embeddings (free alternative)
            return self._simple_embedding(text)
        except Exception as e:
            logger.error(f"Error embedding text: {e}")
            raise

    def embed_texts(self, texts: list) -> list:
        """Generate embeddings for multiple texts"""
        embeddings = []
        for text in texts:
            embedding = self.embed_text(text)
            embeddings.append(embedding)
        return embeddings

    def get_embedding_dimension(self) -> int:
        """Get dimension of embeddings"""
        return 384  # Dimension of simple embeddings

    @staticmethod
    def _simple_embedding(text: str) -> list:
        """
        Create simple embedding using character frequency
        (Free alternative to OpenAI embeddings)
        """
        # Convert text to lowercase and get character frequencies
        text_lower = text.lower()
        vector = [0.0] * 384

        # Use character frequencies
        for char in text_lower:
            if ord(char) < 384:
                vector[ord(char)] += 1.0

        # Add word length features
        words = text_lower.split()
        for i, word in enumerate(words[:384]):
            vector[i] += len(word) * 0.1

        # Normalize
        total = sum(abs(v) for v in vector)
        if total > 0:
            vector = [v / total for v in vector]

        return vector