import sys
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String
from sqlalchemy.orm import sessionmaker

# Добавляем путь к модулю
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/../')

from app.main import app, get_db, Base

DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
metadata = MetaData()

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(scope="module")
def setup_database():
    items_table = Table(
        'items', metadata,
        Column('id', Integer, primary_key=True, index=True, autoincrement=True),
        Column('name', String),
        Column('email', String),
        Column('phone', String),
        Column('note', String)
    )
    metadata.create_all(bind=engine)
    yield items_table
    metadata.drop_all(bind=engine)

def test_create_item_success(setup_database):
    response = client.post("/items/", json={"name": "John Doe", "email": "john@example.com", "phone": "1234567890", "note": "Test note"})
    assert response.status_code == 200
    assert response.json()["name"] == "John Doe"

def test_create_item_fail(setup_database):
    response = client.post("/items/", json={"name": "John Doe"})
    assert response.status_code == 422

def test_read_item_success(setup_database):
    response = client.post("/items/", json={"name": "John Doe", "email": "john@example.com", "phone": "1234567890", "note": "Test note"})
    item_id = response.json()["id"]
    response = client.get(f"/items/{item_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "John Doe"

def test_read_item_fail(setup_database):
    response = client.get("/items/999")
    assert response.status_code == 404

def test_update_item_success(setup_database):
    response = client.post("/items/", json={"name": "John Doe", "email": "john@example.com", "phone": "1234567890", "note": "Test note"})
    item_id = response.json()["id"]
    response = client.put(f"/items/{item_id}", json={"name": "Jane Doe", "email": "jane@example.com", "phone": "0987654321", "note": "Updated note"})
    assert response.status_code == 200
    assert response.json()["name"] == "Jane Doe"

def test_update_item_fail(setup_database):
    response = client.put("/items/999", json={"name": "Jane Doe", "email": "jane@example.com", "phone": "0987654321", "note": "Updated note"})
    assert response.status_code == 404

def test_delete_item_success(setup_database):
    response = client.post("/items/", json={"name": "John Doe", "email": "john@example.com", "phone": "1234567890", "note": "Test note"})
    item_id = response.json()["id"]
    response = client.delete(f"/items/{item_id}")
    assert response.status_code == 200
    assert response.json()["detail"] == "Item deleted"

def test_delete_item_fail(setup_database):
    response = client.delete("/items/999")
    assert response.status_code == 404
