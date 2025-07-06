import logging
import requests
import json
from datetime import datetime
from typing import Dict, Any

class LokiLogger:
    """
    Logger que envía logs a Loki y también los imprime en pantalla.
    """
    
    def __init__(self, service_name: str, loki_url: str = "http://localhost:3100"):
        self.service_name = service_name
        self.loki_url = loki_url
        
        # Configurar logging básico
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(service_name)
    
    def _send_to_loki(self, level: str, message: str, extra_data: Dict[str, Any] = None):
        """
        Envía log a Loki.
        """
        try:
            timestamp_ns = int(datetime.now().timestamp() * 1e9)
            
            # Preparar datos para Loki
            log_entry = {
                "streams": [{
                    "stream": {
                        "service": self.service_name,
                        "level": level
                    },
                    "values": [
                        [str(timestamp_ns), json.dumps({
                            "message": message,
                            "extra": extra_data or {}
                        })]
                    ]
                }]
            }
            
            # Enviar a Loki
            response = requests.post(
                f"{self.loki_url}/loki/api/v1/push",
                json=log_entry,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code != 204:
                print(f"Error enviando log a Loki: {response.status_code}")
                
        except Exception as e:
            print(f"Error en LokiLogger: {e}")
    
    def info(self, message: str, extra_data: Dict[str, Any] = None):
        """Log de información."""
        self.logger.info(message)
        print(f"[INFO] {message}")
        self._send_to_loki("INFO", message, extra_data)
    
    def error(self, message: str, extra_data: Dict[str, Any] = None):
        """Log de error."""
        self.logger.error(message)
        print(f"[ERROR] {message} | extra: {json.dumps(extra_data, ensure_ascii=False)}")
        self._send_to_loki("ERROR", message, extra_data)
    
    def warning(self, message: str, extra_data: Dict[str, Any] = None):
        """Log de advertencia."""
        self.logger.warning(message)
        print(f"[WARNING] {message} | extra: {json.dumps(extra_data, ensure_ascii=False)}")
        self._send_to_loki("WARNING", message, extra_data)
    
    def debug(self, message: str, extra_data: Dict[str, Any] = None):
        """Log de debug."""
        self.logger.debug(message)
        self._send_to_loki("DEBUG", message, extra_data)

# Instancia global para usar en todo el proyecto
main_logger = LokiLogger("main")
batch_logger = LokiLogger("batch")
resolution_logger = LokiLogger("resolution") 