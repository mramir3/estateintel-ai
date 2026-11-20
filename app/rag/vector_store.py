"""Vector store implementation with ChromaDB and resilient persistent vector fallback."""
import json
import math
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from app.api.schemas import PropertyItem, SourceCitation
from app.rag.embeddings import embedding_service
from app.config import settings
from app.utils.logging import logger

class VectorStore:
    """Manages property document chunking, indexing, and semantic similarity search."""

    def __init__(self, persist_dir: Optional[Path] = None):
        self.persist_dir = persist_dir or settings.CHROMA_DIR
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.collection_name = settings.COLLECTION_NAME
        
        self._chroma_client = None
        self._chroma_collection = None
        self._local_index: List[Dict[str, Any]] = []
        self._local_index_path = self.persist_dir / "estateintel_vector_index.json"
        
        self._init_store()

    def _init_store(self):
        """Attempts to initialize ChromaDB; falls back to persistent vector index."""
        try:
            import chromadb
            from chromadb.config import Settings as ChromaSettings
            self._chroma_client = chromadb.PersistentClient(
                path=str(self.persist_dir),
                settings=ChromaSettings(anonymized_telemetry=False)
            )
            self._chroma_collection = self._chroma_client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "DarGlobal and Wasalt Real Estate Properties"}
            )
            logger.info(f"Initialized ChromaDB persistent collection: {self.collection_name}")
            return
        except Exception as e:
            logger.warning(f"ChromaDB native backend unavailable ({e}). Using resilient persistent vector store.")

        self._load_local_index()

    def _load_local_index(self):
        """Loads persistent JSON vector index from disk."""
        if self._local_index_path.exists():
            try:
                with open(self._local_index_path, "r", encoding="utf-8") as f:
                    self._local_index = json.load(f)
                logger.info(f"Loaded {len(self._local_index)} indexed documents from local vector store.")
            except Exception as e:
                logger.error(f"Error loading local vector store: {e}")
                self._local_index = []

    def _save_local_index(self):
        """Persists local vector index to disk."""
        try:
            with open(self._local_index_path, "w", encoding="utf-8") as f:
                json.dump(self._local_index, f, ensure_ascii=False)
            logger.info(f"Persisted {len(self._local_index)} documents to local vector store.")
        except Exception as e:
            logger.error(f"Error saving local vector store: {e}")

    def _format_property_doc(self, p: PropertyItem) -> str:
        """Constructs rich contextual text representation for embedding and retrieval."""
        lines = [
            f"Title: {p.title}",
            f"Source Platform: {p.source}",
            f"Property Type: {p.property_type or 'Real Estate'}",
            f"Location: {p.location or 'Not specified'}",
            f"City: {p.city or 'Unknown'}, Country: {p.country or 'Unknown'}",
        ]
        if p.price is not None:
            lines.append(f"Price: {p.price:,.0f} {p.currency or ''}".strip())
        if p.bedrooms is not None:
            lines.append(f"Bedrooms: {p.bedrooms}")
        if p.bathrooms is not None:
            lines.append(f"Bathrooms: {p.bathrooms}")
        if p.area:
            lines.append(f"Area: {p.area}")
        if p.amenities:
            lines.append(f"Amenities & Features: {', '.join(p.amenities)}")
        if p.description:
            lines.append(f"Overview: {p.description}")
        if p.metadata:
            for k, v in p.metadata.items():
                if v and isinstance(v, (str, int, float)):
                    lines.append(f"{k.replace('_', ' ').title()}: {v}")
        return "\n".join(lines)

    def index_properties(self, properties: List[PropertyItem]) -> int:
        """Chunks, embeds, and indexes list of properties into vector store."""
        if not properties:
            return 0

        logger.info(f"Indexing {len(properties)} properties into vector store...")
        docs = [self._format_property_doc(p) for p in properties]
        ids = [p.id for p in properties]
        embeddings = embedding_service.embed_documents(docs)

        # Index in ChromaDB if available
        if self._chroma_collection is not None:
            try:
                metadatas = [
                    {
                        "source": p.source,
                        "title": p.title,
                        "location": p.location or "",
                        "city": p.city or "",
                        "property_type": p.property_type or "",
                        "price": float(p.price) if p.price is not None else -1.0,
                        "source_url": p.source_url,
                        "raw_json": p.model_dump_json()
                    }
                    for p in properties
                ]
                self._chroma_collection.upsert(
                    ids=ids,
                    documents=docs,
                    embeddings=embeddings,
                    metadatas=metadatas
                )
                logger.info(f"Successfully upserted {len(properties)} items to ChromaDB.")
            except Exception as e:
                logger.error(f"ChromaDB indexing error ({e}), maintaining local index sync.")

        # Always maintain synchronized local index
        self._local_index = []
        for p, doc, emb in zip(properties, docs, embeddings):
            self._local_index.append({
                "id": p.id,
                "document": doc,
                "embedding": emb,
                "property_data": p.model_dump()
            })
        self._save_local_index()
        return len(properties)

    def similarity_search(
        self, 
        query: str, 
        top_k: int = 5, 
        source_filter: Optional[str] = None
    ) -> List[Tuple[PropertyItem, float]]:
        """Retrieves top-K most semantically similar properties with relevance scores."""
        if self.count() == 0:
            return []

        # Try ChromaDB query first
        if self._chroma_collection is not None:
            try:
                query_emb = embedding_service.embed_query(query)
                where_clause = {"source": source_filter} if source_filter else None
                res = self._chroma_collection.query(
                    query_embeddings=[query_emb],
                    n_results=min(top_k, self.count()),
                    where=where_clause
                )
                
                results = []
                if res and res.get("metadatas") and res["metadatas"][0]:
                    metas = res["metadatas"][0]
                    distances = res["distances"][0] if "distances" in res and res["distances"] else [0.0] * len(metas)
                    for meta, dist in zip(metas, distances):
                        prop = PropertyItem.model_validate_json(meta["raw_json"])
                        score = max(0.0, 1.0 - (dist if dist is not None else 0.5))
                        results.append((prop, score))
                    return results
            except Exception as e:
                logger.warning(f"ChromaDB query failed ({e}), falling back to local vector search.")

        # Resilient local vector cosine search
        query_vec = embedding_service.embed_query(query)
        scored_items = []

        for item in self._local_index:
            p_data = item["property_data"]
            if source_filter and p_data.get("source", "").lower() != source_filter.lower():
                continue

            doc_vec = item["embedding"]
            # Cosine similarity
            dot = sum(a * b for a, b in zip(query_vec, doc_vec))
            norm_q = math.sqrt(sum(a * a for a in query_vec)) or 1.0
            norm_d = math.sqrt(sum(b * b for b in doc_vec)) or 1.0
            score = max(0.0, min(1.0, dot / (norm_q * norm_d)))
            
            # Boost score if keyword matches title or location
            q_lower = query.lower()
            if p_data.get("title", "").lower() in q_lower or any(word in p_data.get("title", "").lower() for word in q_lower.split() if len(word) > 3):
                score = min(1.0, score + 0.15)
            if p_data.get("city", "").lower() in q_lower or p_data.get("location", "").lower() in q_lower:
                score = min(1.0, score + 0.10)

            prop = PropertyItem(**p_data)
            scored_items.append((prop, score))

        # Sort descending by score
        scored_items.sort(key=lambda x: x[1], reverse=True)
        return scored_items[:top_k]

    def count(self) -> int:
        """Returns total number of indexed properties."""
        if self._chroma_collection is not None:
            try:
                return self._chroma_collection.count()
            except Exception:
                pass
        return len(self._local_index)

    def clear(self):
        """Clears all indexed documents."""
        if self._chroma_collection is not None:
            try:
                self._chroma_client.delete_collection(self.collection_name)
                self._chroma_collection = self._chroma_client.create_collection(self.collection_name)
            except Exception:
                pass
        self._local_index = []
        if self._local_index_path.exists():
            self._local_index_path.unlink()

vector_store = VectorStore()
