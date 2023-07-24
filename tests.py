from starlette.testclient import TestClient
import pytest
import json
from main import app

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base
from main import app, get_session

from base64 import b64encode

SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


Base.metadata.create_all(bind=engine)
client = TestClient(app)


def override_get_session():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_session] = override_get_session


def test_ping():
    response = client.get("/api/ping")
    assert response.status_code == 200
    assert response.json() == {"msg": "Welcome to PhoneBookAPI"}


def test_create_contact():
    payload = b64encode(b"admin:admin").decode("ascii")
    auth_header = f"Basic {payload}"

    test_request_payload = {
        "name": "Jekob",
        "surname": "Stone",
        "phone": "+48111222333",
        "email": "jakobstone@gmail.com",
    }
    response = client.post(
        "/api/contacts",
        content=json.dumps(test_request_payload),
        headers={"Authorization": auth_header},
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["name"] == "Jekob"
    assert "id" in data
    user_id = data["id"]

    response = client.get(
        f"/api/contacts/{user_id}", headers={"Authorization": auth_header}
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["email"] == "jakobstone@gmail.com"
    assert data["id"] == user_id
