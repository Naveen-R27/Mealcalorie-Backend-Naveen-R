from pydantic import BaseModel, Field

class CalorieRequest(BaseModel):
    dish_name: str = Field(..., min_length=2)
    servings: float = Field(..., gt=0)
