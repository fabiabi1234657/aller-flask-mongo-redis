# Taller Flask + MongoDB + Redis

API REST desarrollada con Flask, MongoDB y Redis para gestión de vehículos.

## Integrantes
- Jorge (ITP - Universidad del Putumayo)
- Fabian Andres Coral (uniputumayo)
- Cristian Esteban Pinchao Hernandez (uniputumayo)

---

## Requisitos previos
- Python 3.x instalado
- MongoDB corriendo en `localhost:27017`
- Redis corriendo en `localhost:6379`
  - En WSL Ubuntu: `sudo service redis-server start`
  - Verificar con: `redis-cli ping` → debe responder `PONG`

---

## 1. Instalar dependencias

```bash
# Clonar el repositorio (si no lo tienes)
git clone https://github.com/jhorch1/aller-flask-mongo-redis.git
cd aller-flask-mongo-redis

# Crear y activar entorno virtual
python -m venv env
env\Scripts\activate        # Windows
# source env/bin/activate   # Linux/Mac

# Instalar dependencias desde requirements.txt
pip install -r requirements.txt
```

---

## 2. Iniciar MongoDB

```bash
# Windows: iniciar el servicio (si no está corriendo)
net start MongoDB

# Verificar en mongosh
mongosh
> show dbs
```

---

## 3. Iniciar Redis

```bash
# En WSL Ubuntu
sudo service redis-server start

# Verificar
redis-cli ping
# Debe responder: PONG
```

---

## 4. Cargar los vehículos iniciales en MongoDB

Abrir `mongosh` y ejecutar el script:

```js
load("cargar_vehiculos.js")
```

O bien, dentro de mongosh paso a paso:

```js
use("automoviles")
db.vehiculos.find().pretty()
```

---

## 5. Ejecutar Flask

```bash
flask --app app_vehiculos run
```

La API queda disponible en `http://127.0.0.1:5000`

---

## 6. Endpoints disponibles

| Método | URL | Descripción |
|--------|-----|-------------|
| POST   | `/vehiculos` | Registrar nuevo vehículo |
| GET    | `/vehiculos` | Listar todos los vehículos |
| GET    | `/vehiculos/<nombre>` | Buscar un vehículo por nombre |
| PUT    | `/vehiculos/<nombre>` | Actualizar un vehículo |
| DELETE | `/vehiculos/<nombre>` | Eliminar un vehículo |
| GET    | `/debug/cache/<nombre>` | Ver estado de caché Redis |

---

## 7. Probar cada endpoint en Postman

### POST /vehiculos — Crear vehículo
- **Método:** POST  
- **URL:** `http://127.0.0.1:5000/vehiculos`  
- **Body (JSON):**
```json
{
  "vehiculo": "Tren",
  "categoria": "Terrestre (motorizado)",
  "peso_toneladas": 500,
  "descripcion": "Corta"
}
```

---

### GET /vehiculos — Listar todos
- **Método:** GET  
- **URL:** `http://127.0.0.1:5000/vehiculos`  
- Primera llamada → `"origen": "mongo"` (consulta MongoDB y guarda en Redis 120 s)  
- Segunda llamada → `"origen": "redis"` (responde desde caché)

---

### GET /vehiculos/<nombre> — Buscar uno
- **Método:** GET  
- **URL:** `http://127.0.0.1:5000/vehiculos/Tren`  
- Primera llamada → `"origen": "mongo"`  
- Segunda llamada → `"origen": "redis"`

---

### PUT /vehiculos/<nombre> — Actualizar
- **Método:** PUT  
- **URL:** `http://127.0.0.1:5000/vehiculos/Tren`  
- **Body (JSON):**
```json
{
  "peso_toneladas": 600
}
```

---

### DELETE /vehiculos/<nombre> — Eliminar
- **Método:** DELETE  
- **URL:** `http://127.0.0.1:5000/vehiculos/Tren`

---

### GET /debug/cache/<nombre> — Ver caché
- **Método:** GET  
- **URL:** `http://127.0.0.1:5000/debug/cache/Tren`  
- Respuesta si está en caché:
```json
{
  "clave": "vehiculo:Tren",
  "en_cache": true,
  "ttl_segundos": 13
}
```
- Respuesta si no está:
```json
{
  "clave": "vehiculo:Tren",
  "en_cache": false,
  "ttl_segundos": null
}
```

---

## 8. Demostrar Redis — origen mongo, origen redis y expiración

### Paso 1 — Primera consulta (origen: mongo)
```
GET http://127.0.0.1:5000/vehiculos/Avión
```
→ Responde `"origen": "mongo"` y guarda en Redis con TTL de 20 s ("Avión" = 5 chars sin tilde / 6 con tilde).

### Paso 2 — Segunda consulta inmediata (origen: redis)
```
GET http://127.0.0.1:5000/vehiculos/Avión
```
→ Responde `"origen": "redis"`.

### Paso 3 — Ver TTL en tiempo real
```
GET http://127.0.0.1:5000/debug/cache/Avión
```
→ Muestra `"ttl_segundos": 17` (o el tiempo que reste).

### Paso 4 — Esperar a que expire y volver a consultar
Después de que el TTL llega a 0:
```
GET http://127.0.0.1:5000/vehiculos/Avión
```
→ Vuelve a responder `"origen": "mongo"` (caché expirada).

---

## 9. Lógica de caché Redis

| Campo `vehiculo` (longitud) | TTL individual |
|-----------------------------|---------------|
| ≤ 5 caracteres              | 15 segundos   |
| 6 – 10 caracteres           | 20 segundos   |
| > 10 caracteres             | 40 segundos   |

**Regla prioritaria:** Si `descripcion` tiene más de 20 caracteres, el vehículo **no se guarda en Redis** (siempre responde desde MongoDB).

La caché de la lista general (`GET /vehiculos`) dura **120 segundos**.

---

## Estructura del proyecto

```
aller-flask-mongo-redis/
├── app_vehiculos.py       # API REST principal
├── cargar_vehiculos.js    # Script para poblar MongoDB
├── requirements.txt       # Dependencias Python
├── .gitignore
└── README.md
```
