from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated
from sqlmodel import Session, select
import minilink_api.models as md
from minilink_api.core import get_session, get_password_hash, create_token, verify_password
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter(prefix="/users", tags=["users"])

SessionDep = Annotated[Session, Depends(get_session)]


@router.post("/create")
def create_user(user_post: md.UserCreate, session: SessionDep):
    query = session.exec(select(md.User).where(md.User.email == user_post.email)).first()

    if not query:
        from uuid import uuid4

        final_user = md.User(username=user_post.username,
                    email = user_post.email,
                    password = get_password_hash(user_post.password),
                    id = uuid4().hex,
                    links = 0)
        
        session.add(final_user)
        session.commit()
        session.refresh(final_user)
        return final_user

    raise HTTPException(status_code=409, detail=f"A user already exists with E-mail {user_post.email}.")


@router.post("/token")
def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], session: SessionDep):
    user = session.exec(
        select(md.User).where(md.User.email == form_data.username)
    ).first()
    
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=401,
            detail="E-mail or password is incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token = create_token(data={"sub": user.email})
    
    return {"access_token": access_token, "token_type": "bearer"}
