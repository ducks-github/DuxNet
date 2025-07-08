from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from duxnet_store.models import User
import bcrypt
import uuid
from datetime import datetime
from typing import Optional

router = APIRouter()

# In-memory user storage (replace with DB in production)
users_db = {}

class UserRegisterRequest(BaseModel):
    username: str
    password: str
    email: Optional[str] = None

class UserLoginRequest(BaseModel):
    username: str
    password: str

@router.post("/users/register")
def register_user(req: UserRegisterRequest):
    if req.username in users_db:
        raise HTTPException(status_code=400, detail="Username already exists")
    password_hash = bcrypt.hashpw(req.password.encode(), bcrypt.gensalt()).decode()
    user = User(
        user_id=str(uuid.uuid4()),
        username=req.username,
        password_hash=password_hash,
        email=req.email,
        created_at=datetime.utcnow(),
        is_active=True,
    )
    users_db[req.username] = user
    return {"success": True, "user": user.to_dict()}

@router.post("/users/login")
def login_user(req: UserLoginRequest):
    user = users_db.get(req.username)
    if not user or not bcrypt.checkpw(req.password.encode(), user.password_hash.encode()):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return {"success": True, "user": user.to_dict()} 