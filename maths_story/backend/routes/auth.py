"""Authentication routes — signup, login, Google OAuth, profile."""
from fastapi import APIRouter, HTTPException, Depends
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
import os
import logging

from db import db
from models import UserCreate, UserLogin, User, GoogleAuthRequest
from utils.auth import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])

GOOGLE_CLIENT_ID = os.environ.get("EMERGENT_GOOGLE_AUTH_CLIENT_ID", "")


@router.post("/signup")
async def signup(user_data: UserCreate):
    existing = await db.users.find_one({"email": user_data.email}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user = User(email=user_data.email, name=user_data.name, role="user")
    user_dict = user.model_dump()
    user_dict["password"] = hash_password(user_data.password)
    
    await db.users.insert_one(user_dict)
    
    token = create_access_token({"sub": user.id})
    return {"token": token, "user": user.model_dump()}


@router.post("/login")
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user or not verify_password(credentials.password, user.get("password", "")):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    user_obj = User(**{k: v for k, v in user.items() if k != "password"})
    token = create_access_token({"sub": user_obj.id})
    return {"token": token, "user": user_obj.model_dump()}


@router.post("/google")
async def google_auth(auth_request: GoogleAuthRequest):
    """Google OAuth sign-in / sign-up."""
    try:
        idinfo = id_token.verify_oauth2_token(
            auth_request.token,
            google_requests.Request(),
            GOOGLE_CLIENT_ID
        )
        email = idinfo["email"]
        name = idinfo.get("name", email.split("@")[0])

        existing = await db.users.find_one({"email": email}, {"_id": 0})
        if existing:
            user_obj = User(**{k: v for k, v in existing.items() if k != "password"})
        else:
            user_obj = User(email=email, name=name, role="user")
            user_dict = user_obj.model_dump()
            user_dict["password"] = ""  # No password for OAuth users
            await db.users.insert_one(user_dict)

        token = create_access_token({"sub": user_obj.id})
        return {"token": token, "user": user_obj.model_dump()}
    except ValueError as e:
        logging.error(f"Google OAuth error: {e}")
        raise HTTPException(status_code=401, detail="Invalid Google token")


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
