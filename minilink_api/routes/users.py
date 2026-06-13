from fastapi import APIRouter, Depends, HTTPException, Header
from typing import Annotated
from sqlmodel import Session, select
import minilink_api.models as md
from minilink_api.core import get_session, get_password_hash, create_token, verify_password
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.security import OAuth2PasswordBearer

from minilink_api.core import (
    get_password_hash,
    get_current_user_from_token,
    verify_password,
)

router = APIRouter(prefix="/users", tags=["users"])

SessionDep = Annotated[Session, Depends(get_session)]
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/token")

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
        return md.userPublic(username=user_post.username, links = 0)

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

@router.post('/changepwd')
def change_pwd(token: Annotated[str, Depends(oauth2_scheme)],
                session: SessionDep,
                pwds_data: md.ChangePassword):
    user_email = get_current_user_from_token(token)

    user_query = session.exec(select(md.User).where(md.User.email == user_email)).first()
    
    if user_query:
        if verify_password(pwds_data.current_password, user_query.password):

            hashed_newpwd = get_password_hash(pwds_data.new_password)

            if verify_password(pwds_data.new_password, user_query.password):
                raise HTTPException(
                    status_code=400,
                    detail="New password can't be equal to your current password"
                )

            user_query.password = hashed_newpwd

            session.add(user_query)
            session.commit()
            session.refresh(user_query)

            return {'message': 'User password modified'}
        
        raise HTTPException(
            status_code=401,
            detail="Current password is incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )