from fastapi import APIRouter
from pydantic import BaseModel
from database import connect_db
from rapidfuzz import process

router = APIRouter()

# Modelo para entrada de mensajes
class Message(BaseModel):
    message: str

# Contexto del usuario
user_context = {}

# Función para limpiar mensajes
def clean_message(message: str):
    stopwords = ["la", "el", "de", "una", "un", "tienes", "que", "qué", "quiero", "cuánto"]
    return " ".join([word for word in message.lower().split() if word not in stopwords])

# Lógica principal del chatbot
async def handle_user_message(message: str, user_id: str):
    conn = await connect_db()
    message = clean_message(message)

    try:
        user_context.setdefault(user_id, {})  # Crear contexto si no existe
        last_intent = user_context[user_id].get("last_intent")
        last_entity = user_context[user_id].get("last_entity")

        # Consultar precio
        if "precio" in message or "cuesta" in message:
            producto = message.split("precio")[-1].split("cuesta")[-1].strip()
            rows = await conn.fetch("""
                SELECT p.nombre, p.descripcion, p.precio, m.simbolo
                FROM productos p
                JOIN monedas m ON p.moneda_id = m.id
                WHERE LOWER(p.nombre) ILIKE $1 OR LOWER(p.descripcion) ILIKE $1;
            """, f"%{producto}%")
            if rows:
                response = "\n".join([f"{row['nombre']}: {row['descripcion']} ({row['simbolo']}{row['precio']})" for row in rows])
                user_context[user_id]["last_intent"] = "consultar precio"
                user_context[user_id]["last_entity"] = producto
            else:
                # Sugerir productos similares
                all_products = await conn.fetch("SELECT nombre FROM productos;")
                suggestions = process.extractOne(producto, [row['nombre'] for row in all_products])
                response = f"No se encontró el producto {producto}. ¿Quisiste decir: {suggestions[0]}?"

        # Consultar productos más baratos
        elif "más barato" in message:
            categoria = message.split("más barato")[-1].strip()
            rows = await conn.fetch("""
                SELECT p.nombre, p.descripcion, p.precio, m.simbolo
                FROM productos p
                JOIN categorias c ON p.categoria_id = c.id
                JOIN monedas m ON p.moneda_id = m.id
                WHERE LOWER(c.nombre) ILIKE $1
                ORDER BY p.precio ASC
                LIMIT 1;
            """, f"%{categoria}%")
            if rows:
                response = f"El producto más barato en la categoría {categoria} es:\n{rows[0]['nombre']}: {rows[0]['descripcion']} ({rows[0]['simbolo']}{rows[0]['precio']})"
            else:
                response = f"No encontré productos en la categoría {categoria}."

        # Consultar productos más vendidos
        elif "más vendido" in message or "popular" in message:
            categoria = message.split("más vendido")[-1].strip()
            rows = await conn.fetch("""
                SELECT p.nombre, p.descripcion, i.cantidad
                FROM productos p
                JOIN inventario i ON p.id = i.producto_id
                JOIN categorias c ON p.categoria_id = c.id
                WHERE LOWER(c.nombre) ILIKE $1
                ORDER BY i.cantidad DESC
                LIMIT 1;
            """, f"%{categoria}%")
            if rows:
                response = f"El producto más vendido en la categoría {categoria} es:\n{rows[0]['nombre']}: {rows[0]['descripcion']} (Cantidad en inventario: {rows[0]['cantidad']})"
            else:
                response = f"No encontré productos más vendidos en la categoría {categoria}."

        # Manejo de consultas ambiguas
        elif "y la" in message:
            if last_entity:
                new_product = message.split("y la")[-1].strip()
                response = await handle_user_message(f"precio {new_product}", user_id)
            else:
                response = "No entiendo tu mensaje. Por favor, sé más específico."

        # Consultar inventario
        elif "inventario" in message or "productos" in message:
            rows = await conn.fetch("""
                SELECT p.nombre, i.cantidad
                FROM inventario i
                JOIN productos p ON i.producto_id = p.id
                WHERE i.cantidad > 0;
            """)
            response = "Inventario disponible:\n" + "\n".join([f"{row['nombre']}: {row['cantidad']} unidades" for row in rows[:10]])

        # Mensaje genérico para entradas desconocidas
        else:
            response = "No entiendo tu mensaje. Intenta algo como:\n- Mostrar categorías\n- Consultar precio de un producto\n- Buscar productos más vendidos"

        return response
    finally:
        await conn.close()

# Endpoint principal
@router.post("/chat")
async def chat(message: Message):
    user_id = "default_user"  # Reemplazar por un identificador único en un entorno multiusuario
    response = await handle_user_message(message.message, user_id)
    return {"response": response}
