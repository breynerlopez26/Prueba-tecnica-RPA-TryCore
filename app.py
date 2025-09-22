from flask import Flask, request, jsonify
import sqlite3
from datetime import datetime, timezone
from flask import send_file
import openpyxl
import io

DB_NAME = "database.db"
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS empresas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nit TEXT,
        nombre TEXT,
        categoria TEXT,
        tipo_sociedad TEXT,
        tipo_organizacion TEXT,
        camara_comercio TEXT,
        numero_matricula TEXT,
        fecha_matricula TEXT,
        fecha_vigencia TEXT,
        estado_matricula TEXT,
        fecha_renovacion TEXT,
        ultimo_anio_renovado TEXT,
        fecha_actualizacion TEXT,
        raw_json TEXT,
        estado_transaccion TEXT NOT NULL DEFAULT 'PENDIENTE',
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT
    )
    """)
    conn.commit()
    conn.close()

@app.route("/process-data", methods=["POST"])
def process_data():
    if not request.is_json:
        return jsonify(error="JSON body required"), 400
    data = request.get_json()

    # Basic validation: at least nit or nombre
    nit = data.get("nit") or data.get("NIT") or data.get("Identificación")
    nombre = data.get("nombre") or data.get("Nombre")
    if not (nit or nombre):
        return jsonify(error="Se requiere NIT o nombre"), 400

    # Insert or upsert: if exists update raw_json and keep estado_transaccion
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, estado_transaccion FROM empresas WHERE nit=? OR nombre=?", (nit, nombre))
    row = cursor.fetchone()
    now = datetime.now(timezone.utc).isoformat()
    raw = str(data)
    try:
        if row:
            cursor.execute("""
                UPDATE empresas
                SET nit=?, nombre=?, categoria=?, tipo_sociedad=?, tipo_organizacion=?, camara_comercio=?,
                    numero_matricula=?, fecha_matricula=?, fecha_vigencia=?, estado_matricula=?, fecha_renovacion=?,
                    ultimo_anio_renovado=?, fecha_actualizacion=?, raw_json=?, updated_at=?
                WHERE id=?
            """, (
                nit, nombre, data.get("Categoria de la Matrícula"), data.get("Tipo de Sociedad"),
                data.get("Tipo Organización"), data.get("Cámara de Comercio"), data.get("Número de Matrícula"),
                data.get("Fecha de Matrícula"), data.get("Fecha de Vigencia"), data.get("Estado de la matrícula"),
                data.get("Fecha de renovación"), data.get("Último año renovado"), data.get("Fecha de Actualización"),
                raw, now, row[0]
            ))
            conn.commit()
            conn.close()
            return jsonify(message="Registro actualizado", id=row[0], existing_state=row[1]), 200
        else:
            cursor.execute("""
                INSERT INTO empresas (nit, nombre, categoria, tipo_sociedad, tipo_organizacion, camara_comercio,
                numero_matricula, fecha_matricula, fecha_vigencia, estado_matricula, fecha_renovacion,
                ultimo_anio_renovado, fecha_actualizacion, raw_json, estado_transaccion, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'PENDIENTE', ?, ?)
            """, (
                nit, nombre, data.get("Categoria de la Matrícula"), data.get("Tipo de Sociedad"),
                data.get("Tipo Organización"), data.get("Cámara de Comercio"), data.get("Número de Matrícula"),
                data.get("Fecha de Matrícula"), data.get("Fecha de Vigencia"), data.get("Estado de la matrícula"),
                data.get("Fecha de renovación"), data.get("Último año renovado"), data.get("Fecha de Actualización"),
                raw, now, now
            ))
            conn.commit()
            new_id = cursor.lastrowid
            conn.close()
            return jsonify(message="Registro creado", id=new_id), 201
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify(error="DB error", detail=str(e)), 500

@app.route("/update-status", methods=["POST"])
def update_status():
    if not request.is_json:
        return jsonify(error="JSON body required"), 400
    data = request.get_json()
    nit = data.get("nit") or data.get("NIT") or data.get("Identificación") or data.get("nombre")
    estado = data.get("estado")
    if not nit or estado not in ["PENDIENTE", "PROCESADO", "ERROR"]:
        return jsonify(error="Datos inválidos"), 400
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    now = datetime.now(timezone.utc).isoformat()
    cursor.execute("UPDATE empresas SET estado_transaccion=?, updated_at=? WHERE nit=? OR nombre=?", (estado, now, nit, nit))
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    if affected==0:
        return jsonify(error="Registro no encontrado"), 404
    return jsonify(message="Estado actualizado", estado=estado), 200

@app.route("/empresas/estado/<estado>", methods=["GET"])
def get_empresas_por_estado(estado):
    estado = estado.upper()
    if estado not in ("PENDIENTE", "PROCESADO", "ERROR"):
        return jsonify(error="Estado inválido"), 400

    solo_nombres = request.args.get("solo_nombres", "false").lower() == "true"

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, nit, nombre, categoria, tipo_sociedad, tipo_organizacion,
               camara_comercio, numero_matricula, fecha_matricula, fecha_vigencia,
               estado_matricula, fecha_renovacion, ultimo_anio_renovado, fecha_actualizacion,
               estado_transaccion
        FROM empresas
        WHERE estado_transaccion=?
    """, (estado,))
    rows = cursor.fetchall()
    conn.close()

    if solo_nombres:
        # Solo devolver lista de nombres
        nombres = [r[2] for r in rows if r[2] is not None]
        return jsonify(nombres), 200

    # Devolver todo como antes
    empresas = [
        {
            "id": r[0],
            "nit": r[1],
            "nombre": r[2],
            "categoria": r[3],
            "tipo_sociedad": r[4],
            "tipo_organizacion": r[5],
            "camara_comercio": r[6],
            "numero_matricula": r[7],
            "fecha_matricula": r[8],
            "fecha_vigencia": r[9],
            "estado_matricula": r[10],
            "fecha_renovacion": r[11],
            "ultimo_anio_renovado": r[12],
            "fecha_actualizacion": r[13],
            "estado_transaccion": r[14]
        }
        for r in rows
    ]
    return jsonify(empresas), 200

@app.route("/reporte", methods=["GET"])
def reporte():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT nit, nombre, categoria, tipo_sociedad, tipo_organizacion,
               camara_comercio, numero_matricula, fecha_matricula, fecha_vigencia,
               estado_matricula, ultimo_anio_renovado, fecha_actualizacion, estado_transaccion
        FROM empresas
    """)
    rows = cursor.fetchall()
    conn.close()

    # Crear Excel en memoria
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Reporte Empresas"

    # Encabezados
    headers = [
        "NIT", "Nombre", "Categoría", "Tipo Sociedad", "Tipo Organización",
        "Cámara Comercio", "Número Matrícula", "Fecha Matrícula", "Fecha Vigencia",
        "Estado Matrícula", "Último Año Renovado", "Fecha Actualización", "Estado Transacción"
    ]
    ws.append(headers)

    # Datos
    for r in rows:
        ws.append(r)

    # Guardar en memoria
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    return send_file(
        output,
        as_attachment=True,
        download_name="reporte_empresas.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


if __name__ == "__main__":
    init_db()
    app.run(debug=True)

