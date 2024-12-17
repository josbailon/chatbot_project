from fastapi import APIRouter
from pydantic import BaseModel
from database import db
from unidecode import unidecode
import re

router = APIRouter(prefix="/api")

class Message(BaseModel):
    user: str
    message: str

# Almacenamiento del carrito por usuario
user_carts = {}

# Función para normalizar texto
def normalize_text(text: str) -> str:
    return unidecode(text.lower().replace(",", "").replace(".", "").strip())

# Extraer la intención y nombre del producto
def extract_product_name(msg: str, triggers: list) -> str:
    clean_msg = re.sub(r"\b(el|la|de|del|los|las|un|una|quiero|cuanto cuesta|cuesta|agrega|añadir|comprar)\b", "", msg)
    for trigger in triggers:
        clean_msg = clean_msg.replace(trigger, "")
    return clean_msg.strip()

# Buscar productos por nombre
async def search_product_by_name(product_name):
    query = """
        SELECT p.id, p.nombre, p.descripcion, p.precio, m.simbolo
        FROM productos p
        JOIN monedas m ON p.moneda_id = m.id
        WHERE LOWER(p.nombre) ILIKE $1;
    """
    return await db.fetch(query, f"%{product_name}%")

# Buscar productos similares
async def suggest_similar_products():
    query = "SELECT nombre, precio FROM productos LIMIT 3;"
    return await db.fetch(query)

# Obtener productos por categoría
async def get_products_by_category(category):
    query = """
        SELECT p.nombre, p.descripcion, p.precio, m.simbolo
        FROM productos p
        JOIN categorias c ON p.categoria_id = c.id
        JOIN monedas m ON p.moneda_id = m.id
        WHERE LOWER(c.nombre) ILIKE $1
        LIMIT 3;
    """
    return await db.fetch(query, f"%{category}%")

# Obtener producto por precio
async def get_product_by_price(order):
    query = f"SELECT nombre, precio FROM productos ORDER BY precio {order} LIMIT 1;"
    return await db.fetchrow(query)

# Añadir producto al carrito
def add_to_cart(user, product_name):
    user_carts.setdefault(user, []).append(product_name)
    return f"✅ {product_name} ha sido añadido a tu carrito."

# Ver carrito
def view_cart(user):
    cart = user_carts.get(user, [])
    return "🛒 Tu carrito está vacío." if not cart else "🛒 Tu carrito:\n" + "\n".join(cart)

# Lógica principal del chatbot
async def handle_message(user: str, message: str):
    msg = normalize_text(message)
    response = ""

    categorias = {
        "cerveza": "cervezas",
        "whisky": "whiskys",
        "vino": "vinos",
        "licor": "licores",
        "tequila": "tequilas",
        "ron": "rones"
    }

    try:
        # Recomendar productos
        if "recomienda" in msg or "recomiendame" in msg:
            categoria = next((cat for cat in categorias if cat in msg), None)
            if categoria:
                rows = await get_products_by_category(categorias[categoria])
                if rows:
                    response = f"🍻 Aquí tienes algunos {categoria}s recomendados:\n" + "\n".join(
                        [f"{r['nombre']}: {r['descripcion']} ({r['simbolo']}{r['precio']})" for r in rows]
                    )
                else:
                    response = f"😔 No encontré {categoria}s. Prueba con otra categoría."
            else:
                response = "🔍 ¿Qué tipo de bebida buscas? Puedo recomendar cervezas, whiskys, vinos, y más."

        # Preguntas sobre precios
        elif "cuesta" in msg or "precio" in msg:
            product_name = extract_product_name(msg, ["cuanto", "precio"])
            rows = await search_product_by_name(product_name)
            if rows:
                response = f"💰 {rows[0]['nombre']}: ${rows[0]['precio']}"
            else:
                response = f"❌ No encontré '{product_name}'. ¿Quisiste decir algo más? Aquí algunas sugerencias:"
                suggestions = await suggest_similar_products()
                response += "\n" + "\n".join([f"- {r['nombre']}: ${r['precio']}" for r in suggestions])

        # Añadir productos al carrito
        elif "comprar" in msg or "agrega" in msg or "añadir" in msg:
            product_name = extract_product_name(msg, ["comprar", "agrega", "añadir"])
            rows = await search_product_by_name(product_name)
            if rows:
                response = add_to_cart(user, rows[0]['nombre'])
            else:
                response = f"❌ No pude encontrar '{product_name}'. Prueba con otro producto."

        # Ver el carrito
        elif "ver carrito" in msg:
            response = view_cart(user)

        # Bebida más económica
        elif "economica" in msg or "barata" in msg:
            row = await get_product_by_price("ASC")
            response = f"💸 La bebida más económica es: {row['nombre']} - ${row['precio']}"

        # Bebida más popular
        elif "popular" in msg or "cara" in msg:
            row = await get_product_by_price("DESC")
            response = f"🌟 La bebida más popular (más cara) es: {row['nombre']} - ${row['precio']}"

        # Respuesta por defecto
        else:
            response = (
                "🤔 No entiendo tu mensaje. Prueba con:\n"
                "- Recomiéndame una cerveza/vino/etc.\n"
                "- ¿Cuál es la bebida más económica?\n"
                "- ¿Cuál es la bebida más popular?\n"
                "- ¿Cuánto cuesta [producto]?\n"
                "- Comprar [producto]\n"
                "- Ver carrito"
            )

    except Exception as e:
        response = f"❗ Lo siento, ocurrió un error inesperado: {str(e)}"

    return response

@router.post("/chat")
async def chat(message: Message):
    response = await handle_message(message.user, message.message)
    return {"response": response}
