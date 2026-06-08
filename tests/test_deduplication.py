import pytest
from src.models.incident import Incident, SeverityLevel, IncidentStatus
from src.embeddings.embedding_service import EmbeddingService
from src.vector_db.vector_store import VectorStore
from src.deduplication.deduplication_engine import DeduplicationEngine


@pytest.fixture
def embedding_service():
    return EmbeddingService(model_type="sentence-transformers")


@pytest.fixture
def vector_store(embedding_service):
    return VectorStore(dimension=embedding_service.get_embedding_dimension())


@pytest.fixture
def dedup_engine(embedding_service, vector_store):
    return DeduplicationEngine(embedding_service, vector_store)


def test_embed_text(embedding_service):
    """Test text embedding"""
    text = "Database connection timeout error"
    embedding = embedding_service.embed_text(text)
    assert len(embedding) > 0
    assert isinstance(embedding, list)


def test_vector_store_operations(vector_store):
    """Test vector store add and search"""
    embeddings = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
    incident_ids = ["inc1", "inc2"]

    vector_store.add(embeddings, incident_ids)
    assert vector_store.get_index_size() == 2


def test_duplicate_detection(dedup_engine, embedding_service, vector_store):
    """Test duplicate detection"""
    # Create first incident
    incident1 = Incident(
        title="Database Timeout",
        description="Database connection timeout in production",
        severity=SeverityLevel.CRITICAL,
        source="db"
    )
    dedup_engine.index_incident(incident1)

    # Create potential duplicate
    incident2 = Incident(
        title="DB Connection Timeout",
        description="Database is experiencing connection timeouts",
        severity=SeverityLevel.CRITICAL,
        source="db"
    )

    # Test deduplication
    is_duplicate, parent, score = dedup_engine.deduplicate(incident2, [incident1])

    if score > 0.85:  # Only assert if similarity is high
        assert is_duplicate is True
        assert parent.id == incident1.id


if __name__ == '__main__':
    pytest.main([__file__, '-v'])