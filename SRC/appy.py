import os
import re
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash

# 1. Obtener el directorio actual (carpeta 'SRC')
current_dir = os.path.dirname(os.path.abspath(__file__))

# 2. Apuntar a la carpeta 'Templates' respetando la mayúscula inicial
template_dir = os.path.join(current_dir, 'Templates')

app = Flask(__name__, template_folder=template_dir)
app.secret_key = os.environ.get("SECRET_KEY", "cambia-esto-en-produccion")

DB_PATH = os.path.join(current_dir, "usuarios.db")
MAX_INTENTOS = 3

# --- RUTA LOGIN / HOME ---
@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        correo = request.form.get('correo')
        contrasena = request.form.get('contrasena')

        return redirect(url_for('login'))
        
    return render_template('login.html')

# --- RUTA REGISTRO ---
@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        correo = request.form.get('correo')
        contrasena = request.form.get('contrasena')

        return redirect(url_for('login'))
        
    return render_template('registro.html')

@app.route('/recuperar', methods=['GET', 'POST'])
def recuperar():
    paso_actual = 1
    if request.method == 'POST':
        paso_actual = int(request.form.get('paso', 1)) + 1
        
    return render_template('recuperar.html', paso=paso_actual)

if __name__ == '__main__':
    app.run(debug=True, port=4000)