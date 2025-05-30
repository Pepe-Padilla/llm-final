import os
import json
from datetime import datetime
from dotenv import load_dotenv
from api.gestor_incidencias import get_incidencias
from llm.LLMRephrase import rephrase_incidence
from llm.LLMRelevantResponse import check_relevance
from llm.LLMResolution import get_resolution
from resolution import process_resolution

# Load environment variables
load_dotenv()

def main():
    # Get open incidents
    incidencias = get_incidencias()
    
    # Process each incident
    resultados = []
    for incidencia in incidencias:
        # Get rephrased versions of the incident
        rephrased = rephrase_incidence(incidencia)
        
        # Get relevant responses for each rephrased version
        relevant_responses = []
        for version in rephrased:
            if check_relevance(version, incidencia):
                relevant_responses.append(version)
        
        # Get final resolution
        resolution = None
        if relevant_responses:
            resolution = get_resolution(relevant_responses, incidencia)
        
        # Process the resolution
        result = process_resolution(resolution, incidencia)
        resultados.append({
            "incidencia": incidencia["codIncidencia"],
            "resolucion": result
        })
    
    # Save report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    report_path = f"resources/reporte{timestamp}.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main() 