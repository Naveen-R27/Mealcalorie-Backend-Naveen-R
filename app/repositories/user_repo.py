from sqlalchemy import select
from app.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession

class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_email(self, email: str):
        q = select(User).where(User.email == email)
        r = await self.session.execute(q)
        return r.scalars().first()

    async def create_user(self, first_name, last_name, email, hashed_password):
        user = User(first_name=first_name, last_name=last_name, email=email, hashed_password=hashed_password)
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user
