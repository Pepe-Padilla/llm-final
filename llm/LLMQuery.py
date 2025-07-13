"""Consultas a la base de datos vectorial."""

from typing import List, Dict, Any
from qdrant_client import QdrantClient
from .LLMEmbedding import get_embedding
from .LLMLogger import log_llm_interaction
from config import VECTOR_DB_URL, QUERY_LIMIT_VECTORDB

def get_qdrant_client():
    """Obtiene cliente de Qdrant."""
    return QdrantClient(url=VECTOR_DB_URL)

def query_vector_db(query: str, limit: int = QUERY_LIMIT_VECTORDB) -> List[Dict[str, Any]]:
    """Consulta la base de datos vectorial por incidencias similares."""
    client = get_qdrant_client()
    query_vector = get_embedding(query)
    
    search_result = client.search(
        collection_name="incidencias",
        query_vector=query_vector,
        limit=limit
    )
    
    result = [
        {
            "score": hit.score,
            "metadata": {k: v for k, v in hit.payload.items() if k != "summary"},
            "summary": hit.payload.get("summary", "")
        }
        for hit in search_result
    ]
    
    log_llm_interaction("LLMQuery", f"query: {query}, limit: {limit}", f"results: {len(result)}")
    return result 