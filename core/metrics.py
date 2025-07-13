"""Sistema simple de métricas y monitoreo."""

import time
from datetime import datetime
from typing import Dict, Any
from collections import defaultdict, Counter
from observabilidad.logger import main_logger
from config import CRITIC_APPROVAL_THRESHOLD


class SystemMetrics:
    """Métricas del sistema de resolución automática."""
    
    def __init__(self):
        self.reset_metrics()
    
    def reset_metrics(self):
        """Reinicia todas las métricas."""
        self.start_time = time.time()
        self.incident_times = []
        self.resolution_types = Counter()
        self.problem_types = Counter()
        self.api_errors = defaultdict(int)
        self.critic_rejections = 0
        self.critic_approvals = 0
        self.solutions_found_per_incident = []
        self.processing_errors = []
    
    def record_incident_start(self, incident_code: str):
        """Registra el inicio del procesamiento de una incidencia."""
        self._current_incident = {
            "code": incident_code,
            "start_time": time.time()
        }
    
    def record_incident_end(self, resolution_type: str):
        """Registra el fin del procesamiento de una incidencia."""
        if hasattr(self, '_current_incident'):
            processing_time = time.time() - self._current_incident["start_time"]
            self.incident_times.append(processing_time)
            self.resolution_types[resolution_type] += 1
    
    def record_solutions_found(self, count: int):
        """Registra el número de soluciones encontradas."""
        self.solutions_found_per_incident.append(count)
    
    def record_problem_type(self, problem_type: str):
        """Registra el tipo de problema identificado por el crítico."""
        if problem_type and problem_type != "unknown":
            self.problem_types[problem_type] += 1
    
    def record_critic_decision(self, status: str):
        """Registra la decisión del crítico."""
        if status == "APPROVED":
            self.critic_approvals += 1
        elif status == "REJECTED":
            self.critic_rejections += 1
    
    def record_api_error(self, api_name: str):
        """Registra un error de API."""
        self.api_errors[api_name] += 1
    
    def record_processing_error(self, error: str, incident_code: str = "unknown"):
        """Registra un error de procesamiento."""
        self.processing_errors.append({
            "timestamp": datetime.now().isoformat(),
            "incident_code": incident_code,
            "error": str(error)
        })
    
    def get_summary(self) -> Dict[str, Any]:
        """Obtiene resumen de métricas."""
        total_time = time.time() - self.start_time
        total_incidents = len(self.incident_times)
        
        summary = {
            "execution_summary": {
                "total_time_seconds": round(total_time, 2),
                "total_incidents": total_incidents,
                "avg_time_per_incident": round(sum(self.incident_times) / len(self.incident_times), 2) if self.incident_times else 0,
                "incidents_per_minute": round((total_incidents / total_time) * 60, 2) if total_time > 0 else 0
            },
            "resolution_distribution": dict(self.resolution_types),
            "problem_type_distribution": dict(self.problem_types),
            "critic_performance": {
                "total_evaluations": self.critic_approvals + self.critic_rejections,
                "approvals": self.critic_approvals,
                "rejections": self.critic_rejections,
                "approval_rate": round(self.critic_approvals / (self.critic_approvals + self.critic_rejections) * 100, 2) if (self.critic_approvals + self.critic_rejections) > 0 else 0
            },
            "solution_effectiveness": {
                "avg_solutions_per_incident": round(sum(self.solutions_found_per_incident) / len(self.solutions_found_per_incident), 2) if self.solutions_found_per_incident else 0,
                "incidents_with_solutions": len([x for x in self.solutions_found_per_incident if x > 0]),
                "incidents_without_solutions": len([x for x in self.solutions_found_per_incident if x == 0])
            },
            "error_summary": {
                "api_errors": dict(self.api_errors),
                "processing_errors": len(self.processing_errors),
                "error_rate": round(len(self.processing_errors) / total_incidents * 100, 2) if total_incidents > 0 else 0
            }
        }
        
        return summary
    
    def log_final_metrics(self):
        """Registra las métricas finales en el log."""
        summary = self.get_summary()
        
        main_logger.info("📊 MÉTRICAS FINALES DEL SISTEMA", extra_data={
            "action": "final_metrics",
            **summary
        })
        
        # Log de insights específicos
        if summary["critic_performance"]["approval_rate"] < CRITIC_APPROVAL_THRESHOLD:
            rejection_rate = 100 - summary["critic_performance"]["approval_rate"]
            main_logger.warning("⚠️ Alta tasa de rechazo del crítico", extra_data={
                "action": "high_rejection_rate_warning",
                "rejection_rate": rejection_rate,
                "approval_rate": summary["critic_performance"]["approval_rate"],
                "summary": summary
            })
        
        if summary["solution_effectiveness"]["incidents_without_solutions"] > summary["solution_effectiveness"]["incidents_with_solutions"]:
            main_logger.warning("⚠️ Muchas incidencias sin soluciones en catálogo", extra_data={
                "action": "low_solution_coverage_warning",
                "without_solutions": summary["solution_effectiveness"]["incidents_without_solutions"],
                "with_solutions": summary["solution_effectiveness"]["incidents_with_solutions"],
                "summary": summary
            })


# Instancia global de métricas
system_metrics = SystemMetrics() 