import asyncio
from src.database import engine, Base

async def init_db():
    print("⏳ Connecting to Database...")
    async with engine.begin() as conn:
        # This checks your blueprints and creates any missing tables
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Success! Tables created.")

if __name__ == "__main__":
    asyncio.run(init_db())