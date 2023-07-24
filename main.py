from typing import List, Annotated

from fastapi import FastAPI, status, HTTPException, APIRouter, Depends, Path, Query
from database import Base, engine, SessionLocal
from sqlalchemy.orm import Session
from sqlalchemy import select, Select, func
import models
import schemas
import secrets_keys

import secrets
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

Base.metadata.create_all(engine)

app = FastAPI()
router = APIRouter()
security = HTTPBasic()


def get_current_username(
    credentials: Annotated[HTTPBasicCredentials, Depends(security)]
):
    current_username_bytes = credentials.username.encode("utf8")
    correct_username_bytes = bytes(secrets_keys.USER, encoding="utf8")
    is_correct_username = secrets.compare_digest(
        current_username_bytes, correct_username_bytes
    )
    current_password_bytes = credentials.password.encode("utf8")
    correct_password_bytes = bytes(secrets_keys.PASSWORD, encoding="utf8")
    is_correct_password = secrets.compare_digest(
        current_password_bytes, correct_password_bytes
    )
    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def paginate(query: Select, limit: int, offset: int) -> dict:
    with SessionLocal() as session:
        return {
            "count": session.scalar(select(func.count()).select_from(query.subquery())),
            "items": [
                contact for contact in session.scalars(query.limit(limit).offset(offset))
            ],
        }


@router.get("/", response_model=schemas.PaginatedResponse[schemas.ContactDB])
async def read_contacts_list(
    username: Annotated[str, Depends(get_current_username)],
    limit: int = Query(100, ge=0, le=200),
    offset: int = Query(0, ge=0),
):
    return paginate(select(models.Contact), limit, offset)


@router.post("/", response_model=schemas.ContactDB, status_code=status.HTTP_201_CREATED)
async def create_contact(
    username: Annotated[str, Depends(get_current_username)],
    contact: schemas.ContactSchema,
    session: Session = Depends(get_session),
):
    contactdb = models.Contact(
        name=contact.name,
        surname=contact.surname,
        phone=contact.phone,
        email=contact.email,
    )

    session.add(contactdb)
    session.commit()
    session.refresh(contactdb)

    return contactdb


@router.get("/{contact_id}", response_model=schemas.ContactDB)
async def read_contact(
    username: Annotated[str, Depends(get_current_username)],
    contact_id: Annotated[int, Path(title="The ID of the item to get", ge=1)],
    session: Session = Depends(get_session),
):
    contact = session.query(models.Contact).get(contact_id)

    if not contact:
        raise HTTPException(
            status_code=404, detail=f"contact item with id {contact_id} not found"
        )

    return contact


@router.put("/{contacts_id}", response_model=schemas.ContactDB)
async def create_contacts(
    username: Annotated[str, Depends(get_current_username)],
    contacts_id: Annotated[int, Path(title="The ID of the item to get", ge=1)],
    updated_contact: schemas.ContactSchema,
    session: Session = Depends(get_session),
):
    contact = session.query(models.Contact).get(contacts_id)

    if contact:
        contact.name = updated_contact.name
        contact.surname = updated_contact.surname
        contact.phone = updated_contact.phone
        contact.email = updated_contact.email
        session.commit()

    if not contact:
        raise HTTPException(
            status_code=404, detail=f"contact item with id {id} not found"
        )

    return contact


@router.delete("/{contacts_id}")
def delete_contact(
    username: Annotated[str, Depends(get_current_username)],
    contacts_id: Annotated[int, Path(title="The ID of the item to get", ge=1)],
    session: Session = Depends(get_session),
):
    contact = session.query(models.Contact).get(contacts_id)

    if contact:
        session.delete(contact)
        session.commit()
    else:
        raise HTTPException(
            status_code=404, detail=f"contact item with id {contacts_id} not found"
        )

    return "Done"


app.include_router(router, tags=["contats"], prefix="/contacts")


@app.get("/ping", response_model=schemas.WelcomeMsgSchema)
def root():
    return {"msg": "Welcome to PhoneBookAPI"}


@app.get("/users/me")
def read_current_user(username: Annotated[str, Depends(get_current_username)]):
    return {"username": username}
