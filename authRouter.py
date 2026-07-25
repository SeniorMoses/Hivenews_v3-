from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session
import bcrypt

from database import get_db
from models import User, RefreshToken
from schemas import Signup, TokenResponse, RefreshRequest, LogoutRequest
from auth import create_access_token, create_refresh_token

router = APIRouter(prefix="", tags=["Authentication"])

@router.post("/signup")
async def register(data: Signup, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == data.email).first()
    if existing_user:
        raise HTTPException(
        status_code=400,
         detail="Email already exists"
         )

    hashed = await run_in_threadpool(
        bcrypt.hashpw,
        data.password.encode(),
        bcrypt.gensalt()
    )

    new_user = User(
        username=data.username,
        role="user",
        email=data.email,
        password=hashed.decode()
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "Signup successfully 🎉"}

@router.post("/login", response_model=TokenResponse)
async def signin(
    data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == data.username).first()
    if not user:
        raise HTTPException(
        status_code=401, 
        detail="Invalid credentials"
        )

    password_valid = await run_in_threadpool(
        bcrypt.checkpw,
        data.password.encode(),
        user.password.encode()
    )
    if not password_valid:
        raise HTTPException(
        status_code=401,
        detail="Invalid credentials"
        )

    access_token = create_access_token({
        "id": user.id,
        "username": user.username,
        "role": user.role
    })
    refresh_token = create_refresh_token(user.id, db)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "message": "login succesful"
    }

@router.post("/refresh", response_model=TokenResponse)
async def refresh_access(
    req: RefreshRequest,
    db: Session = Depends(get_db)
):
    stored_token = db.query(RefreshToken).filter(
        RefreshToken.token == req.refresh_token,
        RefreshToken.revoked == False
    ).first()

    if not stored_token:
        raise HTTPException(
        status_code=401,
         detail="Invalid or revoked refresh token"
         )

    if stored_token.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
        status_code=401,
        detail = "Refresh token expired"
         )

    user = stored_token.user
    if not user:
        raise HTTPException(
        status_code=401, 
        detail="User not found"
        )

    new_access = create_access_token({
        "id": user.id,
        "username": user.username,
        "role": user.role
    })

    return {
        "access_token": new_access,
        "refresh_token": req.refresh_token,
        "token_type": "bearer"
    }

@router.post("/logout")
async def logout(
    req: LogoutRequest,
    db: Session = Depends(get_db)
):
    stored_token = db.query(RefreshToken).filter(
        RefreshToken.token == req.refresh_token
    ).first()

    if not stored_token:
        raise HTTPException(
        status_code=404, 
        detail="Refresh token not found"
        )

    stored_token.revoked = True
    db.commit()

    return {"message": "Logged out successfully"}
