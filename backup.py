"""Backup de la base de datos vectorial."""
import json
from datetime import datetime
from qdrant_client import QdrantClient
from config import VECTOR_DB_URL

def get_all_data():
    # Get all points from the collection
    client = QdrantClient(url=VECTOR_DB_URL)
    
    points = client.scroll(
        collection_name="incidencias",
        limit=100,  # Adjust this number based on your needs
        with_payload=True,
        with_vectors=False  # We don't need the vectors for this
    )[0]  # scroll returns a tuple, we want the first element
    
    # Format the data
    formatted_data = []
    for point in points:
        formatted_data.append({
            "id": point.id,
            "payload": point.payload
        })
    
    return formatted_data

def main():
    try:
        # Get all data
        data = get_all_data()
        
        # Also save to a file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        with open(f'backup/database_dump{timestamp}.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        print(f"\nTotal records found: {len(data)}")
        print("Data has been saved to 'database_dump.json'")
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main() 