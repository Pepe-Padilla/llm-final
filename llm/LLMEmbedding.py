"""LLM para generar embeddings."""

from typing import List
from langchain_ollama import OllamaEmbeddings
from langchain_community.embeddings import OpenAIEmbeddings
from .LLMLogger import log_llm_interaction
from config import ENTORNO, OLLAMA_BASE_URL, OPENAI_API_KEY, LLM_MODEL_DESA

def get_embedding(text: str) -> List[float]:
    """Obtiene el embedding de un texto."""
    if ENTORNO == "DESA":
        embedding_model = OllamaEmbeddings(
            base_url=OLLAMA_BASE_URL,
            model=LLM_MODEL_DESA,
        )
    else:
        embedding_model = OpenAIEmbeddings(
            openai_api_key=OPENAI_API_KEY
        )
    
    embedding = embedding_model.embed_query(text)
    
    log_llm_interaction("LLMEmbedding", f"text: {text[:100]}...", f"embedding length: {len(embedding)}")
    
    return embedding 