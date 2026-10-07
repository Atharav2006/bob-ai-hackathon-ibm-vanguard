import os
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import uvicorn

from . import models, schemas, auth
from .database import get_db

def add_auth_routes(app: FastAPI):
    @app.post("/api/token", response_model=auth.Token)
    def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
        user = db.query(models.User).filter(models.User.username == form_data.username).first()
        if not user or not auth.verify_password(form_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        access_token = auth.create_access_token(data={"sub": user.username})
        return {"access_token": access_token, "token_type": "bearer"}

    @app.post("/api/users/", response_model=schemas.UserOut)
    def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
        hashed_password = auth.get_password_hash(user.password)
        # Prevent privilege escalation from public registration
        safe_role = models.UserRole.RESPONDER # default safe role
        db_user = models.User(username=user.username, hashed_password=hashed_password, role=safe_role)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
