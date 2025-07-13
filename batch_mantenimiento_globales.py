from datetime import datetime
from dotenv import load_dotenv
from observabilidad.logger import batch_logger
from qdrant_client import QdrantClient
from api.gestor_incidencias import get_incidencias_cerradas
from llm.LLMGenerator import generate_summary
from llm.LLMRephrase import rephrase_incidence
from llm.LLMSuggestion import suggest_solution
from llm.LLMEmbedding import get_embedding
from llm.LLMQuery import query_vector_db
from utils import convert_json_response

# Load environment variables
load_dotenv()

def analyze_closed_incident(incident):
    """
    Analiza una incidencia cerrada y genera la información necesaria para el catálogo.
    
    Args:
        incident: Diccionario con los datos de la incidencia cerrada
        
    Returns:
        dict: Datos procesados de la incidencia
    """
    batch_logger.info(f"Analizando incidencia cerrada: {incident['codIncidencia']}", extra_data={
        "action": "analyze_closed_incident",
        "codIncidencia": incident["codIncidencia"],
        "titulo": incident["titulo"],
        "estado": incident["estado"]
    })
    
    # Generar resumen usando LLM
    summary = generate_summary(incident)
    batch_logger.debug("Resumen generado", extra_data={
        "action": "summary_generated",
        "codIncidencia": incident["codIncidencia"],
        "summary": summary
    })
    
    # Generar versiones reformuladas
    rephrase_response = rephrase_incidence(incident)
    rephrased_versions = convert_json_response(rephrase_response, "rephrase")
    batch_logger.debug("Versiones reformuladas generadas", extra_data={
        "action": "rephrase_generated",
        "codIncidencia": incident["codIncidencia"],
        "versions_count": len(rephrased_versions)
    })
    
    # Sugerir solución usando LLM
    suggestion_response = suggest_solution(incident)
    suggested_solution = convert_json_response(suggestion_response, "suggestion")
    batch_logger.debug("Solución sugerida", extra_data={
        "action": "solution_suggested",
        "codIncidencia": incident["codIncidencia"],
        "suggestion": suggested_solution
    })
    
    return {
        "incident": incident,
        "summary": summary,
        "rephrased_versions": rephrased_versions,
        "suggested_solution": suggested_solution
    }

def check_if_incident_exists(incident_text):
    """
    Verifica si una incidencia similar ya existe en la base de datos vectorial.
    
    Args:
        incident_text: Texto de la incidencia a verificar
        
    Returns:
        bool: True si existe una incidencia similar, False en caso contrario
    """
    batch_logger.debug("Verificando si la incidencia ya existe", extra_data={
        "action": "check_incident_exists",
        "incident_preview": incident_text[:100] + "..." if len(incident_text) > 100 else incident_text
    })
    
    # Buscar incidentes similares en la base de datos vectorial
    similar_incidents = query_vector_db(incident_text)
    
    # Si hay incidentes similares, consideramos que ya existe
    if similar_incidents and len(similar_incidents) > 0:
        batch_logger.debug("Incidencia similar encontrada", extra_data={
            "action": "similar_incident_found",
            "similar_count": len(similar_incidents),
            "similarity_preview": str(similar_incidents[0])[:100] + "..." if similar_incidents else ""
        })
        return True
    
    batch_logger.debug("No se encontraron incidencias similares", extra_data={
        "action": "no_similar_incidents"
    })
    return False

def create_csv_entry(analyzed_incident):
    """
    Crea una entrada CSV basada en la incidencia analizada.
    
    Args:
        analyzed_incident: Datos procesados de la incidencia
        
    Returns:
        dict: Entrada para el archivo CSV
    """
    incident = analyzed_incident["incident"]
    suggested_solution = analyzed_incident["suggested_solution"]
    
    # Extraer información del historial de resolución
    resolution_info = None
    if incident.get("historial"):
        for entry in incident["historial"]:
            if entry.get("CodigoResolucion"):
                resolution_info = entry
                break
    
    # Crear entrada CSV
    csv_entry = {
        "COMPONENTE": suggested_solution.get("COMPONENTE", "Desconocido"),
        "DESCRIPCION": suggested_solution.get("DESCRIPCION", incident.get("descripcion", "")),
        "TIPO INCIDENCIA": suggested_solution.get("TIPO INCIDENCIA", "Técnico"),
        "SOLUCIÓN": suggested_solution.get("SOLUCIÓN", resolution_info.get("NotasResolucion", "") if resolution_info else ""),
        "FECHA DE RESOLUCIÓN": incident.get("apertura", ""),
        "RESOLUCION AUTOMÁTICA": suggested_solution.get("RESOLUCION AUTOMÁTICA", "manual"),
        "BUZON REASIGNACION": suggested_solution.get("BUZON REASIGNACION", "")
    }
    
    batch_logger.debug("Entrada CSV creada", extra_data={
        "action": "csv_entry_created",
        "codIncidencia": incident["codIncidencia"],
        "csv_entry": csv_entry
    })
    
    return csv_entry

def main():
    """Función principal del batch de mantenimiento."""
    start_time = time.time()
    
    # Generar nombre del archivo con fecha
    date_str = datetime.now().strftime("%Y%m%d")
    output_file = f"resources/PROBLEMAS_GLOBALES_{date_str}.csv"
    
    batch_logger.info(f"Iniciando batch de mantenimiento globales", extra_data={
        "action": "batch_start",
        "output_file": output_file,
        "date": date_str
    })
    
    # Obtener incidencias cerradas de los últimos 2 meses
    batch_logger.info("Obteniendo incidencias cerradas...")
    incidencias_cerradas = get_incidencias_cerradas(meses=2)
    
    batch_logger.info(f"Total de incidencias cerradas encontradas: {len(incidencias_cerradas)}", extra_data={
        "action": "closed_incidents_loaded",
        "total_incidents": len(incidencias_cerradas)
    })
    
    # Procesar cada incidencia
    new_entries = []
    processed_count = 0
    skipped_count = 0
    
    for i, incident in enumerate(incidencias_cerradas, 1):
        batch_logger.info(f"Procesando incidencia {i}/{len(incidencias_cerradas)}: {incident['codIncidencia']}", extra_data={
            "action": "process_incident",
            "incident_index": i,
            "total_incidents": len(incidencias_cerradas),
            "codIncidencia": incident["codIncidencia"]
        })
        
        # Verificar si ya existe en la base de datos
        incident_text = f"{incident['titulo']} {incident['descripcion']}"
        
        if check_if_incident_exists(incident_text):
            batch_logger.debug("Incidencia ya existe, omitiendo", extra_data={
                "action": "incident_skipped",
                "codIncidencia": incident["codIncidencia"],
                "reason": "already_exists"
            })
            skipped_count += 1
            continue
        
        # Analizar la incidencia
        try:
            analyzed_incident = analyze_closed_incident(incident)
            csv_entry = create_csv_entry(analyzed_incident)
            new_entries.append(csv_entry)
            processed_count += 1
            
            batch_logger.info(f"Incidencia procesada exitosamente", extra_data={
                "action": "incident_processed",
                "codIncidencia": incident["codIncidencia"],
                "processed_count": processed_count
            })
            
        except Exception as e:
            batch_logger.error(f"Error procesando incidencia {incident['codIncidencia']}: {str(e)}", extra_data={
                "action": "incident_error",
                "codIncidencia": incident["codIncidencia"],
                "error": str(e),
                "error_type": type(e).__name__
            })
            continue
    
    # Guardar resultados en archivo CSV
    if new_entries:
        batch_logger.info(f"Guardando {len(new_entries)} nuevas entradas en {output_file}", extra_data={
            "action": "save_csv",
            "output_file": output_file,
            "new_entries_count": len(new_entries)
        })
        
        df = pd.DataFrame(new_entries)
        df.to_csv(output_file, index=False, encoding='utf-8')
        
        batch_logger.info(f"Archivo CSV guardado exitosamente", extra_data={
            "action": "csv_saved",
            "output_file": output_file,
            "rows_written": len(new_entries)
        })
    else:
        batch_logger.info("No se encontraron nuevas entradas para guardar", extra_data={
            "action": "no_new_entries"
        })
    
    # Estadísticas finales
    total_time = time.time() - start_time
    batch_logger.info("=== Estadísticas del Batch ===", extra_data={
        "action": "batch_complete",
        "total_incidents": len(incidencias_cerradas),
        "processed_count": processed_count,
        "skipped_count": skipped_count,
        "new_entries_count": len(new_entries),
        "total_time": round(total_time, 2),
        "output_file": output_file
    })

if __name__ == "__main__":
    main() 
