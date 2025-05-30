import os
import requests
from typing import Dict, Any

BASE_URL = os.getenv("MOCK_SISTEMA_URL", "http://localhost:3001")

def get_poliza(numero_poliza: str) -> Dict[str, Any]:
    """Get policy information."""
    response = requests.get(f"{BASE_URL}/api/poliza/{numero_poliza}")
    response.raise_for_status()
    return response.json()

def comprobacion_poliza(
    poliza: str,
    cod_solucion: str,
    str_json: str
) -> Dict[str, Any]:
    """Check policy status and get resolution."""
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