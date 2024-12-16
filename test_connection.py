import asyncio
from database import connect_db

async def test_db():
    try:
        conn = await connect_db()
        print("¡Conexión a la base de datos exitosa!")
        rows = await conn.fetch("SELECT nombre FROM categorias;")
        print("Cervezas:", [row['nombre'] for row in rows])
        await conn.close()
    except Exception as e:
        print("Error al conectar a la base de datos o ejecutar consulta:", e)

# Ejecutar la prueba
asyncio.run(test_db())
