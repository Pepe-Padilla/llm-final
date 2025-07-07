import os
import requests
import mlflow
import mlflow.pytorch
from PIL import Image
import torch
from transformers import AutoTokenizer
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv()

# Cargar modelo una sola vez globalmente
try:
    mlflow.set_tracking_uri('http://localhost:5000')
    global_model = mlflow.pytorch.load_model('models:/image-to-text-finetuned/latest')
    print("Modelo fine-tuneado cargado exitosamente")
except Exception as e:
    print(f"Error cargando modelo fine-tuneado: {e}")
    global_model = None

def analyze_image_with_fine_tuned_model(image_url: str, model) -> str:
    """
    Analiza una imagen usando el modelo fine-tuneado.
    
    Args:
        image_url: URL de la imagen a analizar
        model: Modelo fine-tuneado cargado
        
    Returns:
        str: Descripción del problema encontrado en la imagen
    """
    try:
        # Descargar la imagen
        response = requests.get(image_url)
        response.raise_for_status()
        
        # Guardar imagen temporalmente
        temp_path = "temp_image.png"
        with open(temp_path, "wb") as f:
            f.write(response.content)
        
        # Cargar y procesar imagen
        image = Image.open(temp_path).convert("RGB")
        
        # Cargar tokenizer
        tokenizer = AutoTokenizer.from_pretrained('./finetune/LLMImage/results/tokenizer_base')
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        
        # Cargar feature extractor
        from transformers import ViTImageProcessor
        feature_extractor = ViTImageProcessor.from_pretrained('./finetune/LLMImage/results/feature_extractor_base')
        
        # Procesar imagen
        pixel_values = feature_extractor(image, return_tensors="pt").pixel_values
        
        # Generar descripción
        with torch.no_grad():
            generated_ids = model.generate(
                pixel_values,
                max_length=128,
                num_beams=1,
                early_stopping=True
            )
        
        # Decodificar resultado
        generated_text = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
        
        # Limpiar archivo temporal
        os.remove(temp_path)
        
        return generated_text
        
    except Exception as e:
        raise e

def analyze_image(image_url: str) -> str:
    """
    Analiza una imagen adjunta y genera una descripción del problema.
    
    Args:
        image_url: URL de la imagen a analizar
        
    Returns:
        str: Descripción del problema encontrado en la imagen
    """
    try:
        if global_model is None:
            return f"Error: No se pudo cargar el modelo fine-tuneado"
        
        # Analizar con modelo fine-tuneado
        return analyze_image_with_fine_tuned_model(image_url, global_model)
        
    except Exception as e:
        raise e

def process_attachments(historial_entry: dict) -> str:
    """
    Procesa los adjuntos de una entrada del historial y genera descripción adicional.
    
    Args:
        historial_entry: Entrada del historial con posibles adjuntos
        
    Returns:
        str: Descripción adicional basada en los adjuntos
    """
    adjuntos = historial_entry.get('adjuntos', [])
    if not adjuntos:
        return ""
    
    descriptions = []
    for adjunto in adjuntos:
        if adjunto.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
            description = analyze_image(adjunto)
            descriptions.append(description)
    
    if descriptions:
        return " | ".join(descriptions)
    
    return "" 