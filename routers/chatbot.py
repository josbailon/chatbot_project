from fastapi import APIRouter
from pydantic import BaseModel
from database import connect_db
from rapidfuzz import process

router = APIRouter()

# Modelo para recibir mensajes del usuario
class Message(BaseModel):
    message: str

# Contexto del usuario para conversaciones simples
user_context = {}

# Limpieza de mensajes del usuario
def clean_message(message: str):
    stopwords = ["la", "el", "de", "una", "un", "tienes", "que", "qué", "quiero", "más"]
    return " ".join([word for word in message.lower().split() if word not in stopwords])

# Lógica principal del chatbot
async def handle_user_message(message: str, user_id: str):
    conn = await connect_db()
    message = clean_message(message)

    try:
        # Consultar precio de un producto
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
            else:
                response = f"No se encontró el producto: {producto}."

        # Recomendaciones
        elif "recomiéndame" in message or "recomendar" in message:
            categoria = message.split()[-1]
            rows = await conn.fetch("""
                SELECT p.nombre, p.descripcion, p.precio, m.simbolo
                FROM productos p
                JOIN categorias c ON p.categoria_id = c.id
                JOIN monedas m ON p.moneda_id = m.id
                WHERE LOWER(c.nombre) ILIKE $1
                LIMIT 3;
            """, f"%{categoria}%")
            if rows:
                response = "Te recomiendo:\n" + "\n".join(
                    [f"{row['nombre']}: {row['descripcion']} ({row['simbolo']}{row['precio']})" for row in rows]
                )
            else:
                response = f"No encontré recomendaciones en la categoría {categoria}."

        # Producto más barato
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
                response = f"El producto más barato en {categoria} es:\n{rows[0]['nombre']}: {rows[0]['descripcion']} ({rows[0]['simbolo']}{rows[0]['precio']})"
            else:
                response = f"No encontré productos en la categoría {categoria}."

        # Consulta genérica
        else:
            response = "No entiendo tu mensaje. Puedes preguntar cosas como:\n- Recomiéndame una cerveza\n- ¿Cuánto cuesta el Johnnie Walker?\n- ¿Cuál es el vino más barato?"

        return response

    finally:
        await conn.close()

# Ruta principal del chatbot
@router.post("/chat")
async def chat(message: Message):
    user_id = "default_user"  # Identificador único del usuario
    response = await handle_user_message(message.message, user_id)
    return {"response": response}
