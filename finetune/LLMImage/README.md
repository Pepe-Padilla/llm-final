# Fine-tuning de Modelo de Imagen a Texto

Este directorio contiene un notebook de Jupyter para realizar fine-tuning de un modelo de imagen a texto usando Hugging Face y MLflow.

## Estructura del proyecto

```
LLMImage/
├── image_to_text_finetune.ipynb  # Notebook principal
├── entradas.json                 # Archivo con pares imagen-texto
├── images/                       # Directorio con las imágenes
└── README.md                     # Este archivo
```

## Requisitos previos

1. **MLflow Server**: Asegúrate de tener MLflow ejecutándose localmente:
   ```bash
   mlflow server --host 0.0.0.0 --port 5000
   ```

2. **Dependencias**: Instala las dependencias necesarias:
   ```bash
   pip install transformers datasets torch torchvision pillow mlflow accelerate jupyter
   ```

## Preparación de datos

### 1. Estructura del archivo `entradas.json`

El archivo debe contener un array de objetos con la siguiente estructura:

```json
[
  {
    "imagen": "nombre_imagen.jpg",
    "texto": "Descripción de la imagen"
  },
  {
    "imagen": "otra_imagen.png", 
    "texto": "Otra descripción"
  }
]
```

### 2. Imágenes

Coloca todas las imágenes referenciadas en `entradas.json` en el directorio `images/`. Los formatos soportados son:
- JPG/JPEG
- PNG
- BMP
- TIFF

## Uso del notebook

1. **Abrir el notebook**:
   ```bash
   jupyter notebook image_to_text_finetune.ipynb
   ```

2. **Ejecutar las celdas en orden**:
   - La primera celda instala las dependencias
   - Las siguientes descargan el modelo base
   - Luego se cargan y procesan los datos
   - Finalmente se entrena el modelo y se guarda en MLflow

## Configuración del modelo

El notebook usa el modelo `nlpconnect/vit-gpt2-image-captioning` como base, que combina:
- **Encoder**: Vision Transformer (ViT) para procesar imágenes
- **Decoder**: GPT-2 para generar texto

## Parámetros de entrenamiento

Los parámetros por defecto son:
- **Learning rate**: 5e-5
- **Batch size**: 4
- **Epochs**: 3
- **Optimizer**: AdamW con weight decay 0.01

Puedes modificar estos parámetros en la celda de configuración del entrenamiento.

## Resultados

Después del entrenamiento:
1. El modelo se guarda en MLflow con el nombre `image-to-text-finetuned`
2. Se crea un directorio `results/` con el modelo, tokenizer y feature extractor
3. Puedes probar el modelo con nuevas imágenes

## Carga del modelo entrenado

Para cargar el modelo desde MLflow:

```python
import mlflow.pytorch

# Cargar modelo
model = mlflow.pytorch.load_model("models:/image-to-text-finetuned/latest")
```

## Troubleshooting

### Error: "No se encontró el archivo entradas.json"
- Asegúrate de que el archivo existe en el directorio del notebook
- Verifica que el formato JSON sea válido

### Error: "Imagen no encontrada"
- Verifica que las rutas en `entradas.json` coincidan con los archivos en `images/`
- Asegúrate de que las imágenes estén en formatos soportados

### Error de memoria GPU
- Reduce el `batch_size` en los argumentos de entrenamiento
- Usa `fp16=False` si tienes problemas de compatibilidad

### Error de conexión a MLflow
- Verifica que el servidor MLflow esté ejecutándose en `http://localhost:5000`
- Asegúrate de que no haya problemas de red o firewall 