from fastapi import APIRouter, Depends, HTTPException, Header
from typing import Annotated
from sqlalchemy.orm import session
from sqlmodel import Session, select
import minilink_api.models as md
from minilink_api.core import (
    get_session,
    get_password_hash,
    generate_minilink,
    get_current_user_from_token,
    verify_password,
)
from fastapi.responses import RedirectResponse, Response
from fastapi.security import OAuth2PasswordBearer

router = APIRouter(prefix="/links", tags=["links"])
root_router = APIRouter(tags=["links-root"])  # router mounted at root for short links

SessionDep = Annotated[Session, Depends(get_session)]
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/token")


@router.post("/create")
def create_link(token: Annotated[str, Depends(oauth2_scheme)],
    link_post: md.LinkCreate,
    session: SessionDep):

    user_email = get_current_user_from_token(token)

    user_db = session.exec(select(md.User).where(md.User.email == user_email)).first()
    if not user_db:
        raise HTTPException(status_code=404, detail="User not found")
    
    if link_post.private and not link_post.secret:
        raise HTTPException(status_code=400, detail="Private links must have a secret")

    from uuid import uuid4

    reduced_url = generate_minilink()
    encrypted_secret = get_password_hash(link_post.secret) if link_post.secret else None

    final_link = md.Link(
        id = uuid4().hex,
        url = str(link_post.url),
        description = link_post.description,
        private = link_post.private,
        secret = encrypted_secret if link_post.secret else None,
        owner_id = user_db.id,
        reduced_url = reduced_url
    )

    session.add(final_link)
    session.commit()
    session.refresh(final_link)

    user_db.links = (user_db.links or 0) + 1
    session.add(user_db)

    session.commit()
    session.refresh(final_link)
    
    return {"message": "Link created successfully", "link": link_post}


@router.get("/{minilink}")
def get_link_by_minilink(minilink: str, session: SessionDep):
    query = session.exec(select(md.Link).where(md.Link.reduced_url == minilink)).first()

    if query:
        link_data = md.LinkPublic(
            url=str(query.url),
            description=query.description,
            reduced_url=query.reduced_url,
            private=query.private,
            clicks=query.clicks
        )

        return link_data
    
    raise HTTPException(status_code=404, detail="Link not found")


@root_router.get("/{minilink}")
def short_redirect(minilink: str | None, session: SessionDep,
    link_secret: Annotated[str | None, Header()] = None,
    redirect: bool = True
    ):
    query = session.exec(select(md.Link).where(md.Link.reduced_url == minilink)).first()

    if query:
        if query.private:
            if not link_secret:
                raise HTTPException(status_code=401, detail="This link is private. Please provide the secret to access it.")
            
            if not verify_password(link_secret, query.secret):
                raise HTTPException(status_code=403, detail="Invalid secret for this private link.")

        query.clicks = (query.clicks or 0) + 1
        session.add(query)
        session.commit()
        
        if redirect:
            return RedirectResponse(url=str(query.url))
        
        return {'minilink': query.reduced_url, 'url': str(query.url), 'description': query.description, 'clicks': query.clicks}

    raise HTTPException(status_code=404, detail="Link not found")

@root_router.delete('/{minilink}/delete')
def delete_link(minilink: str, session: SessionDep,
                token: Annotated[str, Depends(oauth2_scheme)]):
    
    user = get_current_user_from_token(token)

    user_query = session.exec(select(md.User).where(md.User.email == user)).first()
    link_query = session.exec(select(md.Link).where(md.Link.reduced_url == minilink)).first()

    if user_query and link_query:
        if user_query.id != link_query.owner_id:

            raise HTTPException(status_code=403, detail="You're not the owner of the link!")
        
        session.delete(link_query)
        session.commit()
        return Response(status_code=204)

    raise HTTPException(status_code=400, detail='User or Link not found')