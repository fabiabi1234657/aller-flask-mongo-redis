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

# ============================================================
# POST /vehiculos   →  Registrar un nuevo vehículo
# ============================================================
@app.route("/vehiculos", methods=["POST"])
def crear_vehiculo():
    datos = request.get_json()

    # Validar campos obligatorios
    campos = ["vehiculo", "categoria", "peso_toneladas", "descripcion"]
    for c in campos:
        if c not in datos:
            return jsonify({"error": f"Falta el campo: {c}"}), 400

    # Verificar que no exista ya
    if vehiculos_col.find_one({"vehiculo": datos["vehiculo"]}):
        return jsonify({"error": "El vehículo ya existe"}), 409

    vehiculos_col.insert_one(datos)
    datos.pop("_id", None)

    # Invalidar caché de la lista general
    cache.delete("todos_vehiculos")

    return jsonify({"mensaje": "Vehículo creado", "datos": datos}), 201


# ============================================================
# GET /vehiculos           →  Listar todos  (caché 120 seg)
# GET /vehiculos/<nombre>  →  Buscar uno    (caché  60 seg)
# ============================================================
@app.route("/vehiculos", methods=["GET"])
def obtener_todos():
    if (en_cache := cache.get("todos_vehiculos")):
        return jsonify({"origen": "redis", "datos": eval(en_cache)})

    lista = list(vehiculos_col.find({}, {"_id": 0}))
    cache.set("todos_vehiculos", str(lista), ex=120)   # 2 minutos
    return jsonify({"origen": "mongo", "datos": lista})


@app.route("/vehiculos/<nombre>", methods=["GET"])
def obtener_uno(nombre):
    clave = f"vehiculo:{nombre}"
    if (en_cache := cache.get(clave)):
        return jsonify({"origen": "redis", "datos": eval(en_cache)})

    vehiculo = vehiculos_col.find_one({"vehiculo": nombre}, {"_id": 0})
    if not vehiculo:
        return jsonify({"error": "Vehículo no encontrado"}), 404

    cache.set(clave, str(vehiculo), ex=60)             # 1 minuto
    return jsonify({"origen": "mongo", "datos": vehiculo})


# ============================================================
# PUT /vehiculos/<nombre>  →  Actualizar un vehículo
# ============================================================
@app.route("/vehiculos/<nombre>", methods=["PUT"])
def actualizar_vehiculo(nombre):
    datos = request.get_json()

    resultado = vehiculos_col.update_one(
        {"vehiculo": nombre},
        {"$set": datos}
    )

    if resultado.matched_count == 0:
        return jsonify({"error": "Vehículo no encontrado"}), 404

    # Limpiar caché del vehículo y de la lista
    cache.delete(f"vehiculo:{nombre}")
    cache.delete("todos_vehiculos")

    actualizado = vehiculos_col.find_one({"vehiculo": nombre}, {"_id": 0})
    return jsonify({"mensaje": "Vehículo actualizado", "datos": actualizado})


# ============================================================
# DELETE /vehiculos/<nombre>  →  Eliminar un vehículo
# ============================================================
@app.route("/vehiculos/<nombre>", methods=["DELETE"])
def eliminar_vehiculo(nombre):
    resultado = vehiculos_col.delete_one({"vehiculo": nombre})

    if resultado.deleted_count == 0:
        return jsonify({"error": "Vehículo no encontrado"}), 404

    # Limpiar caché
    cache.delete(f"vehiculo:{nombre}")
    cache.delete("todos_vehiculos")

    return jsonify({"mensaje": f"'{nombre}' eliminado correctamente"})


# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True)
