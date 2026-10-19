import os
import sqlite3
from werkzeug.security import generate_password_hash

ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "usuarios.db")
db = sqlite3.connect(ruta)

db.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY,
        nombre TEXT,
        correo TEXT UNIQUE,
        fecha_nacimiento TEXT,
        password_hash TEXT
    )
""")

db.execute(
    "INSERT OR IGNORE INTO usuarios (nombre, correo, fecha_nacimiento, password_hash) "
    "VALUES (?, ?, ?, ?)",
    ("Ana López", "ana@correo.com", "1998-05-12", generate_password_hash("Prueba123")),
)
db.commit()
db.close()
print("Usuario de prueba creado.")