import asyncio
from typing import Annotated, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, APIRouter, status, Path, Query, Depends, HTTPException
from sqlalchemy import func, select

from app.schemas import (
    WelcomeMsgSchema,
    ContactSchema,
    ContactDB,
    PaginatedResponse,
    UserSchema,
)
from app.database import engine, metadata, database, Contact

from app.auth import auth_router, init_user, get_current_user


@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.connect()
    await init_user()
    yield
    await database.disconnect()


metadata.create_all(engine)
app = FastAPI(lifespan=lifespan)
router = APIRouter()


async def get_paginated(limit: int, offset: int):
    query = Contact.select().limit(limit).offset(offset)
    items_task = database.fetch_all(query=query)
    count_query = select([func.count()]).select_from(Contact)
    count_task = database.fetch_val(query=count_query)
    items, count = await asyncio.gather(items_task, count_task)
    return {
        "count": count,
        "items": [*items],
    }


@router.get("/", response_model=PaginatedResponse[ContactDB])
async def read_contacts_list(
    current_user: Annotated[UserSchema, Depends(get_current_user)],
    limit: int = Query(100, ge=0, le=200),
    offset: int = Query(0, ge=0),
):
    return await get_paginated(limit, offset)


async def post(payload: ContactSchema):
    query = Contact.insert().values(
        name=payload.name,
        surname=payload.surname,
        phone=payload.phone,
        email=payload.email,
    )
    return await database.execute(query=query)


@router.post("/", response_model=ContactDB, status_code=status.HTTP_201_CREATED)
async def create_contact(
    current_user: Annotated[UserSchema, Depends(get_current_user)],
    payload: ContactSchema,
):
    note_id = await post(payload)
    response_object = {
        "id": note_id,
        "name": payload.name,
        "surname": payload.surname,
        "phone": payload.phone,
        "email": payload.email,
    }
    return response_object


async def get(id: int):
    query = Contact.select().where(id == Contact.c.id)
    return await database.fetch_one(query=query)


@router.get("/{contact_id}", response_model=ContactDB)
async def read_contact(
    current_user: Annotated[UserSchema, Depends(get_current_user)],
    contact_id: Annotated[int, Path(title="The ID of the item to get", ge=1)],
):
    contact = await get(contact_id)
    if not contact:
        raise HTTPException(
            status_code=404, detail=f"Contact with id {contact_id} not found"
        )
    return contact


async def put(id: int, payload: ContactSchema):
    query = (
        Contact.update()
        .where(id == Contact.c.id)
        .values(
            name=payload.name,
            surname=payload.surname,
            phone=payload.phone,
            email=payload.email,
        )
        .returning(Contact.c.id)
    )
    return await database.execute(query=query)


@router.put("/{contact_id}", response_model=ContactDB)
async def update_concat(
    current_user: Annotated[UserSchema, Depends(get_current_user)],
    contact_id: Annotated[int, Path(title="The ID of the item to get", ge=1)],
    payload: ContactSchema,
):
    contact = await get(contact_id)
    if not contact:
        raise HTTPException(
            status_code=404, detail=f"Contact with id {contact_id} not found"
        )

    contact_id = await put(contact_id, payload)

    response_object = {
        "id": contact_id,
        "name": payload.name,
        "surname": payload.surname,
        "phone": payload.phone,
        "email": payload.email,
    }

    return response_object


async def delete(id: int):
    query = Contact.delete().where(id == Contact.c.id)
    return await database.execute(query=query)


@router.delete("/{contact_id}", response_model=ContactDB)
async def delete_contact(
    current_user: Annotated[UserSchema, Depends(get_current_user)],
    contact_id: Annotated[int, Path(title="The ID of the item to get", ge=1)],
):
    contact = await get(contact_id)
    if not contact:
        raise HTTPException(
            status_code=404, detail=f"Contact with id {contact_id} not found"
        )
    await delete(contact_id)
    return contact


@app.get("/ping", response_model=WelcomeMsgSchema)
def root():
    return {"msg": "Welcome to PhoneBookAPI"}


app.include_router(router, tags=["contacts"], prefix="/contacts")
app.include_router(auth_router, tags=["auth"], prefix="/auth")
