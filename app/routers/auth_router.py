from fastapi import APIRouter, Depends, HTTPException, Request
from app.schemas.auth import UserCreate, UserOut,Token,LoginInuser
from app.db import get_db
from app.repositories.user_repo import UserRepository
from app.services.auth_service import AuthService
from app.utils.rate_limiter import RateLimiter

router = APIRouter(prefix="/auth", tags=["auth"])

cache_client = None

@router.post("/register", response_model=UserOut, status_code=201)
async def register(payload: UserCreate, request: Request, db=Depends(get_db)):
    
    ip = request.client.host if request.client else "anonymous"
    limiter = RateLimiter(cache_client)
    allowed = await limiter.is_allowed(f"register:{ip}")
    if not allowed:
        raise HTTPException(status_code=429, detail="Too many requests - try later")

    repo = UserRepository(db)
    service = AuthService(repo)
    try:
        user = await service.register(payload.first_name, payload.last_name, payload.email, payload.password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return user

@router.post("/login", response_model=Token)
async def login(payload: LoginInuser, request: Request, db=Depends(get_db)):
    
    ip = request.client.host if request.client else "anonymous"
    limiter = RateLimiter(cache_client)
    allowed = await limiter.is_allowed(f"login:{ip}")
    if not allowed:
        raise HTTPException(status_code=429, detail="Too many requests - try later")

    repo = UserRepository(db)
    service = AuthService(repo)
    try:
        token = await service.login(payload.email, payload.password)
    except ValueError:

        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    user = await repo.get_by_email(payload.email)
    return {"access_token": token, "token_type": "bearer", "user": user}