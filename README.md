# Taller: API REST con Flask, MongoDB y Redis (Cache-Aside)

API REST desarrollada con **Flask**, **MongoDB** y **Redis** para la gestión de vehículos con un sistema de almacenamiento en caché bajo el patrón **Cache-Aside**, aplicando tiempos de expiración (TTL) dinámicos e invalidación de caché ante modificaciones.

## Integrantes
- **Jorge William Termal** (ITP - Universidad del Putumayo)
- **Fabian Andres Coral Garcia** (ITP - Universidad del Putumayo)
- **Cristian Esteban Pinchao Hernandez** (ITP - Universidad del Putumayo)

**Docente:** Fredy Jacanamijoy  
**Asignatura:** Bases de Datos No Relacionales — Semestre 7 (Nocturna)

## Repositorio
https://github.com/fabiabi1234657/aller-flask-mongo-redis

## Requisitos
- Python 3.x
- MongoDB corriendo en `localhost:27017`
- Redis corriendo en `localhost:6379`

---

## Requisitos previos
- **Python 3.10+** instalado
- **MongoDB** corriendo en `localhost:27017`
- **Redis** corriendo en `localhost:6379`
  - En WSL Ubuntu: `sudo service redis-server start`
  - En Windows / Docker: servicio de Redis activo
  - Verificar conexión con: `redis-cli ping` → debe responder `PONG`

---

## 1. Instalación de dependencias

El proyecto incluye el archivo `requirements.txt` con todas las dependencias necesarias:

```bash
# 1. Clonar el repositorio
git clone https://github.com/fabiabi1234657/aller-flask-mongo-redis.git
cd aller-flask-mongo-redis

# 2. Crear y activar entorno virtual (opcional pero recomendado)
python -m venv env
# En Windows:
env\Scripts\activate
# En Linux/Mac:
# source env/bin/activate

# 3. Instalar librerías
pip install -r requirements.txt

Contenido de `requirements.txt`:
- `Flask`: Framework web para la API REST.
- `pymongo`: Controlador oficial de MongoDB para Python.
- `redis`: Cliente oficial de Redis para Python.

---

## 2. Iniciar Servicios (MongoDB y Redis)

### MongoDB
```bash
# Windows (como Administrador si está como servicio):
net start MongoDB

# O verificar en mongosh:
mongosh
> show dbs
```

### Redis
```bash
# En WSL Ubuntu:
sudo service redis-server start

# Verificar:
redis-cli ping
# Respuesta esperada: PONG
```

---

## 3. Cargar datos iniciales en MongoDB

Ejecutar el script `cargar_vehiculos.js` dentro de la consola `mongosh`:

```bash
load("cargar_vehiculos.js")
```
load("cargar_vehiculos.js")
```

O verificar los datos cargados:
```js
use automoviles
db.vehiculos.find().pretty()
```

---

## 4. Ejecución de la API REST

Para iniciar la aplicación Flask:

```bash
python app_vehiculos.py
```
O con el CLI de Flask:
```bash
python app_vehiculos.py
```

La API quedará escuchando en `http://127.0.0.1:5000`.

---

## 5. Reglas de Caché con Redis (Especificación del Taller)

El sistema utiliza **Redis** (base de datos lógica `db=3`) como caché en memoria bajo las siguientes reglas oficiales:

### A. Tiempos de Expiración (TTL) Dinámicos
El TTL se calcula a partir del número de caracteres del campo que identifica al vehículo (`vehiculo`):

| Condición (longitud del nombre) | Tiempo de expiración (TTL) | Ejemplo de vehículo |
|---------------------------------|----------------------------|---------------------|
| **5 caracteres o menos** | **15 segundos** | `Tren` (4), `Canoa` (5) |
| **Más de 5 y hasta 10 caracteres** | **20 segundos** | `Velero` (6), `Furgoneta` (9) |
| **Más de 10 caracteres** | **40 segundos** | `Motocicleta` (11), `Helicóptero` (11) |

> **Nota:** todos los vehículos de `cargar_vehiculos.js` tienen descripción de más de 20 caracteres, por lo que **no se guardan en caché**. Para demostrar los TTL se deben crear vehículos nuevos con descripción de 20 caracteres o menos.

### B. Regla Prioritaria (Longitud de la Descripción)
> **Condición:** Si el campo `descripcion` tiene **más de 20 caracteres**, el vehículo **NO se almacena en caché** en Redis. Siempre se consulta directamente en MongoDB y responde con `"origen": "mongo"`.

### C. Serialización Segura (JSON Seguro)
- Se reemplaza `eval()` y `str()` por `json.dumps()` y `json.loads()`.
- Se excluye `_id` para mantener compatibilidad JSON estándar.

### D. Invalidación de Caché
- Al actualizar o eliminar un vehículo, se borra la clave individual y la lista general.
- Al crear un vehículo, se invalida `todos_vehiculos`.

---

## 6. Endpoints Disponibles

| Método | Endpoint | Descripción | Comportamiento Caché |
|--------|----------|-------------|----------------------|
| `POST` | `/vehiculos` | Registrar un nuevo vehículo | Invalida `todos_vehiculos` |
| `GET` | `/vehiculos` | Listar todos los vehículos | Caché de 120 s |
| `GET` | `/vehiculos/<nombre>` | Consultar un vehículo por nombre | TTL según nombre o sin caché si `descripcion > 20` |
| `PUT` | `/vehiculos/<nombre>` | Actualizar información de un vehículo | Invalida caché del vehículo y lista general |
| `DELETE` | `/vehiculos/<nombre>` | Eliminar un vehículo | Invalida caché del vehículo y lista general |
| `GET` | `/debug/cache` | Ver claves activas en Redis con su TTL restante | Consulta directa a Redis |
| `GET` | `/debug/cache/<nombre>` | Inspeccionar estado de caché de un vehículo | Consulta directa a Redis (`ttl` y `en_cache`) |
| `GET` | `/health` | Verificar conexión con MongoDB y Redis | Responde `{"mongo": "ok", "redis": "ok"}` o código 503 |

---

## 7. Guía de Pruebas y Demostración en Postman

1. Crear un vehículo con `descripcion` corta para verificar TTL.
2. Consultar `GET /vehiculos/<nombre>` y comprobar el cambio de `origen` a `redis`.
3. Verificar el TTL con `GET /debug/cache/<nombre>`.
4. Probar la regla de descripción > 20 caracteres para confirmar que no se guarda en caché.
5. Validar la invalidación de caché con `PUT` y `DELETE`.
```
