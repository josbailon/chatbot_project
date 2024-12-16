import asyncio
from database import connect_db

async def test_proveedores():
    try:
        conn = await connect_db()
        print("¡Conexión a la base de datos exitosa!")
        
        # Consulta para obtener los proveedores
        rows = await conn.fetch("SELECT nombre, telefono, email FROM proveedores;")
        print("Proveedores:")
        for row in rows:
            print(f"- Nombre: {row['nombre']}, Teléfono: {row['telefono']}, Email: {row['email']}")
        
        await conn.close()
    except Exception as e:
        print("Error al conectar a la base de datos o ejecutar consulta:", e)

# Ejecutar la prueba
asyncio.run(test_proveedores())
