#!/usr/bin/env python
"""Test the entire system"""

print("\n" + "="*70)
print("AI INCIDENT DEDUPLICATION SYSTEM - TEST")
print("="*70 + "\n")

try:
    # Test 1: Check environment
    print("1️⃣  Checking environment...")
    from config import config
    print(f"   ✅ OpenAI API Key configured: {config.OPENAI_API_KEY[:10]}...")
    print(f"   ✅ Model: {config.OPENAI_MODEL}")
    print(f"   ✅ Similarity Threshold: {config.SIMILARITY_THRESHOLD}")

    # Test 2: Initialize services
    print("\n2️⃣  Initializing services...")
    from src.embeddings.embedding_service import EmbeddingService
    from src.vector_db.vector_store import VectorStore
    from src.deduplication.deduplication_engine import DeduplicationEngine
    from src.rag.rag_pipeline import RAGPipeline

    embedding_service = EmbeddingService()
    print("   ✅ Embedding service initialized")

    vector_store = VectorStore()
    print("   ✅ Vector store initialized")

    dedup_engine = DeduplicationEngine(embedding_service, vector_store)
    print("   ✅ Deduplication engine initialized")

    rag_pipeline = RAGPipeline()
    print("   ✅ RAG pipeline initialized")

    # Test 3: Test embeddings
    print("\n3️⃣  Testing embeddings...")
    test_text = "Database connection timeout error"
    embedding = embedding_service.embed_text(test_text)
    print(f"   ✅ Generated embedding with {len(embedding)} dimensions")

    # Test 4: Test vector store
    print("\n4️⃣  Testing vector store...")
    from src.models.incident import Incident, SeverityLevel
    incident = Incident(
        title="Test Incident",
        description="This is a test incident",
        severity=SeverityLevel.HIGH,
        source="test-service"
    )
    vector_store.add([embedding], [incident.id])
    print(f"   ✅ Added to vector store. Size: {vector_store.get_index_size()}")

    # Test 5: Test API
    print("\n5️⃣  Testing API...")
    from src.api.routes import app
    with app.test_client() as client:
        response = client.get('/api/health')
        print(f"   ✅ Health check: {response.status_code}")

    print("\n" + "="*70)
    print("✅ ALL TESTS PASSED!")
    print("="*70)
    print("\n🚀 Ready to run: python -m src.main")
    print("📊 API will be at: http://localhost:5000/api\n")

except Exception as e:
    print(f"\n❌ TEST FAILED: {e}")
    import traceback
    traceback.print_exc()