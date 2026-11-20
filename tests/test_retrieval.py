"""Tests for RAG embeddings, vector storage, and hybrid retrieval using isolated test fixtures."""
import pytest
from app.rag.embeddings import embedding_service
from app.rag.vector_store import VectorStore
from app.rag.retriever import HybridRetriever
from app.api.schemas import PropertyItem
from datetime import datetime, timezone

@pytest.fixture
def sample_property():
    return PropertyItem(
        id="test-luxury-villa-marbella",
        source="DarGlobal",
        title="Tierra Viva Lamborghini Villa",
        description="Exclusive 5 bedroom luxury villa in Marbella Spain designed with Lamborghini DNA.",
        location="Marbella, Spain",
        city="Marbella",
        country="Spain",
        property_type="Villa",
        price=4500000.0,
        currency="EUR",
        bedrooms=5,
        bathrooms=6,
        area="850 SQM",
        amenities=["Private Pool", "Wine Cellar", "Lamborghini Interiors"],
        source_url="https://darglobal.co.uk/tierra-viva",
        scraped_at=datetime.now(timezone.utc).isoformat(),
        content_hash="test-hash-12345"
    )

@pytest.fixture
def test_vector_store(tmp_path):
    """Creates isolated vector store in temporary directory to protect production index."""
    return VectorStore(persist_dir=tmp_path / "test_chroma")

def test_embeddings_generation():
    vec = embedding_service.embed_query("luxury penthouse in Dubai")
    assert isinstance(vec, list)
    assert len(vec) == 384
    norm = sum(x * x for x in vec) ** 0.5
    assert abs(norm - 1.0) < 0.05

def test_vector_indexing_and_retrieval(test_vector_store, sample_property):
    assert test_vector_store.count() == 0
    indexed = test_vector_store.index_properties([sample_property])
    assert indexed == 1
    assert test_vector_store.count() == 1

    results = test_vector_store.similarity_search("Lamborghini villa in Spain", top_k=2)
    assert len(results) == 1
    prop, score = results[0]
    assert prop.id == "test-luxury-villa-marbella"
    assert score > 0.0

def test_hybrid_retriever_metadata_filter(sample_property, monkeypatch, tmp_path):
    t_store = VectorStore(persist_dir=tmp_path / "test_filter")
    t_store.index_properties([sample_property])
    t_retriever = HybridRetriever(top_k=5)
    monkeypatch.setattr("app.rag.retriever.vector_store", t_store)
    
    props, citations, context = t_retriever.retrieve("Find villas in Marbella")
    assert len(props) >= 1
    assert any("Lamborghini" in c.title for c in citations)
    assert "Tierra Viva" in context

def test_empty_retrieval_behavior(monkeypatch, tmp_path):
    empty_store = VectorStore(persist_dir=tmp_path / "empty_store")
    t_retriever = HybridRetriever(top_k=5)
    monkeypatch.setattr("app.rag.retriever.vector_store", empty_store)
    
    props, citations, context = t_retriever.retrieve("Non-existent underwater colony")
    assert len(props) == 0
    assert len(citations) == 0
    assert "No matching real estate developments" in context
