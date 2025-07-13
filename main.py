import json
import time
from datetime import datetime
from typing import List, Dict, Any
from dotenv import load_dotenv
from api.gestor_incidencias import get_incidencias
from llm.LLMRephrase import rephrase_incidence
from llm.LLMRelevance import check_relevance
from llm.LLMQuery import query_vector_db
from llm.LLMKeywords import extract_keywords
from llm.LLMImageAnalysis import process_attachments
from critico import process_resolution_with_critic
from resolution import process_resolution
from observabilidad.logger import main_logger
from utils import convert_json_response
from collections import Counter
from metrics import system_metrics
from decorators import log_execution_time, handle_api_errors

# Load environment variables
load_dotenv()


@handle_api_errors("VECTOR_DB_QUERY", [])
def get_relevant_solutions(incident: str) -> List[Dict[str, Any]]:
    """Obtiene soluciones relevantes de la base de datos vectorial."""
    
    similar_incidents = query_vector_db(incident)
    main_logger.info(f"Encontrados {len(similar_incidents)} incidentes similares")
    
    relevant_solutions = []
    for solution in similar_incidents:
        relevance_response = check_relevance(incident, solution)
        if relevance_response.lower().strip().find("true") >= 0:
            relevant_solutions.append(solution)
    
    main_logger.info(f"Total de soluciones relevantes: {len(relevant_solutions)}")
    return relevant_solutions


def process_incident_attachments(incidencia: Dict[str, Any]) -> Dict[str, Any]:
    """Procesa adjuntos del historial y mejora las descripciones."""
    enhanced_historial = []
    attachments_processed = 0
    
    for entry in incidencia.get('historial', []):
        enhanced_entry = entry.copy()
        attachment_desc = process_attachments(entry)
        
        if attachment_desc:
            attachments_processed += 1
            if entry.get('detalle'):
                enhanced_entry['detalle'] = entry['detalle'] + " | Análisis de adjuntos: " + attachment_desc
            else:
                enhanced_entry['detalle'] = "Análisis de adjuntos: " + attachment_desc
        
        enhanced_historial.append(enhanced_entry)
    
    enhanced_incidencia = incidencia.copy()
    enhanced_incidencia['historial'] = enhanced_historial
    
    # Debug significativo: información de procesamiento de adjuntos
    main_logger.debug("Incidente mejorado con adjuntos", extra_data={
        "action": "enhanced_incident_created",
        "codIncidencia": incidencia.get("codIncidencia", "unknown"),
        "original_historial_count": len(incidencia.get('historial', [])),
        "enhanced_historial_count": len(enhanced_historial),
        "attachments_processed": attachments_processed
    })
    
    return enhanced_incidencia


def collect_relevant_solutions(rephrased_versions: List[str]) -> List[Dict[str, Any]]:
    """Recolecta todas las soluciones relevantes para las versiones reformuladas."""
    all_relevant_solutions = []
    
    for k, version in enumerate(rephrased_versions):
        main_logger.info(f"Procesando versión {k+1}/{len(rephrased_versions)}")
        
        # Debug significativo: preview de la versión que se está procesando
        main_logger.debug(f"Procesando versión reformulada {k+1}", extra_data={
            "action": "process_version",
            "version_index": k + 1,
            "total_versions": len(rephrased_versions),
            "version_preview": version[:100] + "..." if len(version) > 100 else version
        })
        
        relevant_solutions = get_relevant_solutions(version)
        all_relevant_solutions.extend(relevant_solutions)
        
        # Debug significativo: cuántas soluciones se encontraron por versión
        main_logger.debug(f"Soluciones encontradas para versión {k+1}: {len(relevant_solutions)}", extra_data={
            "action": "version_solutions_found",
            "version_index": k + 1,
            "solutions_count": len(relevant_solutions)
        })
    
    # Debug significativo: resumen total de soluciones
    unique_solutions = len(set(str(s) for s in all_relevant_solutions))
    main_logger.debug(f"Recolección de soluciones completada", extra_data={
        "action": "all_solutions_collected",
        "total_solutions": len(all_relevant_solutions),
        "unique_solutions": unique_solutions,
        "duplicate_solutions": len(all_relevant_solutions) - unique_solutions
    })
    
    main_logger.info(f"Total de soluciones relevantes encontradas: {len(all_relevant_solutions)}")
    return all_relevant_solutions


@log_execution_time("SISTEMA_COMPLETO")
def main():
    """Función principal del sistema."""
    start_time = time.time()
    
    # Obtener incidencias abiertas
    main_logger.info("Obteniendo incidencias abiertas...")
    incidencias = get_incidencias()
    total_incidencias = len(incidencias)
    main_logger.info(f"Total de incidencias a procesar: {total_incidencias}")
    
    # Procesar cada incidencia
    resultados = []
    tipos_resolucion = []
    errores_api = {"gestor_incidencias": 0, "sistema": 0}
    
    for i, incidencia in enumerate(incidencias, 1):
        incident_code = incidencia['codIncidencia']
        system_metrics.record_incident_start(incident_code)
        
        main_logger.info(f"Procesando incidencia {i}/{total_incidencias}: {incident_code}")
        
        try:
            # Procesar adjuntos y mejorar historial
            enhanced_incidencia = process_incident_attachments(incidencia)
            
            # Generar versiones reformuladas
            main_logger.info("Generando consultas...")
            rephrase_response = rephrase_incidence(enhanced_incidencia)
            
            # Debug significativo: respuesta cruda del rephrase
            main_logger.debug("Respuesta de reformulación recibida", extra_data={
                "action": "rephrase_response_received",
                "codIncidencia": incident_code,
                "response_length": len(rephrase_response),
                "response_preview": rephrase_response[:200] + "..." if len(rephrase_response) > 200 else rephrase_response
            })
            
            rephrased_versions = convert_json_response(rephrase_response, "rephrase")
            rephrased_versions = [str(incidencia["descripcion"])] + rephrased_versions
            
            # Debug significativo: versiones reformuladas generadas
            main_logger.debug(f"Versiones reformuladas generadas", extra_data={
                "action": "rephrased_versions_created",
                "codIncidencia": incident_code,
                "versions_count": len(rephrased_versions),
                "versions_preview": [v[:50] + "..." if len(v) > 50 else v for v in rephrased_versions[:3]]
            })
            
            # Obtener soluciones relevantes
            main_logger.info("Buscando soluciones relevantes...")
            all_relevant_solutions = collect_relevant_solutions(rephrased_versions)
            
            # Registrar métricas de soluciones encontradas
            system_metrics.record_solutions_found(len(all_relevant_solutions))
            
            # Generar resolución final con validación crítica
            main_logger.info("Generando resolución final con validación crítica...")
            resolution = process_resolution_with_critic(enhanced_incidencia, all_relevant_solutions)

            # Extraer palabras clave
            main_logger.info("Extrayendo palabras clave...")
            keywords_response = extract_keywords(enhanced_incidencia)
            keywords = convert_json_response(keywords_response, "keywords")
            
            # Debug significativo: palabras clave extraídas
            main_logger.debug("Palabras clave extraídas", extra_data={
                "action": "keywords_extracted",
                "codIncidencia": incident_code,
                "keywords": keywords,
                "keywords_count": len(keywords)
            })
            
            # Procesar la resolución
            main_logger.info("Ejecutando resolución")
            result = process_resolution(resolution, incidencia, keywords)
            result["keywords"] = keywords
            
            # Almacenar resultado y tipo de resolución
            resultados.append({"incidencia": incidencia, "resolucion": result})

            resolucion_automatica = resolution.get("metadata",{}).get("RESOLUCION AUTOMÁTICA")
            if resolucion_automatica == None:
                resolucion_automatica = "manual"
                system_metrics.record_processing_error("Error obteniendo resolución automática", incident_code)
            
            # Rastrear tipos de resolución originales para casos api|xxx
            final_resolution_type = result.get("RESOLUCION AUTOMÁTICA", resolucion_automatica)
            original_resolution_type = result.get("original_resolution_type", resolucion_automatica)
            
            # Formato para estadísticas: mostrar "api|xxx[final]" para casos api
            if original_resolution_type != final_resolution_type and original_resolution_type.startswith("api|"):
                display_resolution = f"{original_resolution_type}[{final_resolution_type}]"
            else:
                display_resolution = resolucion_automatica
            
            tipos_resolucion.append(display_resolution)
            system_metrics.record_incident_end(display_resolution)
            
            # Contar errores de API
            estado_api = result.get("estado_api", {})
            if estado_api.get("gestor_incidencias", "").startswith("error"):
                errores_api["gestor_incidencias"] += 1
                system_metrics.record_api_error("gestor_incidencias")
            if estado_api.get("sistema", "").startswith("error"):
                errores_api["sistema"] += 1
                system_metrics.record_api_error("sistema")
            
            main_logger.info(f"Resolución completada: {display_resolution}")
            
        except Exception as e:
            system_metrics.record_processing_error(str(e), incident_code)
            main_logger.error(f"Error procesando incidencia {incident_code}", extra_data={
                "action": "incident_processing_error",
                "codIncidencia": incident_code,
                "error": str(e)
            })
    
    # Calcular estadísticas
    stats = Counter(tipos_resolucion)
    
    # Guardar reporte
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    report_path = f"resources/reporte{timestamp}.json"
    
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)
    
    # Estadísticas finales tradicionales
    total_time = time.time() - start_time
    main_logger.info("=== Estadísticas Finales ===", extra_data={
        "action": "final_statistics",
        "total_incidencias": total_incidencias,
        "tiempo_total": round(total_time, 2),
        "distribucion_resoluciones": dict(stats),
        "errores_gestor": errores_api['gestor_incidencias'],
        "errores_sistema": errores_api['sistema'],
        "reporte_path": report_path
    })
    
    # Métricas avanzadas del sistema
    system_metrics.log_final_metrics()


if __name__ == "__main__":
    main() 