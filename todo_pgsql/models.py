from pydantic import BaseModel

class Token(BaseModel):
    access_token: str
    token_type: str


class TaskCreate(BaseModel):
    tekst: str


class UserCreate(BaseModel):
    username: str
    password: str