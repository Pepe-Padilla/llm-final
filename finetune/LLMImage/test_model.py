#!/usr/bin/env python3
"""
Script para probar el modelo de imagen a texto entrenado desde MLflow.
"""

import os
import sys
import argparse
from PIL import Image
import torch
import mlflow.pytorch
from transformers import ViTImageProcessor, AutoTokenizer

def load_model_from_mlflow(model_name="image-to-text-finetuned", version="latest"):
    """
    Carga el modelo entrenado desde MLflow
    
    Args:
        model_name (str): Nombre del modelo en MLflow
        version (str): Versión del modelo ('latest' o número específico)
    
    Returns:
        tuple: (model, feature_extractor, tokenizer)
    """
    try:
        print(f"Cargando modelo {model_name} versión {version} desde MLflow...")
        
        # Cargar modelo
        model_uri = f"models:/{model_name}/{version}"
        model = mlflow.pytorch.load_model(model_uri)
        
        # Cargar feature extractor y tokenizer desde el directorio local
        if os.path.exists("./results/feature_extractor"):
            feature_extractor = ViTImageProcessor.from_pretrained("./results/feature_extractor")
        else:
            print("⚠️  Feature extractor no encontrado en ./results/, usando el del modelo base")
            feature_extractor = ViTImageProcessor.from_pretrained("nlpconnect/vit-gpt2-image-captioning")
        
        if os.path.exists("./results/tokenizer"):
            tokenizer = AutoTokenizer.from_pretrained("./results/tokenizer")
        else:
            print("⚠️  Tokenizer no encontrado en ./results/, usando el del modelo base")
            tokenizer = AutoTokenizer.from_pretrained("nlpconnect/vit-gpt2-image-captioning")
        
        # Configurar tokenizer
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        
        print("✓ Modelo cargado exitosamente")
        return model, feature_extractor, tokenizer
        
    except Exception as e:
        print(f"✗ Error cargando modelo: {e}")
        return None, None, None

def generate_caption(model, feature_extractor, tokenizer, image_path, max_length=50):
    """
    Genera una descripción para una imagen
    
    Args:
        model: Modelo de imagen a texto
        feature_extractor: Procesador de características de imagen
        tokenizer: Tokenizer para el texto
        image_path (str): Ruta a la imagen
        max_length (int): Longitud máxima de la descripción
    
    Returns:
        str: Descripción generada
    """
    try:
        # Cargar y procesar imagen
        image = Image.open(image_path).convert('RGB')
        pixel_values = feature_extractor(image, return_tensors="pt").pixel_values
        
        # Generar descripción
        with torch.no_grad():
            output_ids = model.generate(
                pixel_values,
                max_length=max_length,
                num_beams=4,
                return_dict_in_generate=True
            ).sequences
        
        # Decodificar resultado
        preds = tokenizer.batch_decode(output_ids, skip_special_tokens=True)
        preds = [pred.strip() for pred in preds]
        
        return preds[0]
        
    except Exception as e:
        print(f"✗ Error generando descripción: {e}")
        return None

def test_single_image(image_path, model_name="image-to-text-finetuned", version="latest"):
    """
    Prueba el modelo con una imagen específica
    
    Args:
        image_path (str): Ruta a la imagen
        model_name (str): Nombre del modelo en MLflow
        version (str): Versión del modelo
    """
    # Cargar modelo
    model, feature_extractor, tokenizer = load_model_from_mlflow(model_name, version)
    
    if model is None:
        print("No se pudo cargar el modelo. Saliendo...")
        return
    
    # Verificar que la imagen existe
    if not os.path.exists(image_path):
        print(f"✗ La imagen {image_path} no existe")
        return
    
    # Generar descripción
    print(f"\nProcesando imagen: {image_path}")
    caption = generate_caption(model, feature_extractor, tokenizer, image_path)
    
    if caption:
        print(f"Descripción generada: {caption}")
    else:
        print("No se pudo generar una descripción")

def test_multiple_images(images_dir, model_name="image-to-text-finetuned", version="latest"):
    """
    Prueba el modelo con múltiples imágenes de un directorio
    
    Args:
        images_dir (str): Directorio con las imágenes
        model_name (str): Nombre del modelo en MLflow
        version (str): Versión del modelo
    """
    # Cargar modelo
    model, feature_extractor, tokenizer = load_model_from_mlflow(model_name, version)
    
    if model is None:
        print("No se pudo cargar el modelo. Saliendo...")
        return
    
    # Verificar que el directorio existe
    if not os.path.exists(images_dir):
        print(f"✗ El directorio {images_dir} no existe")
        return
    
    # Obtener lista de imágenes
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
    images = []
    
    for file in os.listdir(images_dir):
        if any(file.lower().endswith(ext) for ext in image_extensions):
            images.append(os.path.join(images_dir, file))
    
    if not images:
        print(f"No se encontraron imágenes en {images_dir}")
        return
    
    print(f"Encontradas {len(images)} imágenes para procesar")
    
    # Procesar cada imagen
    for i, image_path in enumerate(images, 1):
        print(f"\n[{i}/{len(images)}] Procesando: {os.path.basename(image_path)}")
        caption = generate_caption(model, feature_extractor, tokenizer, image_path)
        
        if caption:
            print(f"Descripción: {caption}")
        else:
            print("No se pudo generar descripción")

def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description="Probar modelo de imagen a texto entrenado")
    parser.add_argument("--image", "-i", help="Ruta a una imagen específica")
    parser.add_argument("--directory", "-d", help="Directorio con imágenes para procesar")
    parser.add_argument("--model", "-m", default="image-to-text-finetuned", 
                       help="Nombre del modelo en MLflow")
    parser.add_argument("--version", "-v", default="latest",
                       help="Versión del modelo")
    
    args = parser.parse_args()
    
    print("=== Probador de Modelo de Imagen a Texto ===")
    print()
    
    # Verificar argumentos
    if not args.image and not args.directory:
        print("Debes especificar --image o --directory")
        print("Ejemplo: python test_model.py --image ./images/test.jpg")
        print("Ejemplo: python test_model.py --directory ./images")
        return
    
    # Configurar MLflow
    try:
        mlflow.set_tracking_uri("http://localhost:5000")
        print("✓ Conectado a MLflow en http://localhost:5000")
    except Exception as e:
        print(f"✗ Error conectando a MLflow: {e}")
        print("Asegúrate de que el servidor MLflow esté ejecutándose")
        return
    
    # Ejecutar pruebas
    if args.image:
        test_single_image(args.image, args.model, args.version)
    elif args.directory:
        test_multiple_images(args.directory, args.model, args.version)

if __name__ == "__main__":
    main() 