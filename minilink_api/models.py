from sqlmodel import Field, SQLModel, AutoString
from pydantic import HttpUrl

""" 
    SQLModels is the base class for all other ones 
    
    Field(index=True) tells SQLModel that it should create a SQL index for this column,
    that would allow faster lookups in the database when reading data filtered by this column.

    SQLModel will know that something declared as str will be a SQL column
    of type TEXT (or VARCHAR, depending on the database).

    https://fastapi.tiangolo.com/tutorial/sql-databases/#create-models
    
"""

from pydantic import EmailStr

class TokenData(SQLModel):
    username: str | None = Field()

class UserBase(SQLModel):
    username: str | None = Field(index=True)
    email: EmailStr | None = Field()

class UserCreate(UserBase):
    """
    username: str
    email: EmailStr
    """

    password: str

class User(UserBase, table=True):
    """
    This is the model that will be used to create the database table for users.
    """

    id: str = Field(default=False, primary_key=True)
    password: str
    links: int | None = Field()

class UserUpdate(UserBase):
    username: str | None = None
    password: str | None = None
    links: int | None = None

"""
    Link related models go here
"""

class LinkBase(SQLModel):
    url: HttpUrl | str = Field(sa_type=AutoString) 
    description: str | None = Field(default=None)
    reduced_url: str | None = Field(default=None)

class LinkCreate(SQLModel):
    url: HttpUrl
    description: str | None = None
    private: bool | None = False
    secret: str | None = None

class Link(LinkBase, table=True):
    """
    url: HttpUrl | str = Field(sa_type=AutoString) 
    description: str | None = Field(default=None)
    reduced_url: str | None = Field(default=None)

    """
    
    id: str = Field(primary_key=True)
    owner_id: str | None = Field(foreign_key="user.id")
    private: bool | None = Field(default=False)
    secret: str | None = Field(default=None)
    clicks: int = Field(default=0)

class LinkPublic(SQLModel):
    url: str
    description: str | None = Field(default=None)
    reduced_url: str | None = Field(default=None)
    private: bool | None = Field(default=False)
    clicks: int = Field(default=0)