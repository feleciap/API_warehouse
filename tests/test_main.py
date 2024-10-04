import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Product  # Импортируйте свои модели
from main import app, get_db  # Импортируйте ваше приложение FastAPI и функцию get_db

# Настройка тестовой базы данных (например, SQLite in-memory)
SQLALCHEMY_DATABASE_URL = "postgresql://feleciap:123@localhost/warehouse"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Создание тестовой сессии для тестов
@pytest.fixture(scope="module")
def test_db():
    Base.metadata.create_all(bind=engine)  # Создание всех таблиц
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)  # Удаление всех таблиц после тестов

@pytest.fixture(scope="module")
def client(test_db):
    def override_get_db():
        try:
            yield test_db
        finally:
            test_db.close()

    app.dependency_overrides[get_db] = override_get_db  # Переопределение зависимости
    return TestClient(app)

def test_create_product(client):
    response = client.post("/products/", json={"name": "Test Product", "description": "Test Desc", "price": 10.0, "quantity": 100})
    assert response.status_code == 200
    assert response.json()["name"] == "Test Product"

def test_get_products(client):
    response = client.get("/products/")
    print(response.text)
    assert response.status_code == 200
    assert len(response.json()) > 0
