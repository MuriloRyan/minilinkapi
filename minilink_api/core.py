from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from sqlmodel import SQLModel, Session, create_engine
from datetime import datetime, timedelta, timezone
from typing import Annotated
import jwt
import os
import random
import string
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("DEV_SECRET")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

sqlite_file_name = "db.sqlite3"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

pwd = CryptContext(schemes=["bcrypt"], deprecated='auto')

def verify_password(plain_password: str, hashed_password: str | None) -> bool:
    if not hashed_password:
        return False
    return pwd.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd.hash(password)

def create_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})

    subject = data.get("username") or data.get("sub")
    if not subject:
        raise ValueError("create_token requires 'username' or 'sub' in data")
    to_encode.update({"username": subject, "sub": subject})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user_from_token(token: str):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    return username

def generate_minilink(length=6):
    base62_alphabet = string.digits + string.ascii_letters
    return ''.join(random.choices(base62_alphabet, k=length))
