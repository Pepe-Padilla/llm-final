import os
from typing import List, Dict, Any
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http import models
from .LLMEmbedding import get_embedding

# Load environment variables
load_dotenv()

def get_qdrant_client() -> QdrantClient:
    """Get a Qdrant client instance."""
    return QdrantClient(
        url=os.getenv("QDRANT_URL", "http://localhost:6333")
    )

def query_vector_db(query: str, limit: int = 2) -> List[Dict[str, Any]]:
    """Query the vector database for similar incidents."""
    client = get_qdrant_client()
    query_vector = get_embedding(query)
    
    search_result = client.search(
        collection_name="incidencias",
        query_vector=query_vector,
        limit=limit
    )
    
    return [
        {
            "score": hit.score,
            "metadata": {k: v for k, v in hit.payload.items() if k != "summary"},
            "summary": hit.payload.get("summary", "")
        }
        for hit in search_result
    ] 