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

    # print(incident)

    # Get similar incidents from vector DB
    similar_incidents = query_vector_db(incident)
    
    # Filter relevant solutions
    relevant_solutions = []

    # print(len(similar_incidents))
    for solution in similar_incidents:
        # print(solution)
        if check_relevance(incident, solution):
            relevant_solutions.append(solution)
            # print("relevante")
    
    return relevant_solutions

def main():
    # Start timing
    start_time = time.time()
    
    # Get open incidents
    main_logger.info("Obteniendo incidencias abiertas...")
    incidencias = get_incidencias()
    total_incidencias = len(incidencias)
    main_logger.info(f"Total de incidencias a procesar: {total_incidencias}")
    
    # Process each incident
    resultados = []
    tipos_resolucion = []
    errores_api = {
        "gestor_incidencias": 0,
        "sistema": 0
    }
    
    for i, incidencia in enumerate(incidencias, 1):
        main_logger.info(f"Procesando incidencia {i}/{total_incidencias}", {
            "codIncidencia": incidencia['codIncidencia'],
            "titulo": incidencia['titulo']
        })
        
        # Process attachments from historial and enhance historial descriptions
        main_logger.info("Procesando adjuntos...")
        enhanced_historial = []
        
        for entry in incidencia.get('historial', []):
            enhanced_entry = entry.copy()
            
            # Process attachments for this entry
            attachment_desc = process_attachments(entry)
            if attachment_desc and entry.get('detalle'):
                # Enhance the detail with attachment analysis
                enhanced_entry['detalle'] = entry['detalle'] + " | Análisis de adjuntos: " + attachment_desc
            elif attachment_desc:
                # If no detail exists, create one with attachment analysis
                enhanced_entry['detalle'] = "Análisis de adjuntos: " + attachment_desc
            
            enhanced_historial.append(enhanced_entry)
        
        # Create enhanced incident with improved historial
        enhanced_incidencia = incidencia.copy()
        enhanced_incidencia['historial'] = enhanced_historial
        
        # Get rephrased versions of the enhanced incident
        main_logger.info("Generando consultas...")
        rephrased_versions = rephrase_incidence(enhanced_incidencia)
        
        # Get relevant solutions for each version
        main_logger.info("Buscando soluciones relevantes...")
        all_relevant_solutions = []
        progress = 0
        total_rows = len(rephrased_versions)
        processed = 0
        for version in rephrased_versions:
            processed += 1
            progress = (processed / total_rows) * 100
            print(f"\rProgress: {progress:.1f}% ({processed}/{total_rows})", end="")
            relevant_solutions = get_relevant_solutions(version)
            all_relevant_solutions.extend(relevant_solutions)
        
        # Get final resolution from all relevant solutions
        main_logger.info("Generando resolución final...")
        resolution = None
        if all_relevant_solutions:
            resolution = get_resolution(enhanced_incidencia, all_relevant_solutions)
        else:
            resolution = {
                "RESOLUCION AUTOMÁTICA": "manual",
                "BUZON REASIGNACION": "",
                "SOLUCIÓN": "No hay soluciones disponibles en el catálogo para esta incidencia, revisar manualmente"
            }
        
        # Extract keywords and add to metadata
        main_logger.info("Extrayendo palabras clave...")
        keywords = extract_keywords(enhanced_incidencia)
        
        # Process the resolution
        main_logger.info("Ejecutando resolución")
        result = process_resolution(resolution, incidencia, keywords)

        result["keywords"] = keywords
        
        # Store result and resolution type
        resultados.append({
            "incidencia": incidencia,
            "resolucion": result
        })
        # print(result)
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
        
        main_logger.info(f"Resolución completada: {resolucion_automatica}", {
            "resolucion": resolucion_automatica,
            "errores_gestor": estado_api.get("gestor_incidencias", ""),
            "errores_sistema": estado_api.get("sistema", "")
        })
    
    # Calculate statistics
    stats = Counter(tipos_resolucion)
    
    # Save report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    report_path = f"resources/reporte{timestamp}.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)
    
    # Log final statistics
    main_logger.info("=== Estadísticas Finales ===", {
        "total_incidencias": total_incidencias,
        "tiempo_total": time.time() - start_time,
        "distribucion_resoluciones": dict(stats),
        "errores_gestor": errores_api['gestor_incidencias'],
        "errores_sistema": errores_api['sistema'],
        "reporte_path": report_path
    })

if __name__ == "__main__":
    main() 