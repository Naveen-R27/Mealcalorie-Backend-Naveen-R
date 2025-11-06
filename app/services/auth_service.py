from app.repositories.user_repo import UserRepository
from app.utils.security import hash_password, verify_password, create_access_token
import logging

class AuthService:
    logger = logging.getLogger("meal_calorie_app.AuthService")
    logger.setLevel(logging.INFO)

    def __init__(self, user_repo: UserRepository, logger: logging.Logger = logger):
        self.user_repo = user_repo
        self.logger = logger

    async def register(self, first_name, last_name, email, password):
        existing = await self.user_repo.get_by_email(email)
        if existing:
            raise ValueError("Email already registered")
        hashed = hash_password(password)
        user = await self.user_repo.create_user(first_name, last_name, email, hashed)
        self.logger.info("Registered new user: %s", email)
        return user

    async def login(self, email, password):
        user = await self.user_repo.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            self.logger.warning("Failed login attempt for user: %s", email)
            raise ValueError("Invalid credentials")
        token = create_access_token({"sub": str(user.id)})
        return token
