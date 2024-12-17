from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from routers import chatbot
from database import db

app = FastAPI()

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar el pool de conexiones al arrancar el servidor
@app.on_event("startup")
async def startup_event():
    await db.initialize()

# Montar la carpeta static para servir archivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")

# Incluir las rutas del chatbot
app.include_router(chatbot.router)

@app.get("/")
async def root():
    return {"message": "Servidor del chatbot funcionando"}
