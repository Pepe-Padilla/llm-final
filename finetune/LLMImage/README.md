# Fine-tuning Simple para Modelo de Imagen a Texto

Sistema ultra simple de fine-tuning con 5 ciclos for anidados, siguiendo el principio KISS.

## 🎯 Características

- **5 ciclos for anidados** que prueban diferentes parámetros
- **Épocas fijo a 5** para todos los entrenamientos
- **Separación automática train/test** (80/20)
- **Registro en MLflow** con parámetros y métricas
- **Métricas ROUGE** para evaluación

## 📋 Requisitos

1. **Modelo base registrado**: Ejecutar `image_to_text_finetune.ipynb` primero
2. **Datos**: Archivo `entradas.json` con imágenes y textos
3. **MLflow server**: Ejecutándose en `http://localhost:5000`

## 🚀 Uso

```bash
# Ejecutar entrenamiento
python kiss_training.py
```

## 📊 Parámetros que prueba

- **batch_size**: [2, 4, 8]
- **learning_rate**: [1e-5, 5e-5, 1e-4]  
- **warmup_steps**: [50, 100, 200]
- **weight_decay**: [0.001, 0.01, 0.1]
- **max_length**: [128, 256]

**Total:** 162 combinaciones de parámetros

## 📈 Resultados

Cada entrenamiento se registra en MLflow con:
- Parámetros utilizados
- Métricas de entrenamiento (loss, tiempo)
- Métricas de evaluación (ROUGE-1, ROUGE-2, ROUGE-L)

## 🔍 Ver resultados

```bash
# Abrir MLflow UI
mlflow ui --port 5000
```

Luego abrir: http://localhost:5000

## 📁 Estructura

```
LLMImage/
├── kiss_training.py      # Código principal
├── image_to_text_finetune.ipynb  # Registro modelo base
├── entradas.json         # Datos de entrenamiento
├── images/               # Imágenes
├── requirements.txt      # Dependencias
└── README.md            # Este archivo
```

¡Súper simple y fácil de explicar! 🎯 