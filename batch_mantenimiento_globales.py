import os
import pandas as pd
import json
from datetime import datetime
from typing import List, Dict, Any
from dotenv import load_dotenv
from observabilidad.logger import batch_logger
from api.gestor_incidencias import get_incidencias_cerradas
from llm.LLMGenerator import generate_summary
from llm.LLMQuery import query_vector_db
from llm.LLMSuggestion import suggest_solution
from utils import simple_json_parse
import time

# Load environment variables
load_dotenv()

def check_if_incident_exists_in_db(incident_summary: str, similarity_threshold: float = 0.70) -> bool:
    """
    Check if similar incident exists in vector database
    """
    try:
        # Query vector database 
        similar_incidents = query_vector_db(incident_summary, limit=3)
        
        # Check if any similar incident has high similarity score
        for similar in similar_incidents:
            if similar["score"] >= similarity_threshold:
                batch_logger.info(f"SIMILAR FOUND: {similar['score']:.3f}")
                return True
        
        highest_score = max([s["score"] for s in similar_incidents]) if similar_incidents else 0
        batch_logger.info(f"NEW (highest: {highest_score:.3f})")
        return False
        
    except Exception as e:
        batch_logger.error(f"DB check failed: {e}")
        return False  # If check fails, assume it's new

def process_closed_incident(incident: Dict[str, Any], similarity_threshold: float = 0.70) -> Dict[str, Any]:
    """
    Process a closed incident to generate a solution entry
    """
    try:
        incident_code = incident['codIncidencia']
        batch_logger.info(f"Processing: {incident_code}")
        
        # Simple description - use original description
        description = incident["descripcion"]
        
        # Check if incident already exists in vector database
        if check_if_incident_exists_in_db(description, similarity_threshold):
            batch_logger.info(f"EXISTS - Skipping: {incident_code}")
            return None
        
        batch_logger.info(f"NEW - Processing: {incident_code}")
        
        # Generate solution suggestion 
        try:
            solution_response = suggest_solution(incident)
            solution_data = simple_json_parse(solution_response, batch_logger)
            
            if not solution_data:
                # Create default solution if LLM fails
                batch_logger.warning(f"LLM failed, using default: {incident_code}")
                solution_data = {
                    "COMPONENTE": "General",
                    "TIPO INCIDENCIA": "General", 
                    "SOLUCIÓN": f"Revisar caso cerrado: {incident['titulo']}",
                    "RESOLUCION AUTOMÁTICA": "manual",
                    "BUZON REASIGNACION": ""
                }
        except Exception as e:
            batch_logger.warning(f"Solution generation failed: {incident_code} - {e}")
            # Fallback to manual entry
            solution_data = {
                "COMPONENTE": "General",
                "TIPO INCIDENCIA": "General",
                "SOLUCIÓN": f"Revisar caso cerrado: {incident['titulo']}",
                "RESOLUCION AUTOMÁTICA": "manual", 
                "BUZON REASIGNACION": ""
            }
        
        # Prepare CSV entry - simple
        csv_entry = {
            "COMPONENTE": solution_data.get("COMPONENTE", "General"),
            "DESCRIPCION": description,
            "TIPO INCIDENCIA": solution_data.get("TIPO INCIDENCIA", "General"),
            "SOLUCIÓN": solution_data.get("SOLUCIÓN", "Revisar manualmente"),
            "FECHA DE RESOLUCIÓN": None,
            "RESOLUCION AUTOMÁTICA": solution_data.get("RESOLUCION AUTOMÁTICA", "manual"),
            "BUZON REASIGNACION": solution_data.get("BUZON REASIGNACION", "")
        }
        
        batch_logger.info(f"SUCCESS: {incident_code} - {csv_entry['RESOLUCION AUTOMÁTICA']}")
        return csv_entry
        
    except Exception as e:
        batch_logger.error(f"FAILED: {incident['codIncidencia']} - {e}")
        return None

def main():
    """
    Main function to process closed incidents and generate new problems CSV.
    """
    start_time = time.time()
    
    # Configuration 
    SIMILARITY_THRESHOLD = 0.65  # Lower = more strict
    
    batch_logger.info("=== STARTING BATCH ===")
    batch_logger.info(f"Threshold: {SIMILARITY_THRESHOLD}")
    
    try:
        # Generate filename
        current_date = datetime.now().strftime("%Y%m%d")
        output_filename = f"resources/PROBLEMAS_GLOBALES_{current_date}.csv"
        batch_logger.info(f"Output: {output_filename}")
        
        # Get closed incidents
        batch_logger.info("Fetching closed incidents...")
        closed_incidents = get_incidencias_cerradas()
        total_incidents = len(closed_incidents)
        batch_logger.info(f"Found: {total_incidents} closed incidents")
        
        # Process each closed incident - simple
        new_entries = []
        
        for i, incident in enumerate(closed_incidents, 1):
            batch_logger.info(f"=== {i}/{total_incidents} ===")
            
            result = process_closed_incident(incident, SIMILARITY_THRESHOLD)
            
            if result is not None:
                new_entries.append(result)
        
        # Results
        total_time = time.time() - start_time
        porcentaje = round((len(new_entries) / total_incidents) * 100, 1) if total_incidents > 0 else 0
        
        batch_logger.info(f"=== RESULTS ===")
        batch_logger.info(f"Processed: {total_incidents}")
        batch_logger.info(f"New entries: {len(new_entries)} ({porcentaje}%)")
        batch_logger.info(f"Time: {total_time:.1f}s")
        
        # Generate files if we have new entries
        if new_entries:
            # CSV
            df = pd.DataFrame(new_entries)
            df.to_csv(output_filename, index=False, encoding='utf-8')
            batch_logger.info(f"CSV: {output_filename}")
            
            # Simple report
            report_filename = f"resources/reporte_mantenimiento_globales_{current_date}.json"
            report_data = {
                "fecha": datetime.now().isoformat(),
                "umbral_similitud": SIMILARITY_THRESHOLD,
                "procesadas": total_incidents,
                "nuevas": len(new_entries),
                "porcentaje": porcentaje,
                "tiempo_segundos": round(total_time, 1),
                "archivo": output_filename
            }
            
            with open(report_filename, "w", encoding="utf-8") as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)
            
            batch_logger.info(f"Report: {report_filename}")
        else:
            batch_logger.info("No new entries found - no files generated")
        
    except Exception as e:
        batch_logger.error(f"FATAL ERROR: {e}")
        raise

if __name__ == "__main__":
    main() 