import json
from flask import Flask, jsonify, request
from pymongo import MongoClient
import redis

app = Flask(__name__)

# ── CONEXIÓN A MONGODB ───────────────────────────────────────────────────────
mongo_client  = MongoClient("mongodb://localhost:27017")
db_mongo      = mongo_client["automoviles"]
vehiculos_col = db_mongo["vehiculos"]

# ── CONEXIÓN A REDIS ─────────────────────────────────────────────────────────
# db=3 para separarlo de otros ejercicios
cache = redis.Redis(host="localhost", port=6379, db=3, decode_responses=True)

LISTA_KEY = "todos_vehiculos"


def ttl_para(nombre: str) -> int:
    """Calcula el TTL en segundos según la longitud del campo vehiculo."""
    n = len(nombre)
    if n <= 5:
        return 15
    elif n <= 10:
        return 20
    else:
        return 40


# ============================================================
# POST /vehiculos   →  Registrar un nuevo vehículo
# ============================================================
@app.route("/vehiculos", methods=["POST"])
def crear_vehiculo():
    datos = request.get_json()
    if not datos:
        return jsonify({"error": "Cuerpo de solicitud JSON no proporcionado"}), 400

    # Validar campos obligatorios
    campos = ["vehiculo", "categoria", "peso_toneladas", "descripcion"]
    for c in campos:
        if c not in datos:
            return jsonify({"error": f"Falta el campo obligatorio: {c}"}), 400

    # Verificar que no exista ya
    if vehiculos_col.find_one({"vehiculo": datos["vehiculo"]}):
        return jsonify({"error": "El vehículo ya existe"}), 409

    vehiculos_col.insert_one(datos)
    datos.pop("_id", None)

    # Invalidar caché de la lista general y de la clave individual
    cache.delete(LISTA_KEY)
    cache.delete(f"vehiculo:{datos['vehiculo']}")

    return jsonify({"mensaje": "Vehículo creado", "datos": datos}), 201


# ============================================================
# GET /vehiculos  →  Listar todos  (caché 120 seg)
# ============================================================
@app.route("/vehiculos", methods=["GET"])
def obtener_todos():
    en_cache = cache.get(LISTA_KEY)
    if en_cache:
        return jsonify({"origen": "redis", "datos": json.loads(en_cache)})

    lista = list(vehiculos_col.find({}, {"_id": 0}))
    cache.set(LISTA_KEY, json.dumps(lista, ensure_ascii=False), ex=120)
    return jsonify({"origen": "mongo", "datos": lista})


# ============================================================
# GET /vehiculos/<nombre>  →  Buscar uno
# Reglas de caché según especificación del taller:
#   1. Regla prioritaria: Si descripcion > 20 caracteres → NO almacenar en caché
#   2. Si descripcion <= 20 caracteres:
#        - Longitud del nombre <= 5 chars  → TTL = 15 s
#        - Longitud del nombre 6 a 10 chars → TTL = 20 s
#        - Longitud del nombre > 10 chars  → TTL = 40 s
# ============================================================
@app.route("/vehiculos/<nombre>", methods=["GET"])
def obtener_uno(nombre):
    clave = f"vehiculo:{nombre}"

    en_cache = cache.get(clave)
    if en_cache:
        return jsonify({"origen": "redis", "datos": json.loads(en_cache)})

    vehiculo = vehiculos_col.find_one({"vehiculo": nombre}, {"_id": 0})
    if not vehiculo:
        return jsonify({"error": "Vehículo no encontrado"}), 404

    # Regla prioritaria: descripcion > 20 chars → no almacenar en Redis
    descripcion = str(vehiculo.get("descripcion") or "")
    if len(descripcion) <= 20:
        nombre_real = str(vehiculo.get("vehiculo") or nombre)
        ttl = ttl_para(nombre_real)
        cache.set(clave, json.dumps(vehiculo, ensure_ascii=False), ex=ttl)

    return jsonify({"origen": "mongo", "datos": vehiculo})


# ============================================================
# PUT /vehiculos/<nombre>  →  Actualizar un vehículo
# ============================================================
@app.route("/vehiculos/<nombre>", methods=["PUT"])
def actualizar_vehiculo(nombre):
    datos = request.get_json()
    if not datos:
        return jsonify({"error": "Cuerpo de solicitud JSON no proporcionado"}), 400

    # Evitar modificar el _id de MongoDB
    datos.pop("_id", None)

    resultado = vehiculos_col.update_one(
        {"vehiculo": nombre},
        {"$set": datos}
    )

    if resultado.matched_count == 0:
        return jsonify({"error": "Vehículo no encontrado"}), 404

    # Invalidar caché individual y lista general
    cache.delete(f"vehiculo:{nombre}")
    if "vehiculo" in datos and datos["vehiculo"] != nombre:
        cache.delete(f"vehiculo:{datos['vehiculo']}")
    cache.delete(LISTA_KEY)

    nombre_actual = datos.get("vehiculo", nombre)
    actualizado = vehiculos_col.find_one({"vehiculo": nombre_actual}, {"_id": 0})
    return jsonify({"mensaje": "Vehículo actualizado", "datos": actualizado})


# ============================================================
# DELETE /vehiculos/<nombre>  →  Eliminar un vehículo
# ============================================================
@app.route("/vehiculos/<nombre>", methods=["DELETE"])
def eliminar_vehiculo(nombre):
    resultado = vehiculos_col.delete_one({"vehiculo": nombre})

    if resultado.deleted_count == 0:
        return jsonify({"error": "Vehículo no encontrado"}), 404

    # Invalidar caché individual y lista general
    cache.delete(f"vehiculo:{nombre}")
    cache.delete(LISTA_KEY)

    return jsonify({"mensaje": f"'{nombre}' eliminado correctamente"})


# ============================================================
# GET /debug/cache/<nombre>  →  Ver estado de caché Redis
# ============================================================
@app.route("/debug/cache/<nombre>", methods=["GET"])
def debug_cache(nombre):
    clave = f"vehiculo:{nombre}"
    ttl   = cache.ttl(clave)       # -2 = no existe, -1 = sin expiración, ≥0 = segundos restantes
    existe = ttl >= 0

    return jsonify({
        "clave":     clave,
        "en_cache":  existe,
        "ttl_segundos": ttl if existe else None
    })


# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True)
