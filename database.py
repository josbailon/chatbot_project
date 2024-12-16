import asyncpg

# Configuración de la base de datos
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "user": "postgres",
    "password": "12345",  # Asegúrate de que la contraseña sea la correcta
    "database": "licoreria_db",
}

# Crear una conexión a la base de datos
async def connect_db():
    try:
        return await asyncpg.connect(**DB_CONFIG)
    except Exception as e:
        print(f"Error al conectar a la base de datos: {e}")
        raise
