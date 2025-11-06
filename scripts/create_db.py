# Creates database tables using SQLAlchemy metadata. Works with SQLite or Postgres (async).
import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from app.db import Base
from app.config import settings

async def run():
    db_url = settings.DATABASE_URL
    print("Creating tables using:", db_url)
    engine = create_async_engine(db_url, future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
    print("Done.")

if __name__ == '__main__':
    asyncio.run(run())
