import os
import requests
from typing import Dict, Any, List

BASE_URL = os.getenv("MOCK_GESTOR_URL", "http://localhost:3000")

def get_incidencias(buzon: str = "GR_SAL_COMP_AUTORIZACIONES") -> List[Dict[str, Any]]:
    """Get open incidents for a specific mailbox."""
    response = requests.get(f"{BASE_URL}/api/incidencias", params={"buzon": buzon})
    response.raise_for_status()
    return response.json()

def patch_incidencia(
    cod_incidencia: str,
    action: str,
    buzon_destino: str = None,
    notas_resolucion: str = None,
    detalle: str = None
) -> Dict[str, Any]:
    """Update an incident with a specific action."""
    data = {"action": action}
    
    if buzon_destino:
        data["buzonDestino"] = buzon_destino
    if notas_resolucion:
        data["notasResolucion"] = notas_resolucion
    if detalle:
        data["detalle"] = detalle
    
    print(f"Sending request to {BASE_URL}/api/incidencias/{cod_incidencia}")
    print(f"With data: {data}")
    
    response = requests.patch(
        f"{BASE_URL}/api/incidencias/{cod_incidencia}",
        json=data
    )
    response.raise_for_status()
    return response.json() 