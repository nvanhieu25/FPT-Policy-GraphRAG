"""
app/api/routes/auth.py

Authentication endpoints: register, login (token), get current user.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import hash_password, verify_password, create_access_token, get_current_user
from app.db.session import get_db
from app.schemas.auth import UserCreate, UserResponse, TokenResponse
from app.services.user_service import get_user_by_email, get_user_by_username, create_user

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=201, summary="Register a new user")
async def register(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    if await get_user_by_email(db, payload.email):
        raise HTTPException(status_code=409, detail="Email already registered")
    if await get_user_by_username(db, payload.username):
        raise HTTPException(status_code=409, detail="Username already taken")
    user = await create_user(db, payload.email, payload.username, hash_password(payload.password))
    logger.info("[Auth] Registered user: %s", user.email)
    return user


@router.post("/token", response_model=TokenResponse, summary="Login and get access token")
async def login(form: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    user = await get_user_by_email(db, form.username)
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token({"sub": user.id})
    logger.info("[Auth] Login successful: %s", user.email)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse, summary="Get current user")
async def get_me(current_user=Depends(get_current_user)):
    return current_user
