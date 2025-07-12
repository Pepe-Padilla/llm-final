import json
import re
from typing import Dict, Any, Union
from observabilidad.logger import main_logger


def markdownJson(response: str) -> str:
    """
    Convierte una respuesta de un LLM, si tiene acotadores de código markdown se los quita
    
    Args:
        response: String con la respuesta de un LLM y si la respuesta está entre indicadores de código markdown
            los elimina
            
    Returns:
        String sin backquotes de markdown
    """
    match = re.search(r"```(?:[a-zA-Z]+\n)?(.*?)```", response, re.DOTALL)
    if match:
        return match.group(1).strip()
    return response.strip()


def convert_json_response(response: str, section: str = "unknown") -> Dict[str, Any]:
    """
    Convierte la respuesta string a json
    
    Args:
        response: String raw de la respuesta del LLM
        section: String de la sección para controlar el log
        
    Returns:
        Dict con la respuesta
    """
    try:
        cleaned_response = markdownJson(response)
        json_response = json.loads(cleaned_response)
        
        main_logger.debug(f"{section} response convertidas exitosamente", extra_data={
            "action": f"{section}_converted_success",
            "response": json_response,
            "keys": list(json_response.keys()) if hasattr(json_response, 'keys') else [],
            "response_type": type(json_response).__name__
        })
        return json_response
    except Exception as e:
        main_logger.error("Error convert_json_response", extra_data={
            "action": f"{section}_conversion_error",
            "error": str(e),
            "error_type": type(e).__name__,
            "raw_response": response
        })
        
        # Fallback to empty dict
        return {}


def convert_eval_response(response: str, section: str = "unknown") -> Dict[str, Any]:
    """
    Convierte la respuesta string a python object por donde se deje el eval o json.loads
    
    Args:
        response: String raw de la respuesta del LLM
        section: String de la sección para controlar el log
        
    Returns:
        Dict con la respuesta
    """
    cleaned_response = markdownJson(response)
    try:
        resp = eval(cleaned_response)
        return resp
    except Exception as e:
        try:
            resp = convert_json_response(response, section)
            return resp
        except Exception as e2:
            main_logger.error("Error convert_eval_response", extra_data={
                "action": f"{section}_conversion_error",
                "error1": str(e),
                "error2": str(e2),
                "error_type": type(e).__name__,
                "error_type2": type(e2).__name__,
                "raw_response": response
            })
            return {}


def simple_json_parse(response: str, logger=None) -> Union[Dict[str, Any], None]:
    """
    Simple JSON parser for LLM responses - returns None if fails
    
    Args:
        response: String con la respuesta del LLM
        logger: Logger opcional para warnings
        
    Returns:
        Dict con la respuesta o None si falla
    """
    try:
        # Try to parse as JSON directly
        return json.loads(response)
    except:
        try:
            # Try to extract JSON from markdown code blocks
            cleaned_response = markdownJson(response)
            return json.loads(cleaned_response)
        except:
            pass
        
        # If all fails, return None (will be handled by caller)
        if logger:
            logger.warning(f"Failed to parse JSON response: {response[:100]}...")
        return None 