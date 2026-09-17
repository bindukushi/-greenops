from fastapi import APIRouter, HTTPException, Depends

from app.models.user import UserRegister, UserLogin, Token, UserOut
from app.database.db import users_collection
from app.core.security import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


def _to_user_out(doc: dict) -> UserOut:
    return UserOut(id=str(doc["_id"]), name=doc["name"], email=doc["email"], role=doc["role"])


@router.post("/register", response_model=Token, status_code=201)
def register(payload: UserRegister):
    if users_collection().find_one({"email": payload.email}):
        raise HTTPException(status_code=409, detail="An account with this email already exists")

    doc = {
        "name": payload.name,
        "email": payload.email,
        "password": hash_password(payload.password),
        "role": payload.role.value,
    }
    result = users_collection().insert_one(doc)
    doc["_id"] = result.inserted_id

    token = create_access_token({"sub": str(doc["_id"])})
    return Token(access_token=token, user=_to_user_out(doc))


@router.post("/login", response_model=Token)
def login(payload: UserLogin):
    user = users_collection().find_one({"email": payload.email})
    if not user or not verify_password(payload.password, user["password"]):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    token = create_access_token({"sub": str(user["_id"])})
    return Token(access_token=token, user=_to_user_out(user))


@router.get("/me", response_model=UserOut)
def me(current_user: dict = Depends(get_current_user)):
    return _to_user_out(current_user)
