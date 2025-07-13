import json
import re
from typing import Dict, Any, Union
from observabilidad.logger import main_logger


def markdownJson(response: str) -> str:
    """Extrae JSON de respuestas con markdown."""
    match = re.search(r"```(?:[a-zA-Z]+\n)?(.*?)```", response, re.DOTALL)
    if match:
        return match.group(1).strip()
    return response.strip()


def convert_json_response(response: str, section: str = "unknown") -> Dict[str, Any]:
    """Convierte respuesta string a JSON."""
    try:
        cleaned_response = markdownJson(response)
        json_response = json.loads(cleaned_response)
        
        main_logger.debug(f"{section} convertido exitosamente", extra_data={
            "action": f"{section}_converted_success",
            "response_type": type(json_response).__name__
        })
        return json_response
    except Exception as e:
        main_logger.error(f"Error convirtiendo JSON en {section}", extra_data={
            "action": f"{section}_conversion_error",
            "response": response,
            "error": str(e)
        })
        return {}

def evalNullNone(response: str) -> str:
    """Evalúa la respuesta y reemplaza None por 'null'."""
    return response.replace("null", "None")


def convert_eval_response(response: str, section: str = "unknown") -> Dict[str, Any]:
    """Convierte respuesta usando eval o JSON según el formato."""
    cleaned_response = markdownJson(response)
    cleaned_response = evalNullNone(cleaned_response)
    try:
        return eval(cleaned_response)
    except Exception as e2:
        try:
            return convert_json_response(response, section)
        except Exception as e:
            main_logger.error(f"Error convirtiendo respuesta en {section}", extra_data={
                "action": f"{section}_conversion_error",
                "response": response,
                "error": str(e),
                "error2": str(e2)

            })
            return {}


def simple_json_parse(response: str, logger=None) -> Union[Dict[str, Any], None]:
    """Parser JSON simple para respuestas LLM."""
    try:
        return json.loads(response)
    except:
        try:
            cleaned_response = markdownJson(response)
            return json.loads(cleaned_response)
        except:
            if logger:
                logger.warning(f"Error parseando JSON: {response[:100]}...")
            return None 