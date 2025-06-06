import os
from dotenv import load_dotenv
from api.gestor_incidencias import patch_incidencia
from api.sistema import comprobacion_poliza

# Load environment variables
load_dotenv()

def process_resolution(resolution, incidencia, keywords):
    if not resolution:
        return {
            "RESOLUCION AUTOMÁTICA": "manual",
            "BUZON REASIGNACION": "",
            "SOLUCIÓN": "No hay soluciones disponibles en el catálogo para esta incidencia, revisar manualmente",
            "estado_api": {
                "gestor_incidencias": "",
                "sistema": ""
            }
        } 
    
    etiqueta = os.getenv("ETIQUETA", "[SPAI] ")
    
    print("-----")
    print(type(resolution))
    print(resolution)
    # Handle case where resolution is a list
    if isinstance(resolution, list) and len(resolution) > 0:
        resolution = resolution[0]
    print("-----")
    # Get resolution type and metadata
    resolution_type = resolution.get("metadata",{}).get("RESOLUCION AUTOMÁTICA", "manual")
    buzon_reasignacion = resolution.get("BUZON REASIGNACION", "")
    solucion = resolution.get("SOLUCIÓN", "")
    
    # Add label to solution
    solucion = f"{etiqueta}{solucion}"
    
    # Initialize API status
    estado_api = {
        "gestor_incidencias": "",
        "sistema": ""
    }
    
    # Process based on resolution type
    if resolution_type == "manual":
        resolution["estado_api"] = estado_api
        return resolution
    
    elif resolution_type == "cierre":
        try:
            patch_incidencia(
                incidencia["codIncidencia"],
                "resolver",
                notasResolucion=solucion
            )
            estado_api["gestor_incidencias"] = "OK"
        except Exception as e:
            estado_api["gestor_incidencias"] = f"error: {str(e)}"
        resolution["estado_api"] = estado_api
        return resolution
    
    elif resolution_type == "en espera":
        try:
            patch_incidencia(
                incidencia["codIncidencia"],
                "en_espera",
                detalle=solucion
            )
            estado_api["gestor_incidencias"] = "OK"
        except Exception as e:
            estado_api["gestor_incidencias"] = f"error: {str(e)}"
        resolution["estado_api"] = estado_api
        return resolution
    
    elif resolution_type == "reasignacion":
        try:
            patch_incidencia(
                incidencia["codIncidencia"],
                "reasignar",
                buzonDestino=buzon_reasignacion,
                detalle=solucion
            )
            estado_api["gestor_incidencias"] = "OK"
        except Exception as e:
            estado_api["gestor_incidencias"] = f"error: {str(e)}"
        resolution["estado_api"] = estado_api
        return resolution
    
    elif resolution_type.startswith("api|"):
        # Extract solution code
        cod_solucion = resolution_type.split("|")[1]
        
        # Get policy data from metadata
        poliza = str(keywords.get("poliza"))
        if not poliza:
            new_resolution = {
                "RESOLUCION AUTOMÁTICA": "en espera",
                "BUZON REASIGNACION": "",
                "SOLUCIÓN": "Por favor, ingrese la poliza para poder continuar con la resolución",
                "estado_api": estado_api
            }
            return process_resolution(new_resolution, incidencia, keywords)
        
        # Call policy check API
        try:
            response = comprobacion_poliza(
                poliza=poliza,
                codSolucion=cod_solucion,
                strJson=str(keywords)
            )
            estado_api["sistema"] = "ok"
        except Exception as e:
            estado_api["sistema"] = f"error: {str(e)}"
            response = {
                "RESOLUCION AUTOMÁTICA": "manual",
                "BUZON REASIGNACION": "",
                "SOLUCIÓN": f"Error al llamar al sistema: {str(e)}",
                "estado_api": estado_api
            }
        
        # Process the response recursively
        return process_resolution(response, incidencia, keywords)
    
    # Default to manual resolution
    resolution["RESOLUCION AUTOMÁTICA"] = "manual"
    resolution["estado_api"] = estado_api
    return resolution