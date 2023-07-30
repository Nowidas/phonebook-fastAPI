import json

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.auth import get_current_user


def override_get_current_user():
    pass


@pytest.fixture(scope="module")
def test_app():
    app.dependency_overrides[get_current_user] = override_get_current_user
    client = TestClient(app)
    yield client


def test_ping(test_app):
    response = test_app.get("/ping")
    assert response.status_code == 200
    assert response.json() == {"msg": "Welcome to PhoneBookAPI"}


def test_create_contact(test_app, monkeypatch):
    test_request_payload = {
        "name": "jack",
        "surname": "kowalsky",
        "phone": "+48333111222",
        "email": "a@b.com",
    }
    test_response_payload = {
        "id": 1,
        "name": "jack",
        "surname": "kowalsky",
        "phone": "tel:+48-33-311-12-22",
        "email": "a@b.com",
    }

    async def mock_post(payload):
        return 1

    monkeypatch.setattr("app.main.post", mock_post)

    response = test_app.post(
        "/contacts/",
        content=json.dumps(test_request_payload),
    )

    assert response.status_code == 201
    assert response.json() == test_response_payload


def test_create_contact_invalid_json(test_app):
    response = test_app.post("/contacts/", content=json.dumps({"name": "something"}))
    assert response.status_code == 422


def test_read_contact(test_app, monkeypatch):
    test_payload = {
        "id": 1,
        "name": "jack",
        "surname": "kowalsky",
        "phone": "tel:+48-33-311-12-22",
        "email": "a@b.com",
    }

    async def mock_get(id):
        return test_payload

    monkeypatch.setattr("app.main.get", mock_get)

    response = test_app.get("/contacts/1")

    assert response.status_code == 200
    assert response.json() == test_payload


def test_read_contact_incorret_id(test_app, monkeypatch):
    async def mock_get(id):
        return None

    monkeypatch.setattr("app.main.get", mock_get)

    response = test_app.get("/contacts/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Contact with id 999 not found"

    response = test_app.get("/contacts/0")

    assert response.status_code == 422
    assert (
        response.json()["detail"][0]["msg"]
        == "Input should be greater than or equal to 1"
    )


def test_read_all_contacts(test_app, monkeypatch):
    test_payload = {
        "count": 2,
        "items": [
            {
                "id": 1,
                "name": "jack",
                "surname": "kowalsky",
                "phone": "tel:+48-33-311-12-22",
                "email": "a@b.com",
            },
            {
                "id": 2,
                "name": "jack",
                "surname": "kowalsky",
                "phone": "tel:+48-33-311-12-22",
                "email": "a@b.com",
            },
        ],
    }

    async def mock_get_paginated(limit, offset):
        return test_payload

    monkeypatch.setattr("app.main.get_paginated", mock_get_paginated)

    response = test_app.get("/contacts/")
    assert response.status_code == 200
    assert response.json() == test_payload


def test_update_contact(test_app, monkeypatch):
    test_update_payload = {
        "name": "jack2",
        "surname": "kowalsky",
        "phone": "tel:+48-33-311-12-22",
        "email": "a@b.com",
    }
    test_update_response = {
        "id": 1,
        "name": "jack2",
        "surname": "kowalsky",
        "phone": "tel:+48-33-311-12-22",
        "email": "a@b.com",
    }

    async def mock_get(contacts_id):
        return True

    monkeypatch.setattr("app.main.get", mock_get)

    async def mock_put(contacts_id, payload):
        return 1

    monkeypatch.setattr("app.main.put", mock_put)

    response = test_app.put("/contacts/1/", content=json.dumps(test_update_payload))
    assert response.status_code == 200
    assert response.json() == test_update_response


@pytest.mark.parametrize(
    "id, payload, status_code",
    [
        [1, {}, 422],
        [1, {"name": "Jack"}, 422],
        [
            0,
            {
                "name": "jack",
                "surname": "kowalsky",
                "phone": "tel:+48-33-311-12-22",
                "email": "a@b.com",
            },
            422,
        ],
        [
            999,
            {
                "name": "jack",
                "surname": "kowalsky",
                "phone": "tel:+48-33-311-12-22",
                "email": "a@b.com",
            },
            404,
        ],
    ],
)
def test_update_contact_invalid(test_app, monkeypatch, id, payload, status_code):
    async def mock_get(id):
        return None

    monkeypatch.setattr("app.main.get", mock_get)

    response = test_app.put(
        f"/contacts/{id}/",
        content=json.dumps(payload),
    )
    assert response.status_code == status_code


def test_remove_contact(test_app, monkeypatch):
    test_data = {
        "id": 1,
        "name": "jack",
        "surname": "kowalsky",
        "phone": "tel:+48-33-311-12-22",
        "email": "a@b.com",
    }

    async def mock_get(id):
        return test_data

    monkeypatch.setattr("app.main.get", mock_get)

    async def mock_delete(id):
        return id

    monkeypatch.setattr("app.main.delete", mock_delete)

    response = test_app.delete("/contacts/1/")
    assert response.status_code == 200
    assert response.json() == test_data


def test_remove_contact_incorrect_id(test_app, monkeypatch):
    async def mock_get(id):
        return None

    monkeypatch.setattr("app.main.get", mock_get)

    response = test_app.delete("/contacts/999/")
    assert response.status_code == 404
    assert response.json()["detail"] == "Contact with id 999 not found"
