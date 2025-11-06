import pytest
from httpx import AsyncClient
from app.main import create_app

@pytest.mark.asyncio
async def test_invalid_servings():
    app = create_app()
    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp = await ac.post("/get-calories", json={"dish_name": "pasta", "servings": 0})
        assert resp.status_code == 400
