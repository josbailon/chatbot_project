import asyncpg

class Database:
    def __init__(self):
        self.pool = None

    async def initialize(self):
        try:
            self.pool = await asyncpg.create_pool(
                host="localhost",
                port=5432,
                user="postgres",
                password="12345",
                database="licoreria_db",
                min_size=2,  # Mínimo de conexiones en el pool
                max_size=10  # Máximo de conexiones en el pool
            )
            print("¡Pool de conexiones inicializado correctamente!")
        except Exception as e:
            print(f"Error al inicializar el pool de conexiones: {e}")

    async def fetch(self, query, *args):
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)

    async def fetchrow(self, query, *args):
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args)

db = Database()
