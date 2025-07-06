import os
from dotenv import load_dotenv
from observabilidad.logger import resolution_logger
from api.gestor_incidencias import patch_incidencia
from api.sistema import comprobacion_poliza

# Load environment variables
load_dotenv()

def process_resolution(resolution, incidencia, keywords):
    resolution_logger.debug("Iniciando procesamiento de resolución", extra_data={
        "action": "start_resolution_processing",
        "codIncidencia": incidencia["codIncidencia"],
        "resolution_type": type(resolution).__name__,
        "keywords_count": len(keywords),
        "keywords": list(keywords.keys())
    })
    
    if not resolution:
        resolution_logger.debug("No hay resolución disponible, usando resolución manual por defecto", extra_data={
            "action": "no_resolution_fallback",
            "codIncidencia": incidencia["codIncidencia"]
        })
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
    
    resolution_logger.debug("Resolución recibida", extra_data={
        "action": "resolution_received",
        "codIncidencia": incidencia["codIncidencia"],
        "resolution_type": type(resolution).__name__,
        "resolution_keys": list(resolution.keys()) if isinstance(resolution, dict) else [],
        "resolution_preview": str(resolution)[:200] + "..." if len(str(resolution)) > 200 else str(resolution)
    })
    
    # Get resolution type and metadata
    resolution_type = resolution.get("metadata",{}).get("RESOLUCION AUTOMÁTICA", "manual")
    buzon_reasignacion = resolution.get("metadata",{}).get("BUZON REASIGNACION", "")
    solucion = resolution.get("metadata",{}).get("SOLUCIÓN", "")
    
    resolution_logger.debug("Metadatos de resolución extraídos", extra_data={
        "action": "resolution_metadata_extracted",
        "resolution_type": resolution_type,
        "buzon_reasignacion": buzon_reasignacion,
        "solucion_length": len(solucion) if solucion else 0,
        "etiqueta": etiqueta
    })
    
    # Add label to solution
    solucion = f"{etiqueta}{solucion}"
    
    # Initialize API status
    estado_api = {
        "gestor_incidencias": "",
        "sistema": ""
    }
    
    resolution_logger.debug("Procesando resolución según tipo", extra_data={
        "action": "process_by_type",
        "codIncidencia": incidencia["codIncidencia"],
        "resolution_type": resolution_type,
        "solucion_with_label": solucion
    })
    
    # Process based on resolution type
    if resolution_type == "manual":
        resolution_logger.info("Resolución manual", extra_data={
            "action": "manual_resolution",
            "codIncidencia": incidencia["codIncidencia"],
            "tipo": "manual",
            "solucion": solucion
        })
        resolution["estado_api"] = estado_api
        return resolution
    
    elif resolution_type == "cierre":
        resolution_logger.debug("Intentando cerrar incidencia", extra_data={
            "action": "close_incident_attempt",
            "codIncidencia": incidencia["codIncidencia"],
            "solucion": solucion
        })
        
        try:
            patch_incidencia(
                incidencia["codIncidencia"],
                "resolver",
                notasResolucion=solucion
            )
            estado_api["gestor_incidencias"] = "OK"
            resolution_logger.info("Incidencia cerrada exitosamente", extra_data={
                "action": "incident_closed_success",
                "codIncidencia": incidencia["codIncidencia"],
                "tipo": "cierre",
                "solucion": solucion,
                "api_status": "OK"
            })
        except Exception as e:
            estado_api["gestor_incidencias"] = f"error: {str(e)}"
            resolution_logger.error("Error cerrando incidencia", extra_data={
                "action": "close_incident_error",
                "codIncidencia": incidencia["codIncidencia"],
                "error": str(e),
                "error_type": type(e).__name__,
                "api_status": f"error: {str(e)}"
            })
        resolution["estado_api"] = estado_api
        return resolution
    
    elif resolution_type == "en espera":
        resolution_logger.debug("Intentando poner incidencia en espera", extra_data={
            "action": "wait_incident_attempt",
            "codIncidencia": incidencia["codIncidencia"],
            "solucion": solucion
        })
        
        try:
            patch_incidencia(
                incidencia["codIncidencia"],
                "en_espera",
                detalle=solucion
            )
            estado_api["gestor_incidencias"] = "OK"
            resolution_logger.info("Incidencia puesta en espera exitosamente", extra_data={
                "action": "incident_wait_success",
                "codIncidencia": incidencia["codIncidencia"],
                "tipo": "en espera",
                "solucion": solucion,
                "api_status": "OK"
            })
        except Exception as e:
            estado_api["gestor_incidencias"] = f"error: {str(e)}"
            resolution_logger.error("Error poniendo incidencia en espera", extra_data={
                "action": "wait_incident_error",
                "codIncidencia": incidencia["codIncidencia"],
                "error": str(e),
                "error_type": type(e).__name__,
                "api_status": f"error: {str(e)}"
            })
        resolution["estado_api"] = estado_api
        return resolution
    
    elif resolution_type == "reasignacion":
        resolution_logger.debug("Intentando reasignar incidencia", extra_data={
            "action": "reassign_incident_attempt",
            "codIncidencia": incidencia["codIncidencia"],
            "buzon_reasignacion": buzon_reasignacion,
            "solucion": solucion
        })
        
        try:
            patch_incidencia(
                incidencia["codIncidencia"],
                "reasignar",
                buzonDestino=buzon_reasignacion,
                detalle=solucion
            )
            estado_api["gestor_incidencias"] = "OK"
            resolution_logger.info("Incidencia reasignada exitosamente", extra_data={
                "action": "incident_reassigned_success",
                "codIncidencia": incidencia["codIncidencia"],
                "tipo": "reasignacion",
                "buzon_reasignacion": buzon_reasignacion,
                "solucion": solucion,
                "api_status": "OK"
            })
        except Exception as e:
            estado_api["gestor_incidencias"] = f"error: {str(e)}"
            resolution_logger.error("Error reasignando incidencia", extra_data={
                "action": "reassign_incident_error",
                "codIncidencia": incidencia["codIncidencia"],
                "error": str(e),
                "error_type": type(e).__name__,
                "api_status": f"error: {str(e)}"
            })
        resolution["estado_api"] = estado_api
        return resolution
    
    elif resolution_type.startswith("api|"):
        # Extract solution code
        cod_solucion = resolution_type.split("|")[1]
        
        resolution_logger.debug("Procesando resolución API", extra_data={
            "action": "api_resolution_processing",
            "codIncidencia": incidencia["codIncidencia"],
            "resolution_type": resolution_type,
            "cod_solucion": cod_solucion,
            "keywords_available": list(keywords.keys())
        })
        
        # Get policy data from metadata
        poliza = str(keywords.get("poliza"))
        if not poliza:
            resolution_logger.debug("No se encontró póliza, solicitando manualmente", extra_data={
                "action": "no_poliza_fallback",
                "codIncidencia": incidencia["codIncidencia"],
                "keywords": list(keywords.keys()),
                "missing_poliza": True
            })
            new_resolution = {
                "metadata": {
                    "RESOLUCION AUTOMÁTICA": "en espera",
                    "BUZON REASIGNACION": "",
                    "SOLUCIÓN": "Por favor, ingrese la poliza para poder continuar con la resolución",
                    "estado_api": estado_api
                }
            }
            return process_resolution(new_resolution, incidencia, keywords)
        
        resolution_logger.debug("Póliza encontrada, llamando al sistema", extra_data={
            "action": "poliza_found_api_call",
            "codIncidencia": incidencia["codIncidencia"],
            "poliza": poliza,
            "cod_solucion": cod_solucion,
            "keywords_json": str(keywords)
        })
        
        # Call policy check API
        try:
            response = comprobacion_poliza(
                poliza=poliza,
                codSolucion=cod_solucion,
                strJson=str(keywords)
            )
            estado_api["sistema"] = "ok"
            resolution_logger.info("Llamada al sistema exitosa", extra_data={
                "action": "system_api_success",
                "codIncidencia": incidencia["codIncidencia"],
                "poliza": poliza,
                "cod_solucion": cod_solucion,
                "response_type": type(response).__name__,
                "api_status": "ok"
            })
        except Exception as e:
            estado_api["sistema"] = f"error: {str(e)}"
            resolution_logger.error("Error en llamada al sistema", extra_data={
                "action": "system_api_error",
                "codIncidencia": incidencia["codIncidencia"],
                "poliza": poliza,
                "cod_solucion": cod_solucion,
                "error": str(e),
                "error_type": type(e).__name__,
                "api_status": f"error: {str(e)}"
            })
            response = {
                "metadata": {
                    "RESOLUCION AUTOMÁTICA": "manual",
                    "BUZON REASIGNACION": "",
                    "SOLUCIÓN": f"[resolution_type] Error al llamar al sistema: {str(e)}",
                    "estado_api": estado_api
                }
            }
        
        resolution_logger.debug("Procesando respuesta del sistema recursivamente", extra_data={
            "action": "recursive_response_processing",
            "codIncidencia": incidencia["codIncidencia"],
            "response_type": type(response).__name__,
            "response_keys": list(response.keys()) if isinstance(response, dict) else []
        })
        
        # Process the response recursively
        return process_resolution(response, incidencia, keywords)
    
    # Default to manual resolution
    resolution_logger.debug("Tipo de resolución no reconocido, usando manual por defecto", extra_data={
        "action": "unknown_resolution_type_fallback",
        "codIncidencia": incidencia["codIncidencia"],
        "resolution_type": resolution_type,
        "fallback_to": "manual"
    })
    
    resolution["metadata"]["RESOLUCION AUTOMÁTICA"] = "manual"
    resolution["estado_api"] = estado_api
    return resolution