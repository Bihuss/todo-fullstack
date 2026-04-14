from datetime import datetime, timedelta, timezone

import os
from pathlib import Path
from dotenv import load_dotenv
import jwt
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from pwdlib import PasswordHash
import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi.middleware.cors import CORSMiddleware


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173","http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Token(BaseModel):
    access_token: str
    token_type: str


class TaskCreate(BaseModel):
    tekst: str


class UserCreate(BaseModel):
    username: str
    password: str

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

password_hash = PasswordHash.recommended()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", 5432)),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


def get_user(username: str):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, username, hashed_password, disabled
        FROM users
        WHERE username = %s;
        """,
        (username,)
    )

    row = cur.fetchone()

    cur.close()
    conn.close()

    if not row:
        return None

    return {
        "id": row[0],
        "username": row[1],
        "hashed_password": row[2],
        "disabled": row[3],
    }


def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user:
        return None
    if not verify_password(password, user["hashed_password"]):
        return None
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=15)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Nie można zweryfikować tokenu",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.InvalidTokenError:
        raise credentials_exception

    user = get_user(username)
    if user is None:
        raise credentials_exception

    return user

@app.post("/register")
def register(user: UserCreate):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    hashed_password = password_hash.hash(user.password)

    try:
        cur.execute(
            """
            INSERT INTO users (username, hashed_password, disabled)
            VALUES (%s, %s, %s)
            RETURNING id, username, disabled;
            """,
            (user.username, hashed_password, False)
        )

        new_user = cur.fetchone()
        conn.commit()

    except psycopg2.Error:
        conn.rollback()
        cur.close()
        conn.close()
        return {"error": "user already exists"}

    cur.close()
    conn.close()

    return new_user


@app.post("/token", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Zły login lub hasło",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]},
        expires_delta=access_token_expires,
    )

    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/")
def home():
    return {"message": "API działa"}


@app.get("/me")
def read_me(current_user: dict = Depends(get_current_user)):
    return current_user


@app.get("/tasks")
def get_tasks(current_user: dict = Depends(get_current_user)):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute(
        """
        SELECT id, tekst, zrobione, user_id
        FROM tasks
        WHERE user_id = %s
        ORDER BY id;
        """,
        (current_user["id"],)
    )

    tasks = cur.fetchall()

    cur.close()
    conn.close()

    return tasks


@app.post("/tasks")
def add_task(task: TaskCreate, current_user: dict = Depends(get_current_user)):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute(
        """
        INSERT INTO tasks (tekst, zrobione, user_id)
        VALUES (%s, %s, %s)
        RETURNING id, tekst, zrobione, user_id;
        """,
        (task.tekst, False, current_user["id"])
    )

    new_task = cur.fetchone()
    conn.commit()

    cur.close()
    conn.close()

    return new_task


@app.delete("/tasks/{task_id}")
def delete_task(task_id: int, current_user: dict = Depends(get_current_user)):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute(
        """
        DELETE FROM tasks
        WHERE id = %s AND user_id = %s
        RETURNING id;
        """,
        (task_id, current_user["id"])
    )

    deleted = cur.fetchone()
    conn.commit()

    cur.close()
    conn.close()

    if deleted:
        return {"status": "deleted"}

    return {"error": "not found"}


@app.put("/tasks/{task_id}")
def mark_done(task_id: int, current_user: dict = Depends(get_current_user)):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute(
        """
        UPDATE tasks
        SET zrobione = TRUE
        WHERE id = %s AND user_id = %s
        RETURNING id, tekst, zrobione, user_id;
        """,
        (task_id, current_user["id"])
    )

    updated = cur.fetchone()
    conn.commit()

    cur.close()
    conn.close()

    if updated:
        return updated

    return {"error": "not found"}