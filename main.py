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
from resolution import process_resolution
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
    print("Obteniendo incidencias abiertas...")
    incidencias = get_incidencias()
    total_incidencias = len(incidencias)
    print(f"Total de incidencias a procesar: {total_incidencias}")
    
    # Process each incident
    resultados = []
    tipos_resolucion = []
    errores_api = {
        "gestor_incidencias": 0,
        "sistema": 0
    }
    
    for i, incidencia in enumerate(incidencias, 1):
        print(f"\nProcesando incidencia {i}/{total_incidencias}")
        print(f"Código: {incidencia['codIncidencia']}")
        
        # Get rephrased versions of the incident
        print("Generando consultas...")
        rephrased_versions = rephrase_incidence(incidencia)
        
        # Get relevant solutions for each version
        print("Buscando soluciones relevantes...")
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
        print("\nGenerando resolución final...")
        resolution = None
        if all_relevant_solutions:
            resolution = get_resolution(incidencia, all_relevant_solutions)
        else:
            resolution = {
                "RESOLUCION AUTOMÁTICA": "manual",
                "BUZON REASIGNACION": "",
                "SOLUCIÓN": "No hay soluciones disponibles en el catálogo para esta incidencia, revisar manualmente"
            }
        
        # Extract keywords and add to metadata
        print("Extrayendo palabras clave...")
        keywords = extract_keywords(incidencia)
        
        # Process the resolution
        print("Ejectuadndo resolución")
        result = process_resolution(resolution, incidencia, keywords)

        result["keywords"] = keywords
        
        # Store result and resolution type
        resultados.append({
            "incidencia": incidencia,
            "resolucion": result
        })
        # print(result)
        resolucion_automatica = result.get("metadata",{}).get("RESOLUCION AUTOMÁTICA")
        tipos_resolucion.append(resolucion_automatica)
        
        # Count API errors
        estado_api = result.get("estado_api", {})
        if estado_api.get("gestor_incidencias", "").startswith("error"):
            errores_api["gestor_incidencias"] += 1
        if estado_api.get("sistema", "").startswith("error"):
            errores_api["sistema"] += 1
        
        print(f"Resolución: {resolucion_automatica}")
        if estado_api.get("gestor_incidencias", "").startswith("error"):
            print(f"Error gestor incidencias: {estado_api['gestor_incidencias']}")
        if estado_api.get("sistema", "").startswith("error"):
            print(f"Error sistema: {estado_api['sistema']}")
    
    # Calculate statistics
    stats = Counter(tipos_resolucion)
    
    # Save report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    report_path = f"resources/reporte{timestamp}.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)
    
    # Print final statistics
    print("\n=== Estadísticas Finales ===")
    print(f"Total de incidencias procesadas: {total_incidencias}")
    print(f"Tiempo total: {time.time() - start_time:.2f} segundos")
    print("\nDistribución de resoluciones:")
    for tipo, cantidad in stats.items():
        porcentaje = (cantidad / total_incidencias) * 100
        print(f"- {tipo}: {cantidad} ({porcentaje:.1f}%)")
    print("\nErrores de API:")
    print(f"- Gestor de incidencias: {errores_api['gestor_incidencias']} errores")
    print(f"- Sistema: {errores_api['sistema']} errores")
    print(f"\nReporte guardado en: {report_path}")

if __name__ == "__main__":
    main() 