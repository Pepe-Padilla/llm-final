import os
import requests
from typing import Dict, Any, List
from datetime import datetime, timedelta

BASE_URL = os.getenv("MOCK_GESTOR_URL", "http://localhost:3000")

def get_incidencias(buzon: str = "GR_SAL_COMP_AUTORIZACIONES") -> List[Dict[str, Any]]:
    """Get open incidents. If buzon is provided, filter by that mailbox."""
    params = {}
    if buzon:
        params["buzon"] = buzon
    
    response = requests.get(f"{BASE_URL}/api/incidencias", params=params)
    response.raise_for_status()
    return response.json()

def get_incidencias_cerradas(buzon: str = "GR_SAL_COMP_AUTORIZACIONES", meses: int = 2) -> List[Dict[str, Any]]:
    """Get closed incidents. For mock, returns all closed incidents regardless of date."""
    response = requests.get(f"{BASE_URL}/api/incidencias/cerradas")
    response.raise_for_status()
    incidencias_cerradas = response.json()
    
    # Filter by buzon if provided
    if buzon:
        incidencias_cerradas = [inc for inc in incidencias_cerradas if inc["buzon"] == buzon]
    
    # For mock environment, return all incidents (no date filtering)
    return incidencias_cerradas

def patch_incidencia(
    cod_incidencia: str,
    action: str,
    buzon_destino: str = None,
    notas_resolucion: str = None,
    detalle: str = None,
    **kwargs
) -> Dict[str, Any]:
    """Update an incident with a specific action."""
    # Flexible parameter handling
    buzon_destino = buzon_destino or kwargs.get('buzonDestino', None)
    notas_resolucion = notas_resolucion or kwargs.get('notasResolucion', None)
    detalle = detalle or kwargs.get('detalle', None)
    
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