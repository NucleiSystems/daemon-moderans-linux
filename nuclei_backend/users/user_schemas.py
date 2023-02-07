from pydantic import BaseModel


# `User` is a class that inherits from `UserBase` and has an `id`, `is_active` and `Config` class
class UserBase(BaseModel):
    email: str


class UserCreate(UserBase):
    password: str
    username: str


class User(UserBase):
    id: int
    is_active: bool

    class Config:
        orm_mode = True
