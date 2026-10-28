import os
import re
from flask import (Flask, render_template, request, redirect,
                    url_for, session, flash)
from werkzeug.security import generate_password_hash, check_password_hash
import conexion as db

# 1. Configuración del directorio y la aplicación Flask
current_dir = os.path.dirname(os.path.abspath(__file__))
template_dir = os.path.join(current_dir, 'Templates')

app = Flask(__name__, template_folder=template_dir)
app.secret_key = os.environ.get("SECRET_KEY", "clave_secreta_raices")

MAX_INTENTOS = 3

# ---------- Funciones Auxiliares con MySQL ----------
def buscar_usuario_por_correo(correo):
    try:
        con = db.conectarBd()
        cursor = con.cursor(dictionary=True)
        cursor.execute("SELECT * FROM usuarios WHERE correo = %s", (correo.lower(),))
        usuario = cursor.fetchone()
        cursor.close()
        con.close()
        return usuario
    except Exception as e:
        print(f"Error al consultar BD: {e}")
        return None

def actualizar_password(correo, password_hash):
    try:
        con = db.conectarBd()
        cursor = con.cursor()
        cursor.execute(
            "UPDATE usuarios SET contrasena_hash = %s WHERE correo = %s",
            (password_hash, correo.lower())
        )
        con.commit()
        cursor.close()
        con.close()
    except Exception as e:
        print(f"Error al actualizar contraseña: {e}")

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


# ---------- Rutas Principales ----------

# --- INICIO DE SESIÓN (LOGIN) ---
@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        correo = request.form.get('correo', '').strip().lower()
        contrasena = request.form.get('contrasena', '').strip()

        usuario = buscar_usuario_por_correo(correo)
        if usuario and check_password_hash(usuario['contrasena_hash'], contrasena):
            session['usuario_id'] = usuario['id_usuario']
            session['usuario_nombre'] = usuario['nombre']
            flash(f"¡Bienvenido de nuevo, {usuario['nombre']}!", "ok")
            return redirect(url_for('principal'))
        else:
            flash("Correo o contraseña incorrectos.", "error")

    return render_template('login.html')


# --- PÁGINA PRINCIPAL (PANEL DE USUARIO AUTENTICADO) ---
@app.route('/principal')
def principal():
    if 'usuario_id' not in session:
        flash("Por favor, inicia sesión para acceder.", "error")
        return redirect(url_for('login'))

    return render_template('dasboard_principal.html')


# --- CERRAR SESIÓN ---
@app.route('/logout')
def logout():
    session.clear()
    flash("Has cerrado sesión correctamente.", "ok")
    return redirect(url_for('login'))


# --- REGISTRO DE USUARIO ---
@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        correo = request.form.get('correo', '').strip().lower()
        contrasena = request.form.get('contrasena', '').strip()

        # 1. Validar el formato del correo mediante Expresión Regular
        patron_correo = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(patron_correo, correo):
            flash("Ingresa un correo electrónico con un formato válido.", "error")
            return redirect(url_for('registro'))

        # 2. Validar si el correo ya existe en MySQL
        if buscar_usuario_por_correo(correo):
            flash("Este correo ya está registrado.", "error")
            return redirect(url_for('registro'))

        # 3. Generar el Hash seguro de la contraseña y guardar en MySQL
        pw_hash = generate_password_hash(contrasena)
        try:
            con = db.conectarBd()
            cursor = con.cursor()
            sql = "INSERT INTO usuarios (nombre, correo, contrasena_hash) VALUES (%s, %s, %s)"
            cursor.execute(sql, (nombre, correo, pw_hash))
            con.commit()
            cursor.close()
            con.close()

            flash("¡Cuenta creada exitosamente! Ahora puedes iniciar sesión.", "ok")
            return redirect(url_for('login'))
        except Exception as e:
            flash(f"Error al guardar el usuario: {e}", "error")
            return redirect(url_for('registro'))

    return render_template('registro.html')


# --- RECUPERACIÓN DE CONTRASEÑA EN 3 PASOS ---

# Paso 1: Validar correo
@app.route("/recuperar", methods=["GET", "POST"])
def recuperar():
    if request.method == "POST":
        correo = request.form.get("correo", "").strip().lower()

        if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", correo):
            flash("Ingresa un correo con formato válido.", "error")
        elif not buscar_usuario_por_correo(correo):
            flash("No encontramos una cuenta con ese correo.", "error")
        else:
            reiniciar_flujo()
            session["rec_correo"] = correo
            session["rec_intentos"] = 0
            return redirect(url_for("recuperar_datos"))

    return render_template("recuperar.html", paso=1)


# Paso 2: Validar identidad
@app.route("/recuperar/verificar", methods=["GET", "POST"])
def recuperar_datos():
    correo = session.get("rec_correo")
    if not correo:
        return redirect(url_for("recuperar"))

    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip().lower()
        usuario = buscar_usuario_por_correo(correo)

        if usuario and usuario["nombre"].strip().lower() == nombre:
            session["rec_verificado"] = True
            return redirect(url_for("recuperar_nueva"))

        session["rec_intentos"] = session.get("rec_intentos", 0) + 1
        if session["rec_intentos"] >= MAX_INTENTOS:
            reiniciar_flujo()
            flash("Demasiados intentos fallidos. Inicia el proceso de nuevo.", "error")
            return redirect(url_for("recuperar"))

        flash("Los datos no coinciden. Intenta de nuevo.", "error")

    return render_template("recuperar.html", paso=2)


# Paso 3: Guardar nueva contraseña
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


# ---------- Punto de entrada ----------
if __name__ == '__main__':
    app.run(debug=True, port=4000)