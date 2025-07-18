"""API para sistema de gestión."""
import requests
from typing import Dict, Any
from config import MOCK_SISTEMA_URL

BASE_URL = MOCK_SISTEMA_URL

def get_poliza(numero_poliza: str) -> Dict[str, Any]:
    """Get policy information."""
    response = requests.get(f"{BASE_URL}/api/poliza/{numero_poliza}")
    response.raise_for_status()
    return response.json()

def comprobacion_poliza(
    poliza: str,
    cod_solucion: str = None,
    str_json: str = None,
    **kwargs
) -> Dict[str, Any]:
    """Check policy status and get resolution."""
    # Flexible parameter handling
    cod_solucion = cod_solucion or kwargs.get('codSolucion', '')
    str_json = str_json or kwargs.get('strJson', '')
    
    data = {
        "poliza": poliza,
        "codSolucion": cod_solucion,
        "strJson": str_json
    }
    
    response = requests.post(
        f"{BASE_URL}/api/comprobacionPoliza",
        json=data
    )
    response.raise_for_status()
    return response.json() 