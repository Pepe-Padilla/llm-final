"""Configuración centralizada del sistema."""
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de entornos
ENTORNO = os.getenv("ENTORNO", "DESA")

# URLs de servicios
MOCK_GESTOR_URL = os.getenv("MOCK_GESTOR_URL", "http://localhost:3001")
MOCK_SISTEMA_URL = os.getenv("MOCK_SISTEMA_URL", "http://localhost:3002")
VECTOR_DB_URL = os.getenv("VECTOR_DB_URL", "http://localhost:6333")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# Configuración de LLM
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LLM_MODEL_DESA = "gemma3"
LLM_MODEL_PROD = "gpt-4-mini"
LLM_TEMPERATURE = 0

# Configuración de embeddings
LLM_MODEL_EMBEDDING_DESA = "all-minilm" #"all-MiniLM-L6-v2"
LLM_MODEL_EMBEDDING_PROD = "text-embedding-ada-002"

# Límites y configuraciones
MAX_RETRIES_CRITIC = 2
QUERY_LIMIT_VECTORDB = 2

# Umbrales de métricas
CRITIC_APPROVAL_THRESHOLD = 65  # % mínimo de aprobación del crítico 