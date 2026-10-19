import os
import re
import sqlite3
from flask import (Flask, render_template, request, redirect,
                   url_for, session, flash)
from werkzeug.security import generate_password_hash

# 1. Obtener el directorio actual donde vive este archivo (es decir, la carpeta 'SRC')
current_dir = os.path.dirname(os.path.abspath(__file__))

# 2. Apuntar directamente a la carpeta 'Templates' que está dentro de 'SRC'
template_dir = os.path.join(current_dir, 'Templates')

# Declaramos la variable de ejecución de la aplicación especificando la carpeta de plantillas
app = Flask(__name__, template_folder=template_dir)

# Necesaria para session y flash (en producción, usa una variable de entorno)
app.secret_key = os.environ.get("SECRET_KEY", "cambia-esto-en-produccion")

DB_PATH = os.path.join(current_dir, "usuarios.db")
MAX_INTENTOS = 3


# ---------- Acceso a datos (ADAPTA esto a la BD/modelo real del equipo) ----------
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


# ---------- Validaciones ----------
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


# ---------- Rutas de la aplicación ----------
@app.route('/')
def home():
    return render_template('index.html')


# Paso 1: validar correo
@app.route("/recuperar", methods=["GET", "POST"])
def recuperar_correo():
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

    return render_template("recuperar_contrasena.html", paso=1)


# Paso 2: validar datos del usuario
@app.route("/recuperar/verificar", methods=["GET", "POST"])
def recuperar_datos():
    correo = session.get("rec_correo")
    if not correo:
        return redirect(url_for("recuperar_correo"))

    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip().lower()
        fecha = request.form.get("fecha_nacimiento", "").strip()
        usuario = buscar_usuario_por_correo(correo)

        # ADAPTA los campos al esquema real de la tabla de usuarios
        if (usuario["nombre"].strip().lower() == nombre
                and usuario["fecha_nacimiento"] == fecha):
            session["rec_verificado"] = True
            return redirect(url_for("recuperar_nueva"))

        session["rec_intentos"] = session.get("rec_intentos", 0) + 1
        if session["rec_intentos"] >= MAX_INTENTOS:
            reiniciar_flujo()
            flash("Demasiados intentos fallidos. Inicia el proceso de nuevo.", "error")
            return redirect(url_for("recuperar_correo"))
        flash("Los datos no coinciden. Intenta de nuevo.", "error")

    return render_template("recuperar_contrasena.html", paso=2)


# Paso 3: nueva contraseña
@app.route("/recuperar/nueva", methods=["GET", "POST"])
def recuperar_nueva():
    if not (session.get("rec_correo") and session.get("rec_verificado")):
        return redirect(url_for("recuperar_correo"))

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

    return render_template("recuperar_contrasena.html", paso=3)


# PLACEHOLDER: bórrala si tu equipo ya tiene (o crea) la ruta real de login
@app.route("/login")
def login():
    return "Pantalla de login (placeholder)"


# Definimos el punto de entrada y el puerto de ejecución
if __name__ == '__main__':
    app.run(debug=True, port=4000)