import os
import pandas as pd
import uuid
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http import models
from llm.LLMGenerator import generate_summary
from llm.LLMEmbedding import get_embedding
import time

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
    
    # Set vector size based on environment
    vector_size = 384 if os.getenv("ENTORNO") == "DESA" else 1536
    
    # Create new collection
    client.create_collection(
        collection_name="incidencias",
        vectors_config=models.VectorParams(
            size=vector_size,  # Dynamic size based on environment
            distance=models.Distance.COSINE
        )
    )
    
    return client

def process_csv(client, file_path, metadata_columns):
    # Read CSV file
    df = pd.read_csv(file_path)
    total_rows = len(df)
    processed = 0
    
    print(f"Total documents to process: {total_rows}")
    
    # Process each row
    for _, row in df.iterrows():
        # Generate summary using LLM
        summary = generate_summary(row.to_dict())
        
        # Get embedding
        vector = get_embedding(summary)
        
        # Prepare metadata
        metadata = row.to_dict() #{col: str(row[col]) for col in metadata_columns}
        
        # Add to vector database
        client.upsert(
            collection_name="incidencias",
            points=[
                models.PointStruct(
                    id=str(uuid.uuid4()),  # Generate a UUID
                    vector=vector,
                    payload={
                        "summary": summary,
                        **metadata
                    }
                )
            ]
        )
        
        # Update progress
        processed += 1
        progress = (processed / total_rows) * 100
        print(f"\rProgress: {progress:.1f}% ({processed}/{total_rows})", end="")
    
    print(f"\nCompleted processing {processed} documents from {file_path}")

def main():

    # Start timing
    start_time = time.time()

    # Initialize vector database
    client = init_vector_db()
    
    # Process PROBLEMAS_GLOBALES.csv
    print("Processing PROBLEMAS_GLOBALES.csv")
    process_csv(
        client,
        "resources/PROBLEMAS_GLOBALES.csv",
        [
            "COMPONENTE",
            "DESCRIPCION",
            "TIPO INCIDENCIA",
            "SOLUCIÓN",
            "FECHA DE RESOLUCIÓN",
            "RESOLUCION AUTOMÁTICA",
            "BUZON REASIGNACION"
        ]
    )
    
    # Process CORRECTIVOS_ABIERTOS.csv if it exists
    print("Processing CORRECTIVOS_ABIERTOS.csv")
    correctivos_path = "resources/CORRECTIVOS_ABIERTOS.csv"
    if os.path.exists(correctivos_path):
        process_csv(
            client,
            correctivos_path,
            [
                "ID INCIDENCIA",
                "DESCRIPCION",
                "FECHA PREVISTA",
                "RESOLUCION AUTOMÁTICA"
            ]
        )

    print(f"\nTiempo total: {time.time() - start_time:.2f} segundos")

if __name__ == "__main__":
    main() 