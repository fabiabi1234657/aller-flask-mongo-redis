# Taller: API REST con Flask, MongoDB y Redis

API REST para gestión de vehículos, implementando el patrón **Cache-Aside** con TTL dinámico según la longitud del nombre del vehículo.

## Integrantes

- **Jorge Montoya Manchola** (ITP - Universidad del Putumayo)
- **Fabian Andres Coral Garcia** (ITP - Universidad del Putumayo)
- **Cristian Esteban Pinchao Hernandez** (ITP - Universidad del Putumayo)

## Repositorio

https://github.com/jhorch1/aller-flask-mongo-redis

## Requisitos

- Python 3.x
- MongoDB corriendo en `localhost:27017`
- Redis corriendo en `localhost:6379`

## Instalación

```bash
# Crear y activar entorno virtual
python -m venv env
env\Scripts\activate       # Windows
source env/bin/activate    # Linux / macOS

# Instalar dependencias
pip install -r requirements.txt
```

## Cargar datos iniciales

Abrir **mongosh** y ejecutar:

```bash
load("cargar_vehiculos.js")
```

## Ejecutar la API

```bash
python app_vehiculos.py
```

La API queda disponible en `http://127.0.0.1:5000`

## Endpoints

| Método | URL | Descripción |
|--------|-----|-------------|
| GET | `/vehiculos` | Listar todos los vehículos |
| GET | `/vehiculos/<nombre>` | Buscar un vehículo por nombre |
| POST | `/vehiculos` | Registrar un nuevo vehículo |
| PUT | `/vehiculos/<nombre>` | Actualizar un vehículo existente |
| DELETE | `/vehiculos/<nombre>` | Eliminar un vehículo |
| GET | `/debug/cache` | Ver claves activas en Redis con su TTL restante |

## Reglas de caché (Cache-Aside con TTL dinámico)

La clave de Redis para cada vehículo individual expira según estas reglas:

| Condición | TTL |
|-----------|-----|
| Descripción mayor a 20 caracteres | Sin caché |
| Nombre con 5 o menos caracteres | 15 segundos |
| Nombre con 6 a 10 caracteres | 20 segundos |
| Nombre con más de 10 caracteres | 40 segundos |

La lista completa de vehículos se guarda en caché por **120 segundos**.

En PUT y DELETE se invalida automáticamente el caché del vehículo modificado y de la lista general.

## Ejemplo de respuesta GET individual

```json
{
  "origen": "mongo → guardado en redis 40s",
  "datos": {
    "vehiculo": "Motocicleta",
    "categoria": "Terrestre (motorizado)",
    "peso_toneladas": 0.2,
    "descripcion": "Vehículo de dos ruedas impulsado por motor."
  }
}
```

En la segunda consulta, `"origen"` cambia a `"redis"`.

## Estructura del proyecto

```
taller-flask-mongo-redis/
├── app_vehiculos.py      # API principal
├── cargar_vehiculos.js   # Script para cargar datos en MongoDB
├── requirements.txt      # Dependencias Python
└── README.md
```
