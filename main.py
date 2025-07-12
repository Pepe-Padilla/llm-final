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
from llm.LLMCritic import evaluate_resolution
from resolution import process_resolution
from observabilidad.logger import main_logger
from utils import convert_json_response, convert_eval_response
from collections import Counter
import time

# Load environment variables
load_dotenv()

def process_resolution_with_critic(enhanced_incidencia: Dict[str, Any], all_relevant_solutions: List[Dict[str, Any]], max_retries: int = 2) -> Dict[str, Any]:
    """
    Process resolution with LLM Critic validation.
    
    Args:
        enhanced_incidencia: The enhanced incident with all details
        all_relevant_solutions: List of relevant solutions found
        max_retries: Maximum number of retries (default 2)
    
    Returns:
        Dict with the final resolution
    """
    
    main_logger.info("Iniciando proceso de resolución con crítico", extra_data={
        "action": "start_critic_process",
        "codIncidencia": enhanced_incidencia.get("codIncidencia", "unknown"),
        "solutions_count": len(all_relevant_solutions),
        "max_retries": max_retries
    })
    
    critique_context = ""
    
    for attempt in range(max_retries + 1):
        main_logger.debug(f"Intento {attempt + 1}/{max_retries + 1}", extra_data={
            "action": "critic_attempt",
            "attempt": attempt + 1,
            "max_attempts": max_retries + 1,
            "codIncidencia": enhanced_incidencia.get("codIncidencia", "unknown"),
            "has_critique": len(critique_context) > 0
        })
        
        # Generate resolution
        resolution = None
        if all_relevant_solutions:
            # Include critique in context if available
            context_incident = enhanced_incidencia.copy()
            if critique_context:
                context_incident["critique_context"] = critique_context
                main_logger.debug("Agregando contexto de crítica", extra_data={
                    "action": "add_critique_context",
                    "critique_preview": critique_context[:100] + "..." if len(critique_context) > 100 else critique_context
                })
            
            resolution_response = get_resolution(context_incident, all_relevant_solutions)
            resolution = convert_eval_response(resolution_response, "resolution")
            
            main_logger.debug("Resolución generada", extra_data={
                "action": "resolution_generated",
                "attempt": attempt + 1,
                "resolution_type": resolution.get("metadata", {}).get("RESOLUCION AUTOMÁTICA", ""),
                "has_solution": bool(resolution.get("metadata", {}).get("SOLUCIÓN", ""))
            })
        else:
            resolution = {
                "metadata": {
                    "RESOLUCION AUTOMÁTICA": "manual",
                    "BUZON REASIGNACION": "",
                    "SOLUCIÓN": "No hay soluciones disponibles en el catálogo para esta incidencia, revisar manualmente"
                }
            }
            main_logger.debug("No hay soluciones disponibles, resolución manual", extra_data={
                "action": "no_solutions_manual",
                "attempt": attempt + 1
            })
        
        # Si es una lista, tomar el primer elemento
        if isinstance(resolution, list):
            resolution = resolution[0]
        
        # Evaluate with critic
        main_logger.debug("Evaluando resolución con crítico", extra_data={
            "action": "critic_evaluation",
            "attempt": attempt + 1,
            "resolution_type": resolution.get("metadata", {}).get("RESOLUCION AUTOMÁTICA", "")
        })
        
        critic_response = evaluate_resolution(enhanced_incidencia, resolution)
        critic_evaluation = convert_json_response(critic_response, "critic")
        
        main_logger.debug("Evaluación del crítico recibida", extra_data={
            "action": "critic_evaluation_received",
            "attempt": attempt + 1,
            "status": critic_evaluation.get("status", "unknown"),
            "reason": critic_evaluation.get("reason", "")
        })
        
        status = critic_evaluation.get("status", "APPROVED")
        
        if status == "APPROVED":
            main_logger.info("Resolución aprobada por el crítico", extra_data={
                "action": "resolution_approved",
                "attempt": attempt + 1,
                "reason": critic_evaluation.get("reason", ""),
                "final_resolution_type": resolution.get("metadata", {}).get("RESOLUCION AUTOMÁTICA", "")
            })
            return resolution
        
        elif status == "ALREADY_TRIED":
            main_logger.info("Resolución ya intentada anteriormente, cambiando a manual", extra_data={
                "action": "already_tried_manual",
                "attempt": attempt + 1,
                "reason": critic_evaluation.get("reason", "")
            })
            return {
                "metadata": {
                    "RESOLUCION AUTOMÁTICA": "manual",
                    "BUZON REASIGNACION": "",
                    "SOLUCIÓN": f"La solución propuesta ya fue intentada anteriormente. {critic_evaluation.get('reason', '')}"
                }
            }
        
        elif status == "REJECTED":
            if attempt < max_retries:
                critique_context = critic_evaluation.get("critique", "")
                main_logger.info("Resolución rechazada, reintentando", extra_data={
                    "action": "resolution_rejected_retry",
                    "attempt": attempt + 1,
                    "reason": critic_evaluation.get("reason", ""),
                    "critique_preview": critique_context[:100] + "..." if len(critique_context) > 100 else critique_context
                })
                continue
            else:
                main_logger.info("Resolución rechazada, máximo de reintentos alcanzado", extra_data={
                    "action": "resolution_rejected_max_retries",
                    "attempt": attempt + 1,
                    "reason": critic_evaluation.get("reason", ""),
                    "critique": critic_evaluation.get("critique", "")
                })
                return {
                    "metadata": {
                        "RESOLUCION AUTOMÁTICA": "manual",
                        "BUZON REASIGNACION": "",
                        "SOLUCIÓN": f"No se pudo generar una resolución automática adecuada después de {max_retries + 1} intentos. Última crítica: {critic_evaluation.get('critique', '')}"
                    }
                }
    
    # Fallback (shouldn't reach here)
    main_logger.warning("Fallback a resolución manual", extra_data={
        "action": "fallback_manual",
        "codIncidencia": enhanced_incidencia.get("codIncidencia", "unknown")
    })
    
    return {
        "metadata": {
            "RESOLUCION AUTOMÁTICA": "manual",
            "BUZON REASIGNACION": "",
            "SOLUCIÓN": "Error en el proceso de resolución con crítico, revisar manualmente"
        }
    }

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
        
        relevance_response = check_relevance(incident, solution)
        is_relevant = relevance_response.lower().strip().find("true") >= 0
        
        if is_relevant:
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
            
            enhanced_entry = entry.copy()
            
            # Process attachments for this entry
            attachment_desc = process_attachments(entry)
            if(attachment_desc != ""):
                main_logger.debug("Adjuntos procesados", extra_data={
                    "action": "attachments_processed",
                    "entry_index": j,
                    "attachment_desc": attachment_desc,
                    "entry": entry.get('adjuntos', [])
                })

            if attachment_desc:

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
        rephrase_response = rephrase_incidence(enhanced_incidencia)
        
        main_logger.debug("Respuesta raw de rephrase recibida", extra_data={
            "action": "raw_rephrase_received",
            "response_length": len(rephrase_response),
            "response_preview": rephrase_response[:200] + "..." if len(rephrase_response) > 200 else rephrase_response
        })
        
        # Convert the string response to the required format
        rephrased_versions = convert_json_response(rephrase_response, "rephrase")
        rephrased_versions = [str(incidencia["descripcion"])] + rephrased_versions
        
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
        
        # Get final resolution with critic validation
        main_logger.info("Generando resolución final con validación crítica...")
        resolution = process_resolution_with_critic(enhanced_incidencia, all_relevant_solutions)

        # Extract keywords and add to metadata
        main_logger.info("Extrayendo palabras clave...")
        keywords_response = extract_keywords(enhanced_incidencia)

        # Convert the string response to the required format
        keywords = convert_json_response(keywords_response, "keywords")
        
        main_logger.debug("Palabras clave extraídas", extra_data={
            "action": "keywords_extracted",
            "keywords":keywords
        })
        
        # Process the resolution
        main_logger.info("Ejecutando resolución")
        result = process_resolution(resolution, incidencia, keywords)

        result["keywords"] = keywords
        
        main_logger.debug("Resolución procesada", extra_data={
            "action": "resolution_processed",
            "resolution_type": result.get("RESOLUCION AUTOMÁTICA"),
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