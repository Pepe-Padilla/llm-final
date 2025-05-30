import os
import pandas as pd
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http import models
from llm.LLMGenerator import generate_summary
from llm.embeddings import get_embedding

# Load environment variables
load_dotenv()

def init_vector_db():
    # Initialize Qdrant client
    client = QdrantClient(url=os.getenv("VECTOR_DB_URL"))
    
    # Delete existing collections
    try:
        client.delete_collection("incidencias")
    except:
        pass
    
    # Create new collection
    client.create_collection(
        collection_name="incidencias",
        vectors_config=models.VectorParams(
            size=1536,  # OpenAI embedding size
            distance=models.Distance.COSINE
        )
    )
    
    return client

def process_csv(client, file_path, metadata_columns):
    # Read CSV file
    df = pd.read_csv(file_path)
    
    # Process each row
    for _, row in df.iterrows():
        # Generate summary using LLM
        summary = generate_summary(row.to_dict())
        
        # Get embedding
        vector = get_embedding(summary)
        
        # Prepare metadata
        metadata = {col: str(row[col]) for col in metadata_columns}
        
        # Add to vector database
        client.upsert(
            collection_name="incidencias",
            points=[
                models.PointStruct(
                    id=hash(str(row.to_dict())),  # Simple hash as ID
                    vector=vector,
                    payload={
                        "summary": summary,
                        **metadata
                    }
                )
            ]
        )

def main():
    # Initialize vector database
    client = init_vector_db()
    
    # Process PROBLEMAS_GLOBALES.csv
    process_csv(
        client,
        "resources/PROBLEMAS_GLOBALES.csv",
        [
            "INCIDENCIAS",
            "ID PROBLEMA",
            "COMPONENTE",
            "DESCRIPCION",
            "TIPO INCIDENCIA",
            "SOLUCIÓN",
            "FECHA DE RESOLUCIÓN",
            "BUZON REASIGNACION",
            "RESOLUCION AUTOMÁTICA"
        ]
    )
    
    # Process CORRECTIVOS_ABIERTOS.csv
    process_csv(
        client,
        "resources/CORRECTIVOS_ABIERTOS.csv",
        [
            "ID INCIDENCIA",
            "DESCRIPCION",
            "FECHA PREVISTA",
            "RESOLUCION AUTOMÁTICA"
        ]
    )

if __name__ == "__main__":
    main() 