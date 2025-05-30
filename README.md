# Sistema de Gestión Automática de Incidencias

Este proyecto implementa un sistema de gestión automática de incidencias utilizando técnicas avanzadas de procesamiento de lenguaje natural y bases de datos vectoriales.

## Estructura del Proyecto

El proyecto está dividido en varios componentes:

1. **MockGestorIncidencias**: Servicio mock que simula un gestor de incidencias existente.
2. **MockSistema**: Servicio mock que simula el sistema principal al que se le da mantenimiento.
3. **BaseDeDatosVectorial**: Base de datos vectorial para almacenar y consultar información relevante.
4. **SistemaPrincipal**: Sistema principal que implementa la lógica de resolución automática de incidencias.

## Requisitos

- Docker y Docker Compose
- Python 3.8+
- Node.js 16+
- Ollama (para entorno DESA)

## Configuración

1. Clonar el repositorio
2. Configurar las variables de entorno en el archivo `env`
3. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```
4. Iniciar los servicios:
   ```bash
   docker-compose up -d
   ```

## Uso

1. Ejecutar el proceso batch para preparar la base de datos vectorial:
   ```bash
   python batch.py
   ```

2. Ejecutar el sistema principal:
   ```bash
   python main.py
   ```

## Estructura de Carpetas

```
.
├── api/                    # Funciones para llamadas API
├── llm/                    # Definiciones de LLMs y embeddings
├── prompts/               # Prompts para los LLMs
├── resources/             # Recursos del sistema
├── mock-gestor-incidencias/ # Servicio mock de incidencias
├── mock-sistema/          # Servicio mock del sistema
├── main.py               # Servicio principal
├── resolution.py         # Servicio de resolución
├── batch.py             # Servicio de preparación de datos
├── requirements.txt     # Dependencias de Python
└── docker-compose.yml   # Configuración de Docker
```

## Variables de Entorno

Crear un archivo `env` con las siguientes variables:

```
ENTORNO=DESA
ETIQUETA=[SPAI]
OPENAI_API_KEY=your_api_key
MOCK_GESTOR_URL=http://localhost:3000
MOCK_SISTEMA_URL=http://localhost:3001
VECTOR_DB_URL=http://localhost:6333
```

## Licencia

Este proyecto está bajo la Licencia MIT.
