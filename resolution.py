import os
from dotenv import load_dotenv
from observabilidad.logger import resolution_logger
from api.gestor_incidencias import patch_incidencia
from api.sistema import comprobacion_poliza
from decorators import handle_api_errors
from metrics import system_metrics

# Load environment variables
load_dotenv()

@handle_api_errors("PATCH_INCIDENCIA", {"status": "error"})
def safe_patch_incidencia(*args, **kwargs):
    """Wrapper seguro para patch_incidencia con manejo de errores."""
    return patch_incidencia(*args, **kwargs)

@handle_api_errors("COMPROBACION_POLIZA", {"metadata": {"RESOLUCION AUTOMÁTICA": "manual", "SOLUCIÓN": "Error en sistema"}})
def safe_comprobacion_poliza(*args, **kwargs):
    """Wrapper seguro para comprobacion_poliza con manejo de errores."""
    return comprobacion_poliza(*args, **kwargs)

def process_resolution(resolution, incidencia, keywords):
    """Procesa la resolución según su tipo y ejecuta las acciones correspondientes."""
    
    if not resolution:
        return {
            "RESOLUCION AUTOMÁTICA": "manual",
            "BUZON REASIGNACION": "",
            "SOLUCIÓN": "No hay soluciones disponibles en el catálogo para esta incidencia, revisar manualmente",
            "estado_api": {"gestor_incidencias": "", "sistema": ""}
        } 
    
    etiqueta = os.getenv("ETIQUETA", "[SPAI] ")
    
    # Get resolution type and metadata
    resolution_type = resolution.get("metadata",{}).get("RESOLUCION AUTOMÁTICA", "manual")
    buzon_reasignacion = resolution.get("metadata",{}).get("BUZON REASIGNACION", "")
    solucion = resolution.get("metadata",{}).get("SOLUCIÓN", "")
    
    # Add label to solution
    solucion = f"{etiqueta}{solucion}"
    
    # Initialize API status
    estado_api = {"gestor_incidencias": "", "sistema": ""}
    
    resolution_logger.info(f"Procesando resolución tipo: {resolution_type}", extra_data={
        "action": "process_resolution",
        "codIncidencia": incidencia["codIncidencia"],
        "resolution_type": resolution_type
    })
    
    # Process based on resolution type
    if resolution_type == "manual":
        resolution_logger.info("Resolución manual", extra_data={
            "action": "manual_resolution",
            "codIncidencia": incidencia["codIncidencia"]
        })
        resolution["estado_api"] = estado_api
        return resolution
    
    elif resolution_type == "cierre":
        try:
            safe_patch_incidencia(incidencia["codIncidencia"], "resolver", notas_resolucion=solucion)
            estado_api["gestor_incidencias"] = "OK"
            resolution_logger.info("Incidencia cerrada exitosamente", extra_data={
                "action": "incident_closed_success",
                "codIncidencia": incidencia["codIncidencia"]
            })
        except Exception as e:
            estado_api["gestor_incidencias"] = f"error: {str(e)}"
            system_metrics.record_api_error("gestor_incidencias")
            resolution_logger.error("Error cerrando incidencia", extra_data={
                "action": "close_incident_error",
                "codIncidencia": incidencia["codIncidencia"],
                "error": str(e)
            })
        resolution["estado_api"] = estado_api
        return resolution
    
    elif resolution_type == "en espera":
        try:
            safe_patch_incidencia(incidencia["codIncidencia"], "en_espera", detalle=solucion)
            estado_api["gestor_incidencias"] = "OK"
            resolution_logger.info("Incidencia puesta en espera exitosamente", extra_data={
                "action": "incident_wait_success",
                "codIncidencia": incidencia["codIncidencia"]
            })
        except Exception as e:
            estado_api["gestor_incidencias"] = f"error: {str(e)}"
            system_metrics.record_api_error("gestor_incidencias")
            resolution_logger.error("Error poniendo incidencia en espera", extra_data={
                "action": "wait_incident_error",
                "codIncidencia": incidencia["codIncidencia"],
                "error": str(e)
            })
        resolution["estado_api"] = estado_api
        return resolution
    
    elif resolution_type == "reasignacion":
        try:
            safe_patch_incidencia(incidencia["codIncidencia"], "reasignar", buzon_destino=buzon_reasignacion, detalle=solucion)
            estado_api["gestor_incidencias"] = "OK"
            resolution_logger.info("Incidencia reasignada exitosamente", extra_data={
                "action": "incident_reassigned_success",
                "codIncidencia": incidencia["codIncidencia"],
                "buzon_destino": buzon_reasignacion
            })
        except Exception as e:
            estado_api["gestor_incidencias"] = f"error: {str(e)}"
            system_metrics.record_api_error("gestor_incidencias")
            resolution_logger.error("Error reasignando incidencia", extra_data={
                "action": "reassign_incident_error",
                "codIncidencia": incidencia["codIncidencia"],
                "error": str(e)
            })
        resolution["estado_api"] = estado_api
        return resolution
    
    elif resolution_type.startswith("api|"):
        cod_solucion = resolution_type.split("|")[1]
        
        resolution_logger.info(f"Procesando resolución API: {cod_solucion}", extra_data={
            "action": "api_resolution_processing",
            "codIncidencia": incidencia["codIncidencia"],
            "cod_solucion": cod_solucion
        })
        
        # Get policy data from metadata
        poliza = str(keywords.get("poliza"))
        if not poliza:
            new_resolution = {
                "metadata": {
                    "RESOLUCION AUTOMÁTICA": "en espera",
                    "BUZON REASIGNACION": "",
                    "SOLUCIÓN": "Por favor, ingrese la poliza para poder continuar con la resolución",
                    "estado_api": estado_api
                }
            }
            return process_resolution(new_resolution, incidencia, keywords)
        
        # Call policy check API
        try:
            response = safe_comprobacion_poliza(poliza=poliza, cod_solucion=cod_solucion, str_json=str(keywords))
            estado_api["sistema"] = "ok"
            resolution_logger.info("Llamada al sistema exitosa", extra_data={
                "action": "system_api_success",
                "codIncidencia": incidencia["codIncidencia"],
                "cod_solucion": cod_solucion
            })
        except Exception as e:
            estado_api["sistema"] = f"error: {str(e)}"
            system_metrics.record_api_error("sistema")
            resolution_logger.error("Error en llamada al sistema", extra_data={
                "action": "system_api_error",
                "codIncidencia": incidencia["codIncidencia"],
                "error": str(e)
            })
            response = {
                "metadata": {
                    "RESOLUCION AUTOMÁTICA": "manual",
                    "BUZON REASIGNACION": "",
                    "SOLUCIÓN": f"[{resolution_type}] Error al llamar al sistema: {str(e)}",
                    "estado_api": estado_api
                }
            }
        
        # Preserve original LLM solution and combine with system response
        if isinstance(response, dict) and "metadata" in response:
            original_solution = solucion
            system_solution = response["metadata"].get("SOLUCIÓN", "")
            combined_solution = f"{original_solution} | Sistema: {system_solution}"
            response["metadata"]["SOLUCIÓN"] = combined_solution
            response["metadata"]["original_resolution_type"] = resolution_type
        
        # Process the response recursively and preserve original resolution type
        result = process_resolution(response, incidencia, keywords)
        
        # Ensure original resolution type is preserved in the final result
        if isinstance(result, dict):
            result["original_resolution_type"] = resolution_type
        
        return result
    
    # Default to manual resolution
    resolution_logger.info("Tipo de resolución no reconocido, usando manual por defecto", extra_data={
        "action": "unknown_resolution_type_fallback",
        "codIncidencia": incidencia["codIncidencia"],
        "resolution_type": resolution_type
    })
    
    resolution["metadata"]["RESOLUCION AUTOMÁTICA"] = "manual"
    resolution["estado_api"] = estado_api
    return resolution