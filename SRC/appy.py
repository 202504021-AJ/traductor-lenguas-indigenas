import os
from flask import Flask, render_template, request, redirect, url_for

# 1. Obtener el directorio actual donde vive este archivo (es decir, la carpeta 'SRC')
current_dir = os.path.dirname(os.path.abspath(__file__))

# 2. Apuntar directamente a la carpeta 'Templates' que está dentro de 'SRC'
template_dir = os.path.join(current_dir, 'Templates')

# Declaramos la variable de ejecución de la aplicación especificando la carpeta de plantillas
app = Flask(__name__, template_folder=template_dir)

# Rutas de la aplicación
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/registro')
def registro():
    return render_template('registro.html')

# Definimos el punto de entrada y el puerto de ejecución
if __name__ == '__main__':
    app.run(debug=True, port=4000)