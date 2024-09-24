import pytest
from fastapi.testclient import TestClient
from main import app, get_db, items_table
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, mock_open

DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

mock_file_data = """id,name,email,phone,note
1,John Doe,john@example.com,1234567890,Note 1
2,Jane Doe,jane@example.com,0987654321,Note 2
"""


@pytest.fixture(autouse=True)
def setup_database():
    inspector = inspect(engine)
    if not inspector.has_table('items'):
        items_table.create(bind=engine)

    db = SessionLocal()
    db.execute(
        items_table.insert().values(id=1, name="John Doe", email="john@example.com", phone="1234567890", note="Note 1"))
    db.execute(
        items_table.insert().values(id=2, name="Jane Doe", email="jane@example.com", phone="0987654321", note="Note 2"))
    db.commit()
    db.close()

    yield

    items_table.drop(bind=engine)


@patch("builtins.open", new_callable=mock_open, read_data=mock_file_data)
def test_create_item_success(mock_file):
    response = client.post("/items/", json={"name": "Alice",
                                            "email": "alice@example.com",
                                            "phone": "1112223333",
                                            "note": "Note 3"})
    assert response.status_code == 200
    assert response.json()["name"] == "Alice"


@patch("builtins.open", new_callable=mock_open, read_data=mock_file_data)
def test_create_item_failure(mock_file):
    response = client.post("/items/", json={"name": "",
                                            "email": "alice@example.com",
                                            "phone": "1112223333",
                                            "note": "Note 3"})
    assert response.status_code == 422  # Unprocessable Entity


@patch("builtins.open", new_callable=mock_open, read_data=mock_file_data)
def test_read_item_success(mock_file):
    response = client.get("/items/1")
    assert response.status_code == 200
    assert response.json()["name"] == "John Doe"


@patch("builtins.open", new_callable=mock_open, read_data=mock_file_data)
def test_read_item_failure(mock_file):
    response = client.get("/items/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Item not found"


@patch("builtins.open", new_callable=mock_open, read_data=mock_file_data)
def test_update_item_success(mock_file):
    response = client.put("/items/1", json={"name": "John Smith",
                                            "email": "johnsmith@example.com",
                                            "phone": "1234567890",
                                            "note": "Updated Note"})
    assert response.status_code == 200
    assert response.json()["name"] == "John Smith"


@patch("builtins.open", new_callable=mock_open, read_data=mock_file_data)
def test_update_item_failure(mock_file):
    response = client.put("/items/999", json={"name": "John Smith",
                                              "email": "johnsmith@example.com",
                                              "phone": "1234567890",
                                              "note": "Updated Note"})
    assert response.status_code == 404
    assert response.json()["detail"] == "Item not found"


@patch("builtins.open", new_callable=mock_open, read_data=mock_file_data)
def test_delete_item_success(mock_file):
    response = client.delete("/items/1")
    assert response.status_code == 200
    assert response.json()["detail"] == "Item deleted"


@patch("builtins.open", new_callable=mock_open, read_data=mock_file_data)
def test_delete_item_failure(mock_file):
    response = client.delete("/items/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Item not found"
