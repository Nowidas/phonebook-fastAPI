import os
from sqlalchemy import create_engine
from databases import Database

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL, echo=True)

from sqlalchemy import Column, Integer, String, Table, MetaData

metadata = MetaData()

Contact = Table(
    "Contacts",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String(256), nullable=False),
    Column("surname", String(256)),
    Column("phone", String(256), nullable=False),
    Column("email", String(256)),
)

User = Table(
    "Users",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("username", String, unique=True, index=True),
    Column("hashed_password", String),
)

database = Database(DATABASE_URL)
