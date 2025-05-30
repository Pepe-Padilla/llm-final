import os
from dotenv import load_dotenv
from api.gestor_incidencias import patch_incidencia
from api.sistema import comprobacion_poliza

# Load environment variables
load_dotenv()

def process_resolution(resolution, incidencia):
    if not resolution:
        return "manual sin resolución"
    
    etiqueta = os.getenv("ETIQUETA", "[SPAI] ")
    
    # Get resolution type and metadata
    resolution_type = resolution.get("RESOLUCION AUTOMÁTICA", "manual")
    buzon_reasignacion = resolution.get("BUZON REASIGNACION", "")
    solucion = resolution.get("SOLUCIÓN", "")
    
    # Add label to solution
    solucion = f"{etiqueta}{solucion}"
    
    # Process based on resolution type
    if resolution_type == "manual":
        return "manual"
    
    elif resolution_type == "cierre":
        patch_incidencia(
            incidencia["codIncidencia"],
            "resolver",
            notasResolucion=solucion
        )
        return "cierre"
    
    elif resolution_type == "en espera":
        patch_incidencia(
            incidencia["codIncidencia"],
            "en_espera",
            detalle=solucion
        )
        return "en espera"
    
    elif resolution_type == "reasignacion":
        patch_incidencia(
            incidencia["codIncidencia"],
            "reasignar",
            buzonDestino=buzon_reasignacion,
            detalle=solucion
        )
        return "reasignacion"
    
    elif resolution_type.startswith("api|"):
        # Extract solution code
        cod_solucion = resolution_type.split("|")[1]
        
        # Get policy data from metadata
        poliza = resolution.get("metadata", {}).get("poliza")
        if not poliza:
            return "manual sin poliza"
        
        # Call policy check API
        response = comprobacion_poliza(
            poliza=poliza,
            codSolucion=cod_solucion,
            strJson=str(resolution.get("metadata", {}))
        )
        
        # Process the response recursively
        return process_resolution(response, incidencia)
    
    return "manual sin tipo de resolución" 