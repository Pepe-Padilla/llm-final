import os
from typing import List
from dotenv import load_dotenv
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_ollama import OllamaEmbeddings
from .LLMLogger import log_llm_interaction

# Load environment variables
load_dotenv()

def get_embeddings():
    """Get the appropriate embedding model based on environment."""
    if os.getenv("ENTORNO") == "DESA":
        return OllamaEmbeddings(
            base_url=os.getenv("OLLAMA_BASE_URL"),
            model="all-minilm"
        )
    else:
        return OpenAIEmbeddings(
            model="text-embedding-ada-002",
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )

def get_embedding(text: str) -> List[float]:
    """Generate an embedding for the given text."""
    embeddings = get_embeddings()
    embedding_result = embeddings.embed_query(text)
    
    # Log the interaction (with truncated result for readability)
    log_llm_interaction("LLMEmbedding", text, f"Vector de {len(embedding_result)} dimensiones")
    
    return embedding_result 