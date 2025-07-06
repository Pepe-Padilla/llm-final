import os
import json
from datetime import datetime
from typing import List, Dict, Any
from dotenv import load_dotenv
from api.gestor_incidencias import get_incidencias
from llm.LLMRephrase import rephrase_incidence
from llm.LLMRelevance import check_relevance
from llm.LLMResolution import get_resolution
from llm.LLMQuery import query_vector_db
from llm.LLMKeywords import extract_keywords
from llm.LLMImageAnalysis import process_attachments
from resolution import process_resolution
from observabilidad.logger import main_logger
from collections import Counter
import time

# Load environment variables
load_dotenv()

def get_relevant_solutions(incident: str) -> List[Dict[str, Any]]:
    """Get relevant solutions from vector DB for a given incident."""

    main_logger.debug("Buscando incidentes similares", extra_data={
        "action": "query_vector_db",
        "incident_length": len(incident),
        "incident_preview": incident[:100] + "..." if len(incident) > 100 else incident
    })

    # Get similar incidents from vector DB
    similar_incidents = query_vector_db(incident)
    
    main_logger.debug(f"Encontrados {len(similar_incidents)} incidentes similares", extra_data={
        "action": "similar_incidents_found",
        "count": len(similar_incidents)
    })
    
    # Filter relevant solutions
    relevant_solutions = []

    for i, solution in enumerate(similar_incidents):
        main_logger.debug(f"Evaluando solución {i+1}/{len(similar_incidents)}", extra_data={
            "action": "check_relevance",
            "solution_index": i,
            "total_solutions": len(similar_incidents),
            "solution_keys": list(solution.keys()) if isinstance(solution, dict) else []
        })
        
        if check_relevance(incident, solution):
            relevant_solutions.append(solution)
            main_logger.debug("Solución marcada como relevante", extra_data={
                "action": "solution_relevant",
                "solution_index": i,
                "solution_id": solution.get("id", "unknown")
            })
    
    main_logger.debug(f"Total de soluciones relevantes: {len(relevant_solutions)}", extra_data={
        "action": "relevance_filter_complete",
        "total_similar": len(similar_incidents),
        "total_relevant": len(relevant_solutions)
    })
    
    return relevant_solutions

def main():
    # Start timing
    start_time = time.time()
    
    # Get open incidents
    main_logger.info("Obteniendo incidencias abiertas...")
    incidencias = get_incidencias()
    total_incidencias = len(incidencias)
    main_logger.info(f"Total de incidencias a procesar: {total_incidencias}", extra_data={
        "action": "incidents_loaded",
        "total_incidents": total_incidencias
    })
    
    # Process each incident
    resultados = []
    tipos_resolucion = []
    errores_api = {
        "gestor_incidencias": 0,
        "sistema": 0
    }
    
    for i, incidencia in enumerate(incidencias, 1):
        main_logger.info(f"Procesando incidencia {i}/{total_incidencias}", extra_data={
            "action": "process_incident",
            "incident_index": i,
            "total_incidents": total_incidencias,
            "codIncidencia": incidencia['codIncidencia'],
            "titulo": incidencia['titulo'],
            "has_historial": len(incidencia.get('historial', [])) > 0
        })
        
        # Process attachments from historial and enhance historial descriptions
        main_logger.info("Procesando adjuntos...")
        enhanced_historial = []
        
        for j, entry in enumerate(incidencia.get('historial', [])):
            main_logger.debug(f"Procesando entrada {j+1} del historial", extra_data={
                "action": "process_historial_entry",
                "entry_index": j,
                "total_entries": len(incidencia.get('historial', [])),
                "entry_has_attachments": bool(entry.get('adjuntos')),
                "entry_has_detail": bool(entry.get('detalle'))
            })
            
            enhanced_entry = entry.copy()
            
            # Process attachments for this entry
            attachment_desc = process_attachments(entry)
            if attachment_desc:
                main_logger.debug("Adjuntos procesados", extra_data={
                    "action": "attachments_processed",
                    "entry_index": j,
                    "attachment_desc_length": len(attachment_desc),
                    "attachment_desc_preview": attachment_desc[:100] + "..." if len(attachment_desc) > 100 else attachment_desc
                })
                
                if entry.get('detalle'):
                    # Enhance the detail with attachment analysis
                    enhanced_entry['detalle'] = entry['detalle'] + " | Análisis de adjuntos: " + attachment_desc
                else:
                    # If no detail exists, create one with attachment analysis
                    enhanced_entry['detalle'] = "Análisis de adjuntos: " + attachment_desc
            else:
                main_logger.debug("No se encontraron adjuntos para procesar", extra_data={
                    "action": "no_attachments",
                    "entry_index": j
                })
            
            enhanced_historial.append(enhanced_entry)
        
        # Create enhanced incident with improved historial
        enhanced_incidencia = incidencia.copy()
        enhanced_incidencia['historial'] = enhanced_historial
        
        main_logger.debug("Incidente mejorado creado", extra_data={
            "action": "enhanced_incident_created",
            "original_historial_count": len(incidencia.get('historial', [])),
            "enhanced_historial_count": len(enhanced_historial)
        })
        
        # Get rephrased versions of the enhanced incident
        main_logger.info("Generando consultas...")
        rephrased_versions = rephrase_incidence(enhanced_incidencia)
        
        main_logger.debug(f"Versiones reformuladas generadas: {len(rephrased_versions)}", extra_data={
            "action": "rephrased_versions_created",
            "versions_count": len(rephrased_versions),
            "versions_preview": [v[:50] + "..." if len(v) > 50 else v for v in rephrased_versions[:3]]
        })
        
        # Get relevant solutions for each version
        main_logger.info("Buscando soluciones relevantes...")
        all_relevant_solutions = []
        progress = 0
        total_rows = len(rephrased_versions)
        processed = 0
        
        for k, version in enumerate(rephrased_versions):
            processed += 1
            progress = (processed / total_rows) * 100
            
            main_logger.debug(f"Procesando versión {k+1}/{len(rephrased_versions)}", extra_data={
                "action": "process_version",
                "version_index": k,
                "total_versions": len(rephrased_versions),
                "progress_percentage": round(progress, 1),
                "version_preview": version[:100] + "..." if len(version) > 100 else version
            })
            
            relevant_solutions = get_relevant_solutions(version)
            all_relevant_solutions.extend(relevant_solutions)
            
            main_logger.debug(f"Soluciones encontradas para versión {k+1}: {len(relevant_solutions)}", extra_data={
                "action": "version_solutions_found",
                "version_index": k,
                "solutions_count": len(relevant_solutions)
            })
        
        main_logger.debug(f"Total de soluciones relevantes encontradas: {len(all_relevant_solutions)}", extra_data={
            "action": "all_solutions_collected",
            "total_solutions": len(all_relevant_solutions),
            "unique_solutions": len(set(str(s) for s in all_relevant_solutions))
        })
        
        # Get final resolution from all relevant solutions
        main_logger.info("Generando resolución final...")
        resolution = None
        if all_relevant_solutions:
            resolution = get_resolution(enhanced_incidencia, all_relevant_solutions)
            main_logger.debug("Resolución generada automáticamente", extra_data={
                "action": "auto_resolution_generated",
                "solutions_used": len(all_relevant_solutions),
                "resolution_keys": list(resolution.keys()) if isinstance(resolution, dict) else []
            })
        else:
            resolution = {
                "RESOLUCION AUTOMÁTICA": "manual",
                "BUZON REASIGNACION": "",
                "SOLUCIÓN": "No hay soluciones disponibles en el catálogo para esta incidencia, revisar manualmente"
            }
            main_logger.debug("No se encontraron soluciones, resolución manual", extra_data={
                "action": "manual_resolution_fallback",
                "reason": "no_solutions_available"
            })
        
        # Extract keywords and add to metadata
        main_logger.info("Extrayendo palabras clave...")
        keywords = extract_keywords(enhanced_incidencia)
        
        main_logger.debug("Palabras clave extraídas", extra_data={
            "action": "keywords_extracted",
            "keywords_count": len(keywords),
            "keywords": keywords[:10] if len(keywords) > 10 else keywords
        })
        
        # Process the resolution
        main_logger.info("Ejecutando resolución")
        result = process_resolution(resolution, incidencia, keywords)

        result["keywords"] = keywords
        
        main_logger.debug("Resolución procesada", extra_data={
            "action": "resolution_processed",
            "resolution_type": resolution.get("RESOLUCION AUTOMÁTICA", result.get("RESOLUCION AUTOMÁTICA")),
            "result_keys": list(result.keys()),
            "api_status": result.get("estado_api", {})
        })

        # Store result and resolution type
        resultados.append({
            "incidencia": incidencia,
            "resolucion": result
        })
        
        resolucion_automatica = resolution.get("metadata",{}).get("RESOLUCION AUTOMÁTICA")
        if resolucion_automatica == None:
            resolucion_automatica = "api resolution ->" +  result.get("RESOLUCION AUTOMÁTICA")
        tipos_resolucion.append(resolucion_automatica)
        
        # Count API errors
        estado_api = result.get("estado_api", {})
        if estado_api.get("gestor_incidencias", "").startswith("error"):
            errores_api["gestor_incidencias"] += 1
        if estado_api.get("sistema", "").startswith("error"):
            errores_api["sistema"] += 1
        
        main_logger.info(f"Resolución completada: {resolucion_automatica}", extra_data={
            "action": "incident_completed",
            "incident_index": i,
            "resolucion": resolucion_automatica,
            "errores_gestor": estado_api.get("gestor_incidencias", ""),
            "errores_sistema": estado_api.get("sistema", ""),
            "processing_time": time.time() - start_time
        })
    
    # Calculate statistics
    stats = Counter(tipos_resolucion)
    
    # Save report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    report_path = f"resources/reporte{timestamp}.json"
    
    main_logger.debug("Guardando reporte", extra_data={
        "action": "save_report",
        "report_path": report_path,
        "results_count": len(resultados)
    })
    
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)
    
    # Log final statistics
    total_time = time.time() - start_time
    main_logger.info("=== Estadísticas Finales ===", extra_data={
        "action": "final_statistics",
        "total_incidencias": total_incidencias,
        "tiempo_total": round(total_time, 2),
        "tiempo_promedio_por_incidencia": round(total_time / total_incidencias, 2) if total_incidencias > 0 else 0,
        "distribucion_resoluciones": dict(stats),
        "errores_gestor": errores_api['gestor_incidencias'],
        "errores_sistema": errores_api['sistema'],
        "reporte_path": report_path,
        "success_rate": round((total_incidencias - errores_api['gestor_incidencias'] - errores_api['sistema']) / total_incidencias * 100, 2) if total_incidencias > 0 else 0
    })

if __name__ == "__main__":
    main() 