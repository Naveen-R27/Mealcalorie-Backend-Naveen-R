import logging
import os
import secrets
from fastapi import FastAPI
from app.routers import auth_router, calories_router
from app.config import settings
from app.services.calories_service import USDAClient
from app.utils.cache import InMemoryCache
from app.db import engine, Base
import asyncio
from redis import asyncio as aioredis


LOG_FILE = os.environ.get('LOG_FILE', 'logs/app.log')
os.makedirs(os.path.dirname(LOG_FILE) or '.', exist_ok=True)

logger = logging.getLogger("meal_calorie_app")
logger.setLevel(logging.INFO)
fmt = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')

ch = logging.StreamHandler()
ch.setFormatter(fmt)
logger.addHandler(ch)

try:
    from logging.handlers import RotatingFileHandler
    fh = RotatingFileHandler(LOG_FILE, maxBytes=5*1024*1024, backupCount=3)
    fh.setFormatter(fmt)
    logger.addHandler(fh)
except Exception as e:
    logger.warning("Could not create file handler for logging: %s", e)

def create_app():
    app = FastAPI(title="Meal Calorie Count")
    app.include_router(auth_router.router)
    app.include_router(calories_router.router)

    @app.on_event("startup")
    async def startup():
        
        if not settings.SECRET_KEY or settings.SECRET_KEY.strip().lower().startswith("change"):
            new_key = secrets.token_urlsafe(32)
            logger.warning("SECRET_KEY is not set securely. Generated a runtime secret key. For production, set SECRET_KEY in your .env.")
           
            settings.SECRET_KEY = new_key

        
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables ensured/created.")
        except Exception as e:
            logger.exception("Failed to create database tables: %s", e)
            raise

        
        cache = None
        if settings.REDIS_URL:
            try:
                cache = await aioredis.from_url(settings.REDIS_URL, decode_responses=True)
                logger.info("Connected to Redis at %s", settings.REDIS_URL)
            except Exception as e:
                logger.warning("Could not connect to Redis, falling back to in-memory cache: %s", e)
                cache = InMemoryCache()
        else:
            cache = InMemoryCache()
            logger.info("Using in-memory cache (REDIS_URL not provided).")

        usda = USDAClient(settings.USDA_API_KEY)
        import app.routers.calories_router as cr
        import app.routers.auth_router as ar
        cr.usda_client = usda
        cr.cache_client = cache
        ar.cache_client = cache
        app.state.cache = cache
        app.state.usda = usda

    @app.on_event("shutdown")
    async def shutdown():
        import app.routers.calories_router as cr
        if getattr(cr, 'usda_client', None):
            await cr.usda_client.close()
        if getattr(app.state, 'cache', None) and hasattr(app.state.cache, 'close'):
            try:
                await app.state.cache.close()
            except Exception:
                pass

    return app

app = create_app()
