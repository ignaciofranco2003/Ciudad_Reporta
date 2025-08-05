import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask import send_from_directory
from flask import current_app
import mysql.connector
from datetime import datetime
from flask_cors import CORS
from datetime import datetime
from werkzeug.utils import secure_filename
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
CORS(app)  # habilita CORS para todos los orígenes y rutas

# Ruta absoluta al directorio de imágenes
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'imagenes')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


load_dotenv()  # Carga variables del archivo .env

conn = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASS")
)

cursor = conn.cursor()

# Configuración del correo
EMAIL_CONFIG = {
    'smtp_server':os.getenv("SERVER"),
    'smtp_port': os.getenv("PORT"),
    'sender_email': os.getenv("SENDER"),
    'password': os.getenv("PASS")
}

#------------------------------------------- Init DB -----------------------------------------------
def init_db():
    cursor.execute("CREATE DATABASE IF NOT EXISTS ciudad_reporta")
    conn.database = "ciudad_reporta"

    cursor.execute("""
            CREATE TABLE IF NOT EXISTS categorias_problematicas (
                id_categoria_problematica INT AUTO_INCREMENT PRIMARY KEY,
                nombre_categoria VARCHAR(100) NOT NULL,
                estado_categoria BOOLEAN DEFAULT TRUE
            );
                    """)

    # Verificar si ya hay registros
    cursor.execute('SELECT COUNT(*) FROM categorias_problematicas')
    cantidad = cursor.fetchone()[0]

    if cantidad == 0:
        categorias = [
            "Alumbrado publico",
            "Calles y veredas",
            "Semaforos",
            "Basura y limpieza",
            "Cloacas y desagues",
            "Otros"
        ]

        for descripcion in categorias:
            cursor.execute("INSERT INTO categorias_problematicas (nombre_categoria) VALUES (%s)", (descripcion,))

    cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id_usuario INT AUTO_INCREMENT PRIMARY KEY,
                email VARCHAR(120) UNIQUE NOT NULL,
                rol VARCHAR(20) NOT NULL
            );
                """)

    cursor.execute("""
            CREATE TABLE IF NOT EXISTS admins (
                id_admin INT AUTO_INCREMENT PRIMARY KEY,
                id_usuario INT NOT NULL,
                password VARCHAR(20) NOT NULL,
                FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario)
            );
                """)

    cursor.execute("""
            CREATE TABLE IF NOT EXISTS reporte (
                id_reporte INT AUTO_INCREMENT PRIMARY KEY,
                fk_id_categoria INT NOT NULL,
                descripcion VARCHAR (255) NOT NULL,
                latitud FLOAT NOT NULL,
                longitud FLOAT NOT NULL,
                imagen_URL VARCHAR (50) NOT NULL,
                solucionada BOOLEAN DEFAULT FALSE,
                estado VARCHAR(20) DEFAULT 'activo',
                fecha DATETIME NOT NULL,
                fk_id_usuario INT,
                FOREIGN KEY (fk_id_usuario) REFERENCES usuarios(id_usuario),
                FOREIGN KEY (fk_id_categoria) REFERENCES categorias_problematicas(id_categoria_problematica)
            );
                    """)

    conn.commit()

#------------------------------------------- Registro y Login -----------------------------------------------
@app.route('/login', methods=['POST'])
def login_o_registrar():
    data = request.get_json()
    correo = data.get('correo')

    try:
        # Verificar si el usuario ya existe
        cursor.execute("SELECT id_usuario, rol FROM usuarios WHERE email = %s", (correo,))
        result = cursor.fetchone()

        if result:
            # Usuario ya registrado
            return jsonify({'id': result[0], 'rol': result[1]}), 200
        else:
            # Registrar nuevo usuario con rol por defecto
            cursor.execute("INSERT INTO usuarios (email, rol) VALUES (%s, %s)", (correo, 'usuario'))
            conn.commit()

            # Obtener el ID del nuevo usuario
            cursor.execute("SELECT id_usuario, rol FROM usuarios WHERE email = %s", (correo,))
            nuevo_usuario = cursor.fetchone()

            return jsonify({'id': nuevo_usuario[0], 'rol': nuevo_usuario[1]}), 201

    except Exception as e:
        print(f"[ERROR] {e}")
        return jsonify({'error': 'Error al iniciar sesion o registrar usuario'}), 500

@app.route('/admin/login', methods=['POST'])
def login_admin():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    try:
        # Verificar si es un usuario administrador
        cursor.execute("SELECT id_usuario, rol FROM usuarios WHERE email = %s AND rol = %s", (email,"administrador"))
        usuario = cursor.fetchone()

        if not usuario:
            return jsonify({'error': 'Credenciales invalidas'}), 404

        id_usuario = usuario[0]

        # Verificar contrasenia del admin
        cursor.execute("SELECT password FROM admins WHERE id_usuario = %s", (id_usuario,))
        resultado = cursor.fetchone()

        if not resultado:
            return jsonify({'error': 'Contrasenia no configurada para este administrador'}), 403

        contrasenia_guardada = resultado[0]

        if password == contrasenia_guardada:
            return jsonify({'id': id_usuario, 'rol': 'administrador'}), 200
        else:
            return jsonify({'error': 'Contrasenia incorrecta'}), 401

    except Exception as e:
        print(f"[ERROR] {e}")
        return jsonify({'error': 'Error al procesar login'}), 500

@app.route("/verificar_cuenta", methods=["POST"])
def verificar_cuenta():
    try:
        datos = request.get_json()
        email = datos.get("email")

        if not email:
            return jsonify({"error": "Falta el campo 'email'"}), 400

        cursor.execute("SELECT id_usuario FROM usuarios WHERE email = %s", (email,))
        resultado = cursor.fetchone()

        return jsonify({
            "registrado": resultado is not None
        })
    except Exception as e:
        return jsonify({"error": "Error en el servidor", "detalle": str(e)}), 500

#-------------------------------------------- Registro de problematicas ----------------------------------------------
@app.route('/reporte', methods=['POST'])
def crear_problematica():
    data = request.get_json()
    categoria_nombre = data.get('categoria') #STRING
    descripcion = data.get('descripcion') #STRING
    latitud = data.get('latitud') #FLOAT
    longitud = data.get('longitud') #FLOAT
    imagen_URL = data.get('imagen_URL') #STRING
    usuario_id = data.get('usuario_id') #INT

    fecha = datetime.now()

    solucionada = False #BOOLEAN, por defecto es false
    estado = "Activo" #STRING, por defecto es activo


    try:
        cursor.execute("SELECT id_categoria_problematica FROM categorias_problematicas WHERE nombre_categoria = %s",(categoria_nombre,))
        resultado = cursor.fetchone()

        if resultado:
            fk_id_categoria = resultado[0]
        else:
            return jsonify({'error': 'Categoria no encontrada'}), 400

        cursor.execute("INSERT INTO reporte (fk_id_categoria,descripcion, latitud, longitud, imagen_URL, solucionada, fk_id_usuario, estado, fecha) VALUES (%s, %s, %s, %s, %s, %s, %s, %s,%s)", (fk_id_categoria, descripcion, latitud, longitud, imagen_URL, solucionada, usuario_id, estado, fecha))
        conn.commit()
        return jsonify({'mensaje': 'reporte creado'}), 201
    except Exception as e:
        print(f"[ERROR] {e}")
        return jsonify({'error': 'No se pudo crear el reporte '}), 500

#-------------------------------------------- Listado problematicas solucionadas ----------------------------------------------
@app.route('/reportes_solucionados', methods=['GET'])
def listar_solucionadas():
    try:
        cursor.execute("""
            SELECT r.id_reporte, c.nombre_categoria, r.descripcion, 
                   r.latitud, r.longitud, r.imagen_URL, r.solucionada, 
                   r.fk_id_usuario, r.estado, r.fecha
            FROM reporte r
            JOIN categorias_problematicas c ON r.fk_id_categoria = c.id_categoria_problematica
            WHERE r.solucionada = TRUE
        """)
        
        resultados = cursor.fetchall()

        if not resultados:
            return jsonify({'mensaje': 'No hay reportes solucionados'}), 200

        columnas = [desc[0] for desc in cursor.description]
        reportes = [dict(zip(columnas, fila)) for fila in resultados]

        return jsonify(reportes), 200

    except Exception as e:
        print(f"[ERROR] {e}")
        return jsonify({'error': 'No se pudieron obtener los reportes'}), 500

#-------------------------------------------- Listado reportes por estado----------------------------------------------
@app.route('/reportes/<estado>', methods=['GET'])
def listar_por_estado(estado):
    try:
        cursor.execute("""
            SELECT r.id_reporte, c.nombre_categoria, r.descripcion, 
                   r.latitud, r.longitud, r.imagen_URL, r.solucionada, 
                   r.fk_id_usuario, r.estado
            FROM reporte r
            JOIN categorias_problematicas c ON r.fk_id_categoria = c.id_categoria_problematica
            WHERE r.estado = %s
        """, (estado,))
        
        resultados = cursor.fetchall()

        if not resultados:
            return jsonify({'mensaje': f'No hay reportes con el estado: {estado}'}), 204

        columnas = [desc[0] for desc in cursor.description]
        reportes = [dict(zip(columnas, fila)) for fila in resultados]

        return jsonify(reportes), 200

    except Exception as e:
        print(f"[ERROR] {e}")
        return jsonify({'error': 'No se pudieron obtener los reportes'}), 500

#-------------------------------------------- Listado reportes por usuario----------------------------------------------
@app.route('/reportes/<int:id_usuario>', methods=['GET'])
def listar_por_usuario(id_usuario):
    try:
        cursor.execute("""
            SELECT r.id_reporte, c.nombre_categoria, r.descripcion, 
                   r.latitud, r.longitud, r.imagen_URL, r.solucionada, 
                   r.estado
            FROM reporte r
            JOIN categorias_problematicas c ON r.fk_id_categoria = c.id_categoria_problematica
            WHERE r.fk_id_usuario = %s
        """, (id_usuario,))
        
        resultados = cursor.fetchall()

        if not resultados:
            return jsonify({'mensaje': f'No hay reportes con del usuario con id: {id_usuario}'}), 204

        columnas = [desc[0] for desc in cursor.description]
        reportes = [dict(zip(columnas, fila)) for fila in resultados]

        return jsonify(reportes), 200

    except Exception as e:
        print(f"[ERROR] {e}")
        return jsonify({'error': 'No se pudieron obtener los reportes'}), 500

#----------------------------- Listado reportes por usuario por estado------------------------------------- 
@app.route('/reportes/<int:id_usuario>/<estado>', methods=['GET'])
def listar_por_usuario_y_estado(id_usuario, estado):
    try:
        cursor.execute("""
            SELECT r.id_reporte, c.nombre_categoria, r.descripcion, 
                   r.latitud, r.longitud, r.imagen_URL, r.solucionada, 
                   r.estado
            FROM reporte r
            JOIN categorias_problematicas c ON r.fk_id_categoria = c.id_categoria_problematica
            WHERE r.fk_id_usuario = %s AND r.estado = %s
        """, (id_usuario, estado))

        resultados = cursor.fetchall()

        if not resultados:
            return jsonify({'mensaje': f'No hay reportes con estado: {estado}'}), 200

        columnas = [desc[0] for desc in cursor.description]
        reportes = [dict(zip(columnas, fila)) for fila in resultados]

        return jsonify({'reportes': reportes}), 200

    except Exception as e:
        print(f"[ERROR] {e}")
        return jsonify({'error': 'No se pudieron obtener los reportes'}), 500

#-------------------------------------------- Detalles de un reporte----------------------------------------------
@app.route('/detalles_reporte/<int:id_reporte>', methods=['GET'])
def detalle_reporte(id_reporte):
    try:
        cursor.execute("""
            SELECT c.nombre_categoria, r.descripcion, 
                   r.latitud, r.longitud, r.imagen_URL, r.solucionada, 
                   r.fk_id_usuario, r.estado
            FROM reporte r
            JOIN categorias_problematicas c ON r.fk_id_categoria = c.id_categoria_problematica
            WHERE r.id_reporte = %s
        """, (id_reporte,))
        
        resultado = cursor.fetchone()

        if not resultado:
            return jsonify({'mensaje': f'No hay reportes con la id: {id_reporte}'}), 404

        columnas = [desc[0] for desc in cursor.description]
        reporte = dict(zip(columnas, resultado))

        return jsonify(reporte), 200

    except Exception as e:
        print(f"[ERROR] {e}")
        return jsonify({'error': 'No se pudieron obtener los datos del reporte'}), 500

#-------------------------------------------- Actualizar reportes ----------------------------------------------
@app.route('/reportes/<int:id_reporte>', methods=['PUT'])
def actualizar_reporte_usuario(id_reporte):
    data = request.get_json()
    usuario_id = data.get('usuario_id')
    nueva_descripcion = data.get('descripcion')
    nueva_categoria_nombre = data.get('nombre_categoria')  # viene como texto

    try:
        # Verificamos que el usuario sea quien creó el reporte
        cursor.execute("SELECT fk_id_usuario FROM reporte WHERE id_reporte = %s", (id_reporte,))
        resultado = cursor.fetchone()

        if not resultado:
            return jsonify({'error': 'Reporte no encontrado'}), 404

        creador_id = resultado[0]

        if creador_id != usuario_id:
            return jsonify({'error': 'No tiene permiso para modificar este reporte'}), 403

        # Buscar ID de la nueva categoría
        cursor.execute("SELECT id_categoria_problematica FROM categorias_problematicas WHERE nombre_categoria = %s", (nueva_categoria_nombre,))
        categoria = cursor.fetchone()

        if not categoria:
            return jsonify({'error': 'Categoría no encontrada'}), 400

        id_categoria = categoria[0]

        # Actualizar el reporte
        cursor.execute("""
            UPDATE reporte 
            SET descripcion = %s, fk_id_categoria = %s 
            WHERE id_reporte = %s
        """, (nueva_descripcion, id_categoria, id_reporte))
        
        conn.commit()
        return jsonify({'mensaje': 'Reporte actualizado correctamente'}), 200

    except Exception as e:
        print(f"[ERROR] {e}")
        return jsonify({'error': 'No se pudo actualizar el reporte'}), 500

#-------------------------------------------- Eliminar de problematicas ----------------------------------------------
@app.route('/borrar_reporte/<int:id_reporte>/<int:id_usuario>', methods=['DELETE'])
def borrar_reporte(id_reporte, id_usuario):

    try:
        # Obtener usuario dueño del reporte y la ruta de la imagen
        cursor.execute("SELECT fk_id_usuario, imagen_URL FROM reporte WHERE id_reporte = %s", (id_reporte,))
        result = cursor.fetchone()

        if result:
            fk_usuario, ruta_imagen = result
            if fk_usuario == id_usuario:
                # Eliminar imagen física si existe
                if ruta_imagen:
                    # Construir ruta absoluta del archivo
                    path_imagen = os.path.join(current_app.root_path, ruta_imagen.lstrip('/'))
                    if os.path.exists(path_imagen):
                        os.remove(path_imagen)

                # Borrar el reporte en la base
                cursor.execute("DELETE FROM reporte WHERE id_reporte = %s", (id_reporte,))
                conn.commit()
                return jsonify({'mensaje': 'Reporte eliminado'}), 200
            else:
                return jsonify({'error': 'No tiene permiso para eliminar este reporte'}), 403
        else:
            return jsonify({'error': 'El reporte no existe'}), 404
    except Exception as e:
        print(f"[ERROR] {e}")
        return jsonify({'error': 'No se pudo eliminar el reporte'}), 500

#-------------------------------------------- Actualizar estados (admin y usuario) ----------------------------------------------
# Ruta para marcar como revisado
@app.route('/reportes/<int:id_reporte>/revisar', methods=['PUT'])
def marcar_como_revisado(id_reporte):
    data = request.get_json()
    id_admin = data.get('id_usuario')

    try:
        # Verificar si el usuario es administrador
        cursor.execute("SELECT rol FROM usuarios WHERE id_usuario = %s", (id_admin,))
        rol = cursor.fetchone()

        if rol and rol[0] == 'administrador':
            # Verificar estado actual del reporte y obtener email del usuario dueño del reporte
            cursor.execute("""
                SELECT r.estado, u.email 
                FROM reporte r
                JOIN usuarios u ON r.fk_id_usuario = u.id_usuario
                WHERE r.id_reporte = %s
            """, (id_reporte,))
            resultado = cursor.fetchone()

            if not resultado:
                return jsonify({'error': 'Reporte no encontrado'}), 404

            estado_actual, email_usuario = resultado

            if estado_actual == 'solucionado':
                return jsonify({'error': 'No se puede marcar como pendiente un reporte ya solucionado'}), 400

            # Actualizar estado a 'pendiente'
            cursor.execute("UPDATE reporte SET estado = 'Pendiente' WHERE id_reporte = %s", (id_reporte,))
            conn.commit()

            asunto = "Tu reporte ha sido marcado como pendiente"
            mensaje = """
                <html>
                <body style="font-family: Arial, sans-serif; color: #333;">
                    <div style="max-width: 600px; margin: auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
                    

                    <div style="text-align: center; margin-bottom: 20px; font-size: 32px; font-weight: bold; color: #d35400;">
                    <br/>
                    📍 Ciudad Reporta
                    </div>

                    <h2 style="color: #2c3e50;">🔔 Reporte actualizado</h2>

                    <p>Hola,</p>

                    <p><strong>Uno de tus reportes ha sido revisado</strong> y marcado como <strong style="color: #d35400;">pendiente</strong> por un administrador.</p>

                    <p>✔️ Si el reporte ya fue solucionado, por favor márcalo como <strong>'Solucionado'</strong>.</p>
                    <p>❗ Si el reporte continúa, seleccioná la opción <strong>'Persiste'</strong>.</p>

                    <p>Puedes ver tus reportes pendientes desde la app:</p>
                    <p><strong>Mis Reportes &gt; Pendientes</strong></p>

                    <br/>
                    <p style="font-size: 12px; color: #999;">Este es un mensaje automático. No respondas a este correo.</p>
                    </div>
                </body>
                </html>
            """
            enviar_correo(email_usuario, asunto, mensaje)

            return jsonify({'mensaje': 'Reporte marcado como pendiente y correo enviado'}), 200
        else:
            return jsonify({'error': 'No autorizado'}), 403

    except Exception as e:
        print(f"[ERROR] {e}")
        return jsonify({'error': 'Error al actualizar el estado'}), 500

@app.route('/reportes/<int:id_reporte>/finalizar', methods=['PUT'])
def finalizar_reporte(id_reporte):
    data = request.get_json()
    id_usuario = data.get('id_usuario')
    confirmacion = data.get('confirmacion')  # Se espera True o False

    if confirmacion is None:
        return jsonify({'error': 'Falta el campo "confirmacion"'}), 400

    try:
        cursor.execute("SELECT fk_id_usuario, estado FROM reporte WHERE id_reporte = %s", (id_reporte,))
        reporte = cursor.fetchone()

        if not reporte:
            return jsonify({'error': 'Reporte no encontrado'}), 404

        if reporte[0] != id_usuario:
            return jsonify({'error': 'No tiene permiso para actualizar este reporte'}), 403

        if reporte[1] != 'Pendiente':
            return jsonify({'error': 'Solo se puede finalizar un reporte pendiente'}), 400

        nuevo_estado = 'Solucionado' if confirmacion else 'Activo'

        cursor.execute("UPDATE reporte SET estado = %s WHERE id_reporte = %s", (nuevo_estado, id_reporte))
        cursor.execute("UPDATE reporte SET solucionada = %s WHERE id_reporte = %s", (confirmacion, id_reporte))
        conn.commit()

        return jsonify({'mensaje': f'Reporte marcado como {nuevo_estado}'}), 200

    except Exception as e:
        print(f"[ERROR] {e}")
        return jsonify({'error': 'Error al finalizar el reporte'}), 500

#-------------------------------------------- Obtener categorias ----------------------------------------------
@app.route('/categorias', methods=['GET'])
def obtener_categorias():
    try:
        cursor.execute("""
            SELECT id_categoria_problematica, nombre_categoria 
            FROM categorias_problematicas 
            WHERE estado_categoria = 1
        """)
        resultados = cursor.fetchall()

        categorias = [
            {'id': fila[0], 'nombre': fila[1]}
            for fila in resultados
        ]

        return jsonify(categorias), 200 

    except Exception as e:
        return jsonify({'error': 'Error al obtener categorías', 'detalles': str(e)}), 500

#--------------------------------------Procesamiento de imagenes -----------------------------------------
@app.route('/imagenes/<nombre>')
def servir_imagen(nombre):
    return send_from_directory('static/imagenes', nombre)

#-------------------------------------------- Index ----------------------------------------------
@app.route('/')
def panel_admin():
    return app.send_static_file('index.html')

#-------------------------------------------- Subir Imagenes ----------------------------------------------
@app.route('/subir-imagen', methods=['POST'])
def subir_imagen():
    if 'imagen' not in request.files:
        return jsonify({'error': 'No se recibió ninguna imagen'}), 400

    imagen = request.files['imagen']
    if imagen.filename == '':
        return jsonify({'error': 'Nombre de archivo vacío'}), 400

    nombre_seguro = secure_filename(imagen.filename)
    # Evita duplicados agregando timestamp
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    extension = os.path.splitext(nombre_seguro)[1]
    nuevo_nombre = f"img_{timestamp}{extension}"
    ruta_completa = os.path.join(UPLOAD_FOLDER, nuevo_nombre)
    imagen.save(ruta_completa)

    url = f"/static/imagenes/{nuevo_nombre}"
    return jsonify({'url': url}), 200

#-------------------------------------------- Enviar Emails ----------------------------------------------
# Función para enviar correo
def enviar_correo(destinatario, asunto, mensaje):
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_CONFIG['sender_email']
        msg['To'] = destinatario
        msg['Subject'] = asunto

        msg.attach(MIMEText(mensaje, 'html'))

        server = smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port'])
        server.starttls()
        server.login(EMAIL_CONFIG['sender_email'], EMAIL_CONFIG['password'])
        server.sendmail(EMAIL_CONFIG['sender_email'], destinatario, msg.as_string())
        server.quit()
        print(f"[INFO] Correo enviado a {destinatario}")
    except Exception as e:
        print(f"[ERROR] Fallo al enviar correo: {e}")

#-------------------------------------------- Alta categorias ----------------------------------------------
@app.route("/categorias", methods=["POST"])
def crear_categoria():
    data = request.get_json()
    nombre = data.get("nombre", "").strip()
    id_admin = data.get("id_usuario")

    if not nombre:
        return jsonify({"error": "El nombre es obligatorio."}), 400

    if not id_admin:
        return jsonify({"error": "El id de usuario es obligatorio."}), 400

    try:
        # Verificar si el usuario existe y es administrador
        cursor.execute("SELECT rol FROM usuarios WHERE id_usuario = %s", (id_admin,))
        resultado = cursor.fetchone()
        if not resultado:
            return jsonify({"error": "Usuario no encontrado."}), 404
        rol = resultado[0]
        if rol.lower() != "administrador":
            return jsonify({"error": "Acceso denegado. No es administrador."}), 403

    except Exception as e:
        print("Error al validar usuario:", e)
        return jsonify({"error": "Error interno al validar usuario."}), 500

    try:
        # Verificar existencia ignorando mayúsculas/minúsculas
        cursor.execute("""
            SELECT id_categoria_problematica FROM categorias_problematicas
            WHERE LOWER(nombre_categoria) = LOWER(%s)
        """, (nombre,))
        existe = cursor.fetchone()

        if existe:
            return jsonify({"error": "Ya existe una categoría con ese nombre."}), 409

        # Insertar si no existe
        cursor.execute("""
            INSERT INTO categorias_problematicas (nombre_categoria)
            VALUES (%s)
        """, (nombre,))
        conn.commit()

        return jsonify({"mensaje": "Categoría creada correctamente."}), 201

    except Exception as e:
        print("Error al crear categoría:", e)
        return jsonify({"error": "Error interno al crear la categoría."}), 500

#-------------------------------------------- baja categorias ----------------------------------------------
@app.route("/categorias/<int:id_usuario>/<int:id_categoria>", methods=["DELETE"])
def eliminar_categoria(id_usuario, id_categoria):
    try:
        # Aquí podés validar id_usuario (p.ej. verificar rol admin)
        cursor.execute("SELECT rol FROM usuarios WHERE id_usuario = %s", (id_usuario,))
        usuario = cursor.fetchone()
        if not usuario:
            return jsonify({"error": "Usuario no encontrado."}), 404
        if usuario[0].lower() != "administrador":
            return jsonify({"error": "Acceso denegado."}), 403

        # Verificar si la categoría existe
        cursor.execute("""
            SELECT nombre_categoria FROM categorias_problematicas
            WHERE id_categoria_problematica = %s
        """, (id_categoria,))
        categoria = cursor.fetchone()

        if not categoria:
            return jsonify({"error": "Categoría no encontrada."}), 404

        try:
            # Intentar eliminar la categoría
            cursor.execute("""
                DELETE FROM categorias_problematicas 
                WHERE id_categoria_problematica = %s
            """, (id_categoria,))
            conn.commit()
            return jsonify({"mensaje": "Categoría eliminada correctamente."}), 200

        except mysql.connector.IntegrityError as e:
            if e.errno == 1451:
                # Categoría en uso, reasignar a "Categoría eliminada"
                cursor.execute("""
                    SELECT id_categoria_problematica FROM categorias_problematicas
                    WHERE LOWER(nombre_categoria) = LOWER(%s)
                """, ("Categoría eliminada",))
                existente = cursor.fetchone()

                if existente:
                    id_eliminada = existente[0]
                else:
                    cursor.execute("""
                        INSERT INTO categorias_problematicas (nombre_categoria, estado_categoria)
                        VALUES (%s, %s)
                    """, ("Categoría eliminada", False))
                    conn.commit()
                    id_eliminada = cursor.lastrowid

                # Reasignar reportes
                cursor.execute("""
                    UPDATE reporte
                    SET fk_id_categoria = %s
                    WHERE fk_id_categoria = %s
                """, (id_eliminada, id_categoria))
                conn.commit()

                # Eliminar categoría original
                cursor.execute("""
                    DELETE FROM categorias_problematicas 
                    WHERE id_categoria_problematica = %s
                """, (id_categoria,))
                conn.commit()

                return jsonify({
                    "mensaje": "Categoría estaba en uso, pero fue reasignada y eliminada correctamente."
                }), 200
            else:
                print("Error:", e)
                return jsonify({"error": "Error al eliminar la categoría."}), 500

    except Exception as e:
        print("Error:", e)
        return jsonify({"error": "Error interno."}), 500

#-------------------------------------------- Main ----------------------------------------------
if __name__ == '__main__':
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5000)
