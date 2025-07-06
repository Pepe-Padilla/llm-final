import json
import os
import torch
from transformers import (
    VisionEncoderDecoderModel, 
    ViTImageProcessor, 
    AutoTokenizer,
    TrainingArguments,
    Trainer
)
import mlflow
import mlflow.pytorch
from PIL import Image
import evaluate
from sklearn.model_selection import train_test_split
import numpy as np

# Verificar que MLflow esté ejecutándose
try:
    mlflow.set_tracking_uri('http://localhost:5000')
    print("✅ MLflow conectado")
except Exception as e:
    print(f"❌ Error conectando a MLflow: {e}")
    print("Asegúrate de ejecutar: python start_mlflow_server.py")
    exit(1)

# Verificar archivos necesarios
required_files = [
    "entradas.json",
    "images/",
    "results/tokenizer_base/",
    "results/feature_extractor_base/"
]

for file_path in required_files:
    if not os.path.exists(file_path):
        print(f"❌ Error: No se encuentra {file_path}")
        print("Asegúrate de haber ejecutado el notebook de registro del modelo base")
        exit(1)

print("✅ Todos los archivos necesarios encontrados")

# Cargar modelo base desde MLflow
try:
    print("Cargando modelo base desde MLflow...")
    model = mlflow.pytorch.load_model('models:/image-to-text-base/latest')
    print("✅ Modelo base cargado")
except Exception as e:
    print(f"❌ Error cargando modelo base: {e}")
    print("Asegúrate de haber ejecutado el notebook de registro")
    exit(1)

# Cargar tokenizer y feature extractor
try:
    tokenizer = AutoTokenizer.from_pretrained('./results/tokenizer_base')
    feature_extractor = ViTImageProcessor.from_pretrained('./results/feature_extractor_base')
    print("✅ Tokenizer y feature extractor cargados")
except Exception as e:
    print(f"❌ Error cargando tokenizer/feature extractor: {e}")
    exit(1)

# Configurar tokenizer
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

# Cargar datos
try:
    print("Cargando datos...")
    with open("entradas.json", 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"✅ Datos cargados: {len(data)} entradas")
except Exception as e:
    print(f"❌ Error cargando datos: {e}")
    exit(1)

# Verificar que las imágenes existan
missing_images = []
for item in data:
    image_path = os.path.join("images", item["imagen"])
    if not os.path.exists(image_path):
        missing_images.append(item["imagen"])

if missing_images:
    print(f"❌ Imágenes faltantes: {missing_images[:5]}...")
    exit(1)

# Separar en train y test
train_data, test_data = train_test_split(data, test_size=0.2, random_state=42)
print(f"✅ Datos separados: {len(train_data)} train, {len(test_data)} test")

class SimpleDataset:
    def __init__(self, data, processor, tokenizer):
        self.data = data
        self.processor = processor
        self.tokenizer = tokenizer
    
    def __len__(self):
        return len(self.data)
    
    def __getitem__(self, idx):
        item = self.data[idx]
        
        try:
            # Cargar imagen
            image_path = os.path.join("images", item["imagen"])
            image = Image.open(image_path).convert("RGB")
            
            # Procesar imagen
            pixel_values = self.processor(image, return_tensors="pt").pixel_values.squeeze()
            
            # Tokenizar texto
            text = item["texto"]
            labels = self.tokenizer(
                text, 
                truncation=True, 
                padding="max_length", 
                max_length=128,
                return_tensors="pt"
            ).input_ids.squeeze()
            
            return {
                "pixel_values": pixel_values,
                "labels": labels
            }
        except Exception as e:
            print(f"❌ Error procesando item {idx}: {e}")
            # Retornar un item dummy en caso de error
            return {
                "pixel_values": torch.zeros(3, 224, 224),
                "labels": torch.zeros(128, dtype=torch.long)
            }

def compute_metrics(eval_preds):
    """Calcular métricas simples sin ROUGE"""
    try:
        predictions, labels = eval_preds
        
        # Si son tuplas, extraer el primer elemento
        if isinstance(predictions, tuple):
            predictions = predictions[0]
        if isinstance(labels, tuple):
            labels = labels[0]
        
        # Convertir a numpy si son tensores
        if hasattr(predictions, 'cpu'):
            predictions = predictions.cpu().numpy()
        if hasattr(labels, 'cpu'):
            labels = labels.cpu().numpy()
        
        # Si son listas, convertir a numpy
        if isinstance(predictions, list):
            predictions = np.array(predictions)
        if isinstance(labels, list):
            labels = np.array(labels)
        
        # Asegurar que sean 2D
        if len(predictions.shape) == 1:
            predictions = predictions.reshape(1, -1)
        if len(labels.shape) == 1:
            labels = labels.reshape(1, -1)
        
        # Decodificar predicciones
        decoded_preds = tokenizer.batch_decode(predictions, skip_special_tokens=True)
        
        # Reemplazar -100 en labels
        labels = np.where(labels != -100, labels, tokenizer.pad_token_id)
        decoded_labels = tokenizer.batch_decode(labels, skip_special_tokens=True)
        
        # Métricas simples
        total_predictions = len(decoded_preds)
        total_references = len(decoded_labels)
        
        # Calcular longitud promedio
        avg_pred_length = np.mean([len(pred.split()) for pred in decoded_preds])
        avg_ref_length = np.mean([len(ref.split()) for ref in decoded_labels])
        
        return {
            "total_predictions": total_predictions,
            "total_references": total_references,
            "avg_pred_length": avg_pred_length,
            "avg_ref_length": avg_ref_length,
            "sample_pred": decoded_preds[0] if decoded_preds else "",
            "sample_ref": decoded_labels[0] if decoded_labels else ""
        }
    except Exception as e:
        print(f"❌ Error calculando métricas: {e}")
        return {"total_predictions": 0, "total_references": 0, "avg_pred_length": 0, "avg_ref_length": 0}

def trainModel(batch_size, learning_rate, warmup_steps, weight_decay, max_length, saveModel=False):
    """
    Función simple para entrenar modelo con parámetros específicos
    """
    print(f"\n🔄 Entrenando con:")
    print(f"  batch_size: {batch_size}")
    print(f"  learning_rate: {learning_rate}")
    print(f"  warmup_steps: {warmup_steps}")
    print(f"  weight_decay: {weight_decay}")
    print(f"  max_length: {max_length}")
    
    try:
        # Crear datasets
        train_dataset = SimpleDataset(train_data, feature_extractor, tokenizer)
        test_dataset = SimpleDataset(test_data, feature_extractor, tokenizer)
        
        # Configurar argumentos de entrenamiento
        training_args = TrainingArguments(
            output_dir=f"./results/batch{batch_size}_lr{learning_rate}",
            num_train_epochs=5,  # Fijo en 5 épocas
            per_device_train_batch_size=batch_size,
            per_device_eval_batch_size=batch_size,
            learning_rate=learning_rate,
            warmup_steps=warmup_steps,
            weight_decay=weight_decay,
            logging_steps=10,
            eval_strategy="epoch",
            save_strategy="epoch",
            load_best_model_at_end=True,
            metric_for_best_model="eval_loss",  # Cambiado de eval_rouge1
            greater_is_better=False,  # Cambiado porque loss es mejor cuando es menor
            push_to_hub=False,
            dataloader_pin_memory=False,
            remove_unused_columns=False,
            report_to=None,
        )
        
        # Inicializar trainer
        trainer = Trainer(
            model=model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=test_dataset,
            processing_class=feature_extractor,  # Cambiado de tokenizer
            compute_metrics=compute_metrics
        )
        
        # Entrenar modelo
        print("🚀 Iniciando entrenamiento...")
        train_result = trainer.train()
        
        # Evaluar modelo
        print("📊 Evaluando modelo...")
        eval_result = trainer.evaluate()
        
        # Calcular métricas adicionales
        predictions = trainer.predict(test_dataset)
        metrics = compute_metrics((predictions.predictions, predictions.label_ids))
        
        # Registrar en MLflow
        mlflow.set_experiment("Image-to-Text-Simple")
        
        # Asegurar que no hay run activo
        try:
            mlflow.end_run()
        except:
            pass
        
        with mlflow.start_run(run_name=f"batch{batch_size}_lr{learning_rate}"):
            # Log parámetros
            mlflow.log_params({
                "batch_size": batch_size,
                "learning_rate": learning_rate,
                "warmup_steps": warmup_steps,
                "weight_decay": weight_decay,
                "max_length": max_length,
                "num_epochs": 5
            })
            
            # Log métricas de entrenamiento
            mlflow.log_metrics({
                "train_loss": train_result.training_loss,
                "train_runtime": train_result.metrics.get("train_runtime", 0),
            })
            
            # Log métricas de evaluación
            mlflow.log_metrics({
                "eval_loss": eval_result["eval_loss"],
                "total_predictions": metrics["total_predictions"],
                "total_references": metrics["total_references"],
                "avg_pred_length": metrics["avg_pred_length"],
                "avg_ref_length": metrics["avg_ref_length"],
            })
            
            if saveModel:
                mlflow.pytorch.log_model(trainer.model, "model", registered_model_name="image-to-text-simple")
                print("💾 Modelo guardado en MLflow")
            
            print(f"✅ Entrenamiento completado. Loss: {eval_result['eval_loss']:.4f}")
            return metrics
            
    except Exception as e:
        print(f"❌ Error en entrenamiento: {str(e)}")
        return None

# Parámetros a probar (completos)
batch_sizes = [2, 4, 8]  # Restaurado completo
learning_rates = [1e-5, 5e-5, 1e-4]  # Restaurado completo
warmup_steps_list = [50, 100, 200]  # Restaurado completo
weight_decays = [0.001, 0.01, 0.1]  # Restaurado completo
max_lengths = [128, 256]  # Restaurado completo

print("🎯 Iniciando entrenamientos con diferentes parámetros...")
print("=" * 60)

# Contador de entrenamientos exitosos
successful_runs = 0
total_runs = len(batch_sizes) * len(learning_rates) * len(warmup_steps_list) * len(weight_decays) * len(max_lengths)

# 5 ciclos for anidados
for batch_size in batch_sizes:
    for learning_rate in learning_rates:
        for warmup_steps in warmup_steps_list:
            for weight_decay in weight_decays:
                for max_length in max_lengths:
                    try:
                        result = trainModel(batch_size, learning_rate, warmup_steps, weight_decay, max_length)
                        if result:
                            successful_runs += 1
                    except Exception as e:
                        print(f"❌ Error en entrenamiento: {str(e)}")
                        continue

print(f"\n🎉 Entrenamientos completados!")
print(f"✅ Exitosos: {successful_runs}/{total_runs}")
print("📊 Revisa MLflow para ver todos los resultados.") 