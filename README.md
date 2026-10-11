# Taller: API REST con Flask, MongoDB y Redis (Cache-Aside)

API REST desarrollada con **Flask**, **MongoDB** y **Redis** para la gestión de vehículos con un sistema de almacenamiento en caché bajo el patrón **Cache-Aside**, aplicando tiempos de expiración (TTL) dinámicos e invalidación de caché ante modificaciones.

---

## Integrantes
- **Jorge William Termal** (ITP - Universidad del Putumayo)
- **Fabian Andres Coral Garcia** (ITP - Universidad del Putumayo)
- **Cristian Esteban Pinchao Hernandez** (ITP - Universidad del Putumayo)

**Docente:** Fredy Jacanamijoy  
**Asignatura:** Bases de Datos No Relacionales — Semestre 7 (Nocturna)

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
```

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

```js
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
flask --app app_vehiculos run
```

La API quedará escuchando en `http://127.0.0.1:5000`.

---

## 5. Reglas de Caché con Redis (Especificación del Taller)

El sistema utiliza **Redis** (base de datos lógica `db=3`) como caché en memoria bajo las siguientes reglas oficiales:

### A. Tiempos de Expiración (TTL) Dinámicos
El TTL se calcula a partir del número de caracteres del campo que identifica al vehículo (`vehiculo`):

| Condición (longitud del nombre) | Tiempo de expiración (TTL) | Ejemplo de vehículo |
|---------------------------------|----------------------------|---------------------|
| **5 caracteres o menos**        | **15 segundos**            | `Tren` (4), `Canoa` (5) |
| **Más de 5 y hasta 10 caracteres** | **20 segundos**         | `Velero` (6), `Furgoneta` (9) |
| **Más de 10 caracteres**        | **40 segundos**            | `Motocicleta` (11), `Helicóptero` (11) |

> **Nota:** todos los vehículos de `cargar_vehiculos.js` tienen descripción de más de 20 caracteres, por lo que **no se guardan en caché** (regla B). Para demostrar los TTL se deben crear vehículos nuevos con descripción de 20 caracteres o menos (ver pruebas de la sección 7).

### B. Regla Prioritaria (Longitud de la Descripción)
> **Condición:** Si el campo `descripcion` tiene **más de 20 caracteres**, el vehículo **NO se almacena en caché** en Redis. Siempre se consulta directamente en MongoDB y responde con `"origen": "mongo"`. Esta regla tiene prioridad absoluta sobre las reglas de TTL.

### C. Serialización Segura (JSON Seguro)
- Se sustituyó el uso inseguro de `eval()` y `str()` por `json.dumps()` para almacenar en Redis y `json.loads()` para recuperar desde Redis.
- Se gestiona la exclusión de `_id` (`{"_id": 0}`) para garantizar compatibilidad total con el formato JSON estándar.

### D. Invalidación de Caché
- Al **actualizar (`PUT`)** o **eliminar (`DELETE`)** un vehículo, se elimina automáticamente su clave individual en Redis (`vehiculo:<nombre>`) y la clave de la lista general (`todos_vehiculos`).
- Al **crear (`POST`)** un vehículo, se invalida la lista general en Redis para mantener los datos sincronizados.

---

## 6. Endpoints Disponibles

| Método | Endpoint | Descripción | Comportamiento Caché |
|--------|----------|-------------|----------------------|
| `POST` | `/vehiculos` | Registrar un nuevo vehículo | Invalida `todos_vehiculos` |
| `GET` | `/vehiculos` | Listar todos los vehículos | Sin caché (siempre `origen: mongo`) |
| `GET` | `/vehiculos/<nombre>` | Consultar un vehículo por nombre | Aplica reglas de TTL (15s, 20s, 40s) o exclusión si desc > 20 |
| `PUT` | `/vehiculos/<nombre>` | Actualizar información de un vehículo | Invalida caché del vehículo y lista general |
| `DELETE` | `/vehiculos/<nombre>` | Eliminar un vehículo | Invalida caché del vehículo y lista general |
| `GET` | `/debug/cache/<nombre>` | Inspeccionar estado de caché y TTL restante | Consulta directa a Redis (`ttl` y `en_cache`) |

---

## 7. Guía de Pruebas y Demostración en Postman

### Prueba 1: TTL de 15 segundos (Nombre ≤ 5 caracteres, Descripción ≤ 20 caracteres)
1. **Crear vehículo:** `POST http://127.0.0.1:5000/vehiculos`
   ```json
   {
     "vehiculo": "Tren",
     "categoria": "Terrestre (motorizado)",
     "peso_toneladas": 500,
     "descripcion": "Corta"
   }
   ```
2. **Primera consulta:** `GET http://127.0.0.1:5000/vehiculos/Tren`
   - Responde: `"origen": "mongo"` (y lo guarda en Redis con TTL de 15 segundos).
3. **Segunda consulta inmediata:** `GET http://127.0.0.1:5000/vehiculos/Tren`
   - Responde: `"origen": "redis"`.
4. **Verificar TTL restante:** `GET http://127.0.0.1:5000/debug/cache/Tren`
   - Responde: `{"en_cache": true, "ttl_segundos": 13}`.
5. **Esperar 15 segundos y volver a consultar:**
   - Responde: `"origen": "mongo"` (el registro expiró automáticamente en Redis).

---

### Prueba 2: TTL de 20 segundos (Nombre entre 6 y 10 caracteres, Descripción ≤ 20 caracteres)
1. **Crear vehículo:** `POST http://127.0.0.1:5000/vehiculos`
   ```json
   {
     "vehiculo": "Velero",
     "categoria": "Acuático",
     "peso_toneladas": 2,
     "descripcion": "Navega con viento"
   }
   ```
   *(Nombre "Velero" = 6 caracteres; descripción = 17 caracteres ≤ 20)*
2. **Consultar:** `GET http://127.0.0.1:5000/vehiculos/Velero`
   - 1ª vez: `"origen": "mongo"` (almacena en Redis con TTL de 20s).
   - 2ª vez: `"origen": "redis"`.
3. **Verificar en debug:** `GET http://127.0.0.1:5000/debug/cache/Velero`
   - Muestra `ttl_segundos` iniciando en 20s.

---

### Prueba 3: TTL de 40 segundos (Nombre > 10 caracteres, Descripción ≤ 20 caracteres)
1. **Crear vehículo:** `POST http://127.0.0.1:5000/vehiculos`
   ```json
   {
     "vehiculo": "Motocicleta",
     "categoria": "Terrestre (motorizado)",
     "peso_toneladas": 0.2,
     "descripcion": "Dos ruedas"
   }
   ```
   *(Nombre "Motocicleta" = 11 caracteres; descripción = 10 caracteres ≤ 20)*
2. **Consultar:** `GET http://127.0.0.1:5000/vehiculos/Motocicleta`
   - 1ª vez: `"origen": "mongo"` (almacena en Redis con TTL de 40s).
   - 2ª vez: `"origen": "redis"`.
3. **Verificar en debug:** `GET http://127.0.0.1:5000/debug/cache/Motocicleta`
   - Muestra `ttl_segundos` iniciando en 40s.

---

### Prueba 4: Regla Prioritaria — Descripción > 20 caracteres (NO se guarda en Redis)
1. **Consultar cualquier vehículo con descripción larga**, por ejemplo el `Automóvil` cargado inicialmente desde `cargar_vehiculos.js` (cuya descripción es `"Vehículo común para transporte personal."`, con 41 caracteres):
   - `GET http://127.0.0.1:5000/vehiculos/Automóvil`
2. **Respuesta 1ª llamada:** `"origen": "mongo"`.
3. **Respuesta 2ª llamada inmediata:** `"origen": "mongo"`.
4. **Verificar en debug:** `GET http://127.0.0.1:5000/debug/cache/Automóvil`
   ```json
   {
     "clave": "vehiculo:Automóvil",
     "en_cache": false,
     "ttl_segundos": null
   }
   ```
   > Demuestra que la condición de descripción superior a 20 caracteres tiene prioridad y bloquea el guardado en Redis.

---

### Prueba 5: Invalidación de Caché al Modificar (PUT) y Eliminar (DELETE)
1. Con `Tren` en caché (`"origen": "redis"`):
2. **Modificar:** `PUT http://127.0.0.1:5000/vehiculos/Tren`
   ```json
   {
     "peso_toneladas": 600
   }
   ```
3. **Consultar inmediatamente:** `GET http://127.0.0.1:5000/vehiculos/Tren`
   - Responde: `"origen": "mongo"`, demostrando que la caché fue eliminada tras la actualización para evitar datos obsoletos.
4. **Eliminar:** `DELETE http://127.0.0.1:5000/vehiculos/Tren`
   - Elimina de MongoDB y borra cualquier rastro en Redis.

---

## 8. Estructura del Repositorio

```
aller-flask-mongo-redis/
├── app_vehiculos.py       # API REST con endpoints CRUD y lógica de Redis
├── cargar_vehiculos.js    # Script de inicialización para MongoDB
├── requirements.txt       # Dependencias del proyecto (Flask, pymongo, redis)
├── .gitignore             # Archivos excluidos de control de versiones
└── README.md              # Documentación técnica y guía de pruebas
```
