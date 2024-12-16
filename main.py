from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from routers import chatbot

# Crear la aplicación FastAPI
app = FastAPI()

# Habilitar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cambia "*" por dominios específicos si es necesario
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar los controladores
app.include_router(chatbot.router, prefix="/api")

# Montar la carpeta estática
app.mount("/static", StaticFiles(directory="static"), name="static")

# Ejecutar el servidor
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
