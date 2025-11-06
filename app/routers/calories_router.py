from fastapi import APIRouter, Depends, HTTPException, Request
from app.schemas.calorie import CalorieRequest
from app.services.calories_service import USDAClient, CaloriesService
from app.config import settings
from app.utils.cache import InMemoryCache
from app.utils.rate_limiter import RateLimiter

router = APIRouter(prefix="", tags=["calories"])

# placeholders that will be set in app startup
usda_client = None
cache_client = None

@router.post("/get-calories")
async def get_calories(payload: CalorieRequest, request: Request):
    ip = request.client.host if request.client else "anonymous"
    limiter = RateLimiter(cache_client)
    allowed = await limiter.is_allowed(ip)
    if not allowed:
        raise HTTPException(status_code=429, detail="Too many requests")

    cs = CaloriesService(usda_client, cache_client)
    try:
        res = await cs.get_calories(payload.dish_name, payload.servings)
    except LookupError:
        raise HTTPException(status_code=404, detail="Dish not found or calorie info missing")
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    return res
