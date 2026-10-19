import os
import sqlite3
from werkzeug.security import check_password_hash

ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "usuarios.db")
db = sqlite3.connect(ruta)
fila = db.execute(
    "SELECT password_hash FROM usuarios WHERE correo = ?", ("ana@correo.com",)
).fetchone()
db.close()

print("¿Contraseña vieja (Prueba123) sigue activa?:", check_password_hash(fila[0], "Prueba123"))
print("¿Contraseña nueva (Nueva1234) funciona?:   ", check_password_hash(fila[0], "Nueva1234"))