import csv
import os
from datetime import datetime


def log_llm_interaction(llm_name: str, input_data, output_data):
    """
    Guarda la interacción de un LLM en un archivo CSV.
    Simple y robusto - no falla nunca.
    """
    try:
        # Crear carpeta si no existe
        log_dir = os.path.join(os.path.dirname(__file__), "historico")
        os.makedirs(log_dir, exist_ok=True)
        
        # Archivo de log
        log_file = os.path.join(log_dir, f"{llm_name}.csv")
        
        # Convertir a string simple
        input_str = str(input_data)
        output_str = str(output_data)
        timestamp = datetime.now().isoformat()
        
        # Escribir al archivo
        file_exists = os.path.exists(log_file)
        with open(log_file, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            
            # Header solo si es nuevo
            if not file_exists:
                writer.writerow(["timestamp", "input", "output"])
            
            # Escribir datos
            writer.writerow([timestamp, input_str, output_str])
            
    except Exception:
        # Silencioso - no debe romper el flujo principal
        pass 