import os
import pymysql   # 👈 use PyMySQL for MySQL
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

# Example: MySQL without password (XAMPP / WAMP typical)
DATABASE_URL = os.getenv(
    "DATABASE_URL"
)

# If your MySQL has a password (e.g. root123), set DATABASE_URL in .env like:
# DATABASE_URL=mysql+pymysql://root:root123@localhost:3306/flipr_app

engine = create_engine(DATABASE_URL)

app = FastAPI(title="Flipr API")


class ProjectOut(BaseModel):
    id: int
    image_url: str
    name: str
    description: str


class ClientOut(BaseModel):
    id: int
    image_url: str
    name: str
    description: str
    designation: str


@app.get("/")
def root():
    return {"message": "Flipr API running. Use /projects or /clients."}


@app.get("/projects", response_model=List[ProjectOut])
def get_projects():
    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT id, image_url, name, description FROM projects ORDER BY created_at DESC"
        ))
        rows = result.mappings().all()
        return [dict(row) for row in rows]


@app.get("/clients", response_model=List[ClientOut])
def get_clients():
    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT id, image_url, name, description, designation FROM clients ORDER BY created_at DESC"
        ))
        rows = result.mappings().all()
        return [dict(row) for row in rows]
