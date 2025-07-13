"""Módulo del Crítico - Validación de resoluciones con LLM Crítico."""

import os
import csv
from datetime import datetime
from typing import List, Dict, Any
from llm.LLMCritic import evaluate_resolution
from llm.LLMResolution import get_resolution
from observabilidad.logger import main_logger
from core.utils import convert_json_response, convert_eval_response
from core.metrics import system_metrics
from config import MAX_RETRIES_CRITIC

def log_rejected_resolution(incident_code: str, critic_evaluation: Dict[str, Any], resolution: Dict[str, Any]):
    """Registra resolución rechazada en CSV para análisis."""
    try:
        rejected_dir = "./resources/rejected"
        os.makedirs(rejected_dir, exist_ok=True)
        
        today = datetime.now().strftime("%Y%m%d")
        csv_file = f"{rejected_dir}/rejected{today}.csv"
        file_exists = os.path.exists(csv_file)
        
        row_data = {
            "timestamp": datetime.now().isoformat(),
            "codigo_incidencia": incident_code,
            "motivo_rechazo": critic_evaluation.get("reason", ""),
            "critica_completa": critic_evaluation.get("critique", ""),
            "tipo_problema": critic_evaluation.get("problem_type", ""),
            "evitar_soluciones": str(critic_evaluation.get("avoid_solution_types", [])),
            "enfoque_recomendado": critic_evaluation.get("recommended_approach", ""),
            "resolucion_tipo": resolution.get("metadata", {}).get("RESOLUCION AUTOMÁTICA", ""),
            "resolucion_buzon": resolution.get("metadata", {}).get("BUZON REASIGNACION", ""),
            "resolucion_solucion": resolution.get("metadata", {}).get("SOLUCIÓN", ""),
            "resolucion_completa": str(resolution)
        }
        
        with open(csv_file, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=row_data.keys())
            if not file_exists:
                writer.writeheader()
            writer.writerow(row_data)
            
    except Exception as e:
        main_logger.error(f"Error registrando rechazo en CSV: {str(e)}", extra_data={
            "action": "rejection_csv_error",
            "error": str(e),
            "incident_code": incident_code
        })

def process_resolution_with_critic(enhanced_incidencia: Dict[str, Any], all_relevant_solutions: List[Dict[str, Any]], 
                                   max_retries: int = MAX_RETRIES_CRITIC) -> Dict[str, Any]:
    """Procesa resolución con validación del LLM Crítico."""
    
    incident_code = enhanced_incidencia.get("codIncidencia", "unknown")
    
    main_logger.info("Iniciando proceso de resolución con crítico", extra_data={
        "action": "start_critic_process",
        "codIncidencia": incident_code,
        "solutions_count": len(all_relevant_solutions)
    })
    
    # Sin soluciones → manual directo
    if not all_relevant_solutions:
        main_logger.warning("⚠️ No hay soluciones disponibles en el catálogo", extra_data={
            "action": "no_solutions_warning",
            "codIncidencia": incident_code
        })
        return {
            "metadata": {
                "RESOLUCION AUTOMÁTICA": "manual",
                "BUZON REASIGNACION": "",
                "SOLUCIÓN": "No hay soluciones disponibles en el catálogo para esta incidencia, revisar manualmente"
            }
        }
    
    critique_context = ""
    rejected_solutions = []
    structured_critique = {}
    
    for attempt in range(max_retries + 1):
        main_logger.info(f"Intento {attempt + 1}/{max_retries + 1}", extra_data={
            "action": "critic_attempt",
            "attempt": attempt + 1,
            "codIncidencia": incident_code
        })
        
        # Filtrar soluciones rechazadas
        available_solutions = [sol for sol in all_relevant_solutions if sol not in rejected_solutions]
        
        # Sin soluciones después del filtro → manual
        if not available_solutions:
            main_logger.warning("⚠️ No hay soluciones disponibles después del filtro", extra_data={
                "action": "no_solutions_after_filter_warning",
                "codIncidencia": incident_code,
                "rejected_count": len(rejected_solutions)
            })
            return {
                "metadata": {
                    "RESOLUCION AUTOMÁTICA": "manual",
                    "BUZON REASIGNACION": "",
                    "SOLUCIÓN": f"No hay soluciones disponibles después de filtrar {len(rejected_solutions)} soluciones rechazadas, revisar manualmente"
                }
            }
        
        # Generar resolución con contexto de crítica
        context_incident = enhanced_incidencia.copy()
        if critique_context and structured_critique:
            context_incident["critique_context"] = critique_context
            context_incident["structured_critique"] = structured_critique
        
        resolution_response = get_resolution(context_incident, available_solutions)
        resolution = convert_eval_response(resolution_response, "resolution")
        
        if isinstance(resolution, list):
            resolution = resolution[0]
        
        # Evaluar con crítico
        critic_response = evaluate_resolution(enhanced_incidencia, resolution)
        critic_evaluation = convert_json_response(critic_response, "critic")
        status = critic_evaluation.get("status", "APPROVED")
        
        # Registrar decisión del crítico en métricas
        system_metrics.record_critic_decision(status)
        
        # Registrar tipo de problema si está disponible
        problem_type = critic_evaluation.get("problem_type", "unknown")
        system_metrics.record_problem_type(problem_type)
        
        if status == "APPROVED":
            main_logger.info("✅ Resolución aprobada por el crítico", extra_data={
                "action": "resolution_approved",
                "attempt": attempt + 1,
                "codIncidencia": incident_code,
                "problem_type": problem_type
            })
            return resolution
        
        elif status == "ALREADY_TRIED":
            main_logger.warning("⚠️ Resolución ya intentada anteriormente", extra_data={
                "action": "already_tried_warning",
                "codIncidencia": incident_code,
                "reason": critic_evaluation.get("reason", "")
            })
            return {
                "metadata": {
                    "RESOLUCION AUTOMÁTICA": "manual",
                    "BUZON REASIGNACION": "",
                    "SOLUCIÓN": f"La solución propuesta ya fue intentada anteriormente. {critic_evaluation.get('reason', '')}"
                }
            }
        
        elif status == "REJECTED":
            rejected_solutions.append(resolution)
            
            # Log warning con información completa
            main_logger.warning("⚠️ RESOLUCIÓN RECHAZADA POR CRÍTICO", extra_data={
                "action": "resolution_rejected_by_critic",
                "codIncidencia": incident_code,
                "attempt": attempt + 1,
                "motivo_rechazo": critic_evaluation.get("reason", ""),
                "tipo_problema": problem_type,
                "enfoque_recomendado": critic_evaluation.get("recommended_approach", "")
            })
            
            # Registrar en CSV
            log_rejected_resolution(incident_code, critic_evaluation, resolution)
            
            # Actualizar información estructurada
            structured_critique = {
                "problem_type": problem_type,
                "avoid_solution_types": critic_evaluation.get("avoid_solution_types", []),
                "recommended_approach": critic_evaluation.get("recommended_approach", "")
            }
            
            if attempt < max_retries:
                critique_context = critic_evaluation.get("critique", "")
                continue
            else:
                main_logger.info("Máximo de reintentos alcanzado", extra_data={
                    "action": "max_retries_reached",
                    "codIncidencia": incident_code,
                    "total_rejected": len(rejected_solutions)
                })
                return {
                    "metadata": {
                        "RESOLUCION AUTOMÁTICA": "manual",
                        "BUZON REASIGNACION": "",
                        "SOLUCIÓN": f"No se pudo generar una resolución automática adecuada después de {max_retries + 1} intentos. {len(rejected_solutions)} soluciones rechazadas. Última crítica: {critic_evaluation.get('critique', '')}"
                    }
                }
    
    # Fallback
    return {
        "metadata": {
            "RESOLUCION AUTOMÁTICA": "manual",
            "BUZON REASIGNACION": "",
            "SOLUCIÓN": "Error en el proceso de resolución con crítico, revisar manualmente"
        }
    } 