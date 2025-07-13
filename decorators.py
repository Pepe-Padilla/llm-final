"""Decoradores para manejo consistente de errores y logging."""

import functools
from typing import Any, Callable
from observabilidad.logger import main_logger


def handle_api_errors(operation_name: str = "API_CALL", fallback_value: Any = None):
    """Decorador para manejo consistente de errores en llamadas API."""
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                main_logger.info(f"✅ {operation_name} exitosa", extra_data={
                    "action": f"{operation_name.lower()}_success",
                    "function": func.__name__
                })
                return result
            except Exception as e:
                main_logger.error(f"❌ Error en {operation_name}", extra_data={
                    "action": f"{operation_name.lower()}_error", 
                    "function": func.__name__,
                    "error": str(e),
                    "error_type": type(e).__name__
                })
                return fallback_value
        return wrapper
    return decorator


def log_execution_time(operation_name: str = "OPERATION"):
    """Decorador para medir y registrar tiempo de ejecución."""
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import time
            start_time = time.time()
            
            result = func(*args, **kwargs)
            
            execution_time = time.time() - start_time
            main_logger.info(f"⏱️ {operation_name} completada", extra_data={
                "action": f"{operation_name.lower()}_timing",
                "function": func.__name__,
                "execution_time_seconds": round(execution_time, 2)
            })
            return result
        return wrapper
    return decorator


def log_function_call(include_args: bool = False):
    """Decorador para registrar llamadas a funciones importantes."""
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            extra_data = {
                "action": f"{func.__name__}_called",
                "function": func.__name__
            }
            
            if include_args and args:
                # Solo incluir argumentos no sensibles
                safe_args = []
                for arg in args[:3]:  # Máximo 3 argumentos
                    if isinstance(arg, (str, int, float, bool)):
                        safe_args.append(str(arg)[:100])  # Limitar longitud
                    else:
                        safe_args.append(type(arg).__name__)
                extra_data["args_preview"] = safe_args
            
            main_logger.debug(f"🔄 Ejecutando {func.__name__}", extra_data=extra_data)
            return func(*args, **kwargs)
        return wrapper
    return decorator 