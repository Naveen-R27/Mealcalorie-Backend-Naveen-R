from pydantic import BaseModel, EmailStr, constr

class UserCreate(BaseModel):
    first_name: str
    last_name: str | None = None
    email: EmailStr
    password: constr(min_length=8)

class UserOut(BaseModel):
    id: int
    first_name: str
    last_name: str | None
    email: EmailStr

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user : UserOut

class LoginInuser(BaseModel):
    email: EmailStr
    password: constr(min_length=8)
