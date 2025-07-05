#!/usr/bin/env python3
"""
Script para iniciar el servidor MLflow para el proyecto de fine-tuning de imagen a texto.
"""

import subprocess
import sys
import time
import requests
from pathlib import Path

def check_mlflow_installed():
    """Verifica si MLflow está instalado"""
    try:
        import mlflow
        print("✓ MLflow está instalado")
        return True
    except ImportError:
        print("✗ MLflow no está instalado. Instalando...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "mlflow"])
            print("✓ MLflow instalado exitosamente")
            return True
        except subprocess.CalledProcessError:
            print("✗ Error al instalar MLflow")
            return False

def start_mlflow_server(host="0.0.0.0", port=5000):
    """Inicia el servidor MLflow"""
    print(f"Iniciando servidor MLflow en http://{host}:{port}")
    
    try:
        # Comando para iniciar MLflow
        cmd = [
            sys.executable, "-m", "mlflow", "server",
            "--host", host,
            "--port", str(port),
            "--backend-store-uri", "./mlflow_data"
        ]
        
        print(f"Ejecutando: {' '.join(cmd)}")
        
        # Iniciar el servidor en segundo plano
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Esperar un momento para que el servidor se inicie
        time.sleep(3)
        
        # Verificar si el servidor está funcionando
        try:
            response = requests.get(f"http://{host}:{port}/health", timeout=5)
            if response.status_code == 200:
                print("✓ Servidor MLflow iniciado exitosamente")
                print(f"  URL: http://{host}:{port}")
                print("  Presiona Ctrl+C para detener el servidor")
                
                # Mantener el script ejecutándose
                try:
                    process.wait()
                except KeyboardInterrupt:
                    print("\nDeteniendo servidor MLflow...")
                    process.terminate()
                    process.wait()
                    print("✓ Servidor detenido")
            else:
                print(f"✗ Error: Servidor respondió con código {response.status_code}")
                process.terminate()
                
        except requests.exceptions.RequestException as e:
            print(f"✗ Error conectando al servidor: {e}")
            process.terminate()
            
    except Exception as e:
        print(f"✗ Error iniciando servidor MLflow: {e}")

def main():
    """Función principal"""
    print("=== Iniciador de Servidor MLflow ===")
    print()
    
    # Verificar instalación de MLflow
    if not check_mlflow_installed():
        print("No se pudo instalar MLflow. Saliendo...")
        sys.exit(1)
    
    print()
    
    # Crear directorio para datos de MLflow si no existe
    mlflow_data_dir = Path("./mlflow_data")
    mlflow_data_dir.mkdir(exist_ok=True)
    print(f"✓ Directorio de datos MLflow: {mlflow_data_dir.absolute()}")
    
    print()
    
    # Iniciar servidor
    start_mlflow_server()

if __name__ == "__main__":
    main() 