import os
import re
import sqlite3
from flask import (Flask, render_template, request, redirect,
                    url_for, session, flash)
from werkzeug.security import generate_password_hash

# 1. Configuración de directorio y servidor
current_dir = os.path.dirname(os.path.abspath(__file__))
template_dir = os.path.join(current_dir, 'Templates')

app = Flask(__name__, template_folder=template_dir)
app.secret_key = os.environ.get("SECRET_KEY", "cambia-esto-en-produccion")

DB_PATH = os.path.join(current_dir, "usuarios.db")
MAX_INTENTOS = 3


# 2. Funciones auxiliares y Base de Datos SQLite
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def buscar_usuario_por_correo(correo):
    with get_db() as db:
        return db.execute(
            "SELECT * FROM usuarios WHERE correo = ?", (correo.lower(),)
        ).fetchone()


def actualizar_password(correo, password_hash):
    with get_db() as db:
        db.execute(
            "UPDATE usuarios SET password_hash = ? WHERE correo = ?",
            (password_hash, correo.lower()),
        )


def validar_password(pw):
    errores = []
    if len(pw) < 8:
        errores.append("Debe tener al menos 8 caracteres.")
    if not re.search(r"[A-Z]", pw):
        errores.append("Debe incluir una mayúscula.")
    if not re.search(r"[a-z]", pw):
        errores.append("Debe incluir una minúscula.")
    if not re.search(r"\d", pw):
        errores.append("Debe incluir un número.")
    return errores


def reiniciar_flujo():
    for k in ("rec_correo", "rec_verificado", "rec_intentos"):
        session.pop(k, None)


# 3. Rutas principales de la aplicación

# --- LOGIN / HOME ---
@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        correo = request.form.get('correo')
        contrasena = request.form.get('contrasena')
        # Lógica de verificación en BD cuando tu tabla esté lista
        return redirect(url_for('login'))

    return render_template('login.html')


# --- REGISTRO DE USUARIO ---
@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        correo = request.form.get('correo')
        contrasena = request.form.get('contrasena')
        # Lógica de inserción en BD cuando tu tabla esté lista
        return redirect(url_for('login'))

    return render_template('registro.html')


# --- RECUPERAR CONTRASEÑA (SISTEMA DE 3 PASOS) ---

# Paso 1: Validar correo
@app.route("/recuperar", methods=["GET", "POST"])
def recuperar():
    if request.method == "POST":
        correo = request.form.get("correo", "").strip().lower()

        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", correo):
            flash("Ingresa un correo con formato válido.", "error")
        elif not buscar_usuario_por_correo(correo):
            flash("No encontramos una cuenta con ese correo.", "error")
        else:
            reiniciar_flujo()
            session["rec_correo"] = correo
            session["rec_intentos"] = 0
            return redirect(url_for("recuperar_datos"))

    return render_template("recuperar.html", paso=1)


# Paso 2: Validar identidad (Nombre y fecha de nacimiento)
@app.route("/recuperar/verificar", methods=["GET", "POST"])
def recuperar_datos():
    correo = session.get("rec_correo")
    if not correo:
        return redirect(url_for("recuperar"))

    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip().lower()
        fecha = request.form.get("fecha_nacimiento", "").strip()
        usuario = buscar_usuario_por_correo(correo)

        if (usuario and usuario["nombre"].strip().lower() == nombre
                and usuario["fecha_nacimiento"] == fecha):
            session["rec_verificado"] = True
            return redirect(url_for("recuperar_nueva"))

        session["rec_intentos"] = session.get("rec_intentos", 0) + 1
        if session["rec_intentos"] >= MAX_INTENTOS:
            reiniciar_flujo()
            flash("Demasiados intentos fallidos. Inicia el proceso de nuevo.", "error")
            return redirect(url_for("recuperar"))

        flash("Los datos no coinciden. Intenta de nuevo.", "error")

    return render_template("recuperar.html", paso=2)


# Paso 3: Guardar la nueva contraseña
@app.route("/recuperar/nueva", methods=["GET", "POST"])
def recuperar_nueva():
    if not (session.get("rec_correo") and session.get("rec_verificado")):
        return redirect(url_for("recuperar"))

    if request.method == "POST":
        pw = request.form.get("password", "")
        pw2 = request.form.get("password2", "")

        errores = validar_password(pw)
        if pw != pw2:
            errores.append("Las contraseñas no coinciden.")

        if errores:
            for e in errores:
                flash(e, "error")
        else:
            actualizar_password(session["rec_correo"], generate_password_hash(pw))
            reiniciar_flujo()
            flash("¡Contraseña actualizada! Ya puedes iniciar sesión.", "ok")
            return redirect(url_for("login"))

    return render_template("recuperar.html", paso=3)


# 4. Arranque del servidor
if __name__ == '__main__':
    app.run(debug=True, port=4000)