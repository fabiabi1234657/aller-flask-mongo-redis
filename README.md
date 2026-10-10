# Taller Flask + MongoDB + Redis

API REST desarrollada con Flask, MongoDB y Redis para gestión de vehículos.

## Integrantes
- Jorge (ITP - Universidad del Putumayo)

## Requisitos
- Python 3.x
- MongoDB corriendo en localhost:27017
- Redis corriendo en localhost:6379 (WSL Ubuntu: `sudo service redis-server start`)

## Instalación

```bash
# 1. Clonar el repositorio
git clone https://github.com/jhorch1/aller-flask-mongo-redis.git
cd aller-flask-mongo-redis

# 2. Crear entorno virtual
python -m venv env
env\Scripts\activate        # Windows
# source env/bin/activate   # Linux/Mac

# 3. Instalar dependencias
pip install flask pymongo redis
```

## Cargar datos en MongoDB

Abrir mongosh y ejecutar:
```js
load("cargar_vehiculos.js")
```

## Ejecutar la API

```bash
flask --app app_vehiculos run
```

La API queda disponible en `http://127.0.0.1:5000`

## Endpoints

| Método | URL | Descripción |
|--------|-----|-------------|
| GET | /vehiculos | Listar todos los vehículos |
| GET | /vehiculos/\<nombre\> | Buscar un vehículo |
| POST | /vehiculos | Registrar nuevo vehículo |
| PUT | /vehiculos/\<nombre\> | Actualizar un vehículo |
| DELETE | /vehiculos/\<nombre\> | Eliminar un vehículo |

## Caché Redis
- Lista completa: 120 segundos
- Vehículo individual: 60 segundos
- Primera consulta: `"origen": "mongo"`
- Segunda consulta: `"origen": "redis"`

## Estructura del proyecto
```
taller-flask-mongo-redis/
├── app_vehiculos.py       # API REST principal
├── cargar_vehiculos.js    # Script para poblar MongoDB
├── .gitignore
└── README.md
```
