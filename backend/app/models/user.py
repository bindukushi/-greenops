from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from enum import Enum


class Role(str, Enum):
    admin = "admin"
    analyst = "analyst"
    viewer = "viewer"


class UserRegister(BaseModel):
    name: str = Field(..., min_length=2, max_length=80)
    email: EmailStr
    password: str = Field(..., min_length=6)
    role: Role = Role.viewer


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: str
    name: str
    email: EmailStr
    role: Role


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
