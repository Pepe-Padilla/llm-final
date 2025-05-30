import os
from typing import List
from langchain.embeddings import OpenAIEmbeddings
from langchain.embeddings import OllamaEmbeddings

def get_embeddings():
    """Get the appropriate embedding model based on environment."""
    if os.getenv("ENTORNO") == "DESA":
        return OllamaEmbeddings(
            base_url=os.getenv("OLLAMA_BASE_URL"),
            model="llama2"
        )
    else:
        return OpenAIEmbeddings(
            model="text-embedding-ada-002",
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )

def get_embedding(text: str) -> List[float]:
    """Generate an embedding for the given text."""
    embeddings = get_embeddings()
    return embeddings.embed_query(text) 