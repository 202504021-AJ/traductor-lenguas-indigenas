from conexion import conectarBd

conexion = conectarBd()

if conexion.is_connected():
    print("CONEXION EXITOSA")
    
    conexion.close()