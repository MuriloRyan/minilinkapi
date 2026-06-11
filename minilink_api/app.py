from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import RedirectResponse
from sqlalchemy.util import deprecated
from sqlmodel import SQLModel,Session, create_engine, select, table
from typing import Annotated, final
from fastapi import Depends
import minilink_api.models as md
from passlib.context import CryptContext
from uuid import uuid4
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
import jwt
import os
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import random
import string


        

from fastapi import FastAPI
from minilink_api.core import create_db_and_tables

from minilink_api.routes import users as users_router
from minilink_api.routes import links as links_router

app = FastAPI()


@app.on_event("startup")
def on_startup():
    create_db_and_tables()

# include routers
app.include_router(users_router.router)
app.include_router(links_router.router)
app.include_router(links_router.root_router)