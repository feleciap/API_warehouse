import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.main import app  # Замените на путь к вашему FastAPI приложению
from src.database import TestingSessionLocal, Base  , get_db# Убедитесь, что путь правильный
from src import models  # Импортируем модели

# Настройка базы данных для тестирования
DATABASE_URL = "postgresql://feleciap:123@localhost/warehouse"
engine = create_engine(DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Создаем таблицы базы данных
Base.metadata.create_all(bind=engine)

# Переопределяем зависимость get_db
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(scope="module")
def setup_database():
    db = TestingSessionLocal()
    # Создаем все таблицы
    Base.metadata.create_all(bind=db.bind)
    # Добавляем тестовые данные
    test_product = models.Product(name="Initial Product", description="Initial description", price=5.99, quantity=50)
    db.add(test_product)
    db.commit()
    db.refresh(test_product)
    yield db.query(models.Product).delete()  # Удаляем все продукты
    db.commit()
    db.close()

def test_create_product(setup_database):
    # Данные для нового продукта
    new_product = {
        "name": "Test Product",
        "description": "This is a test product.",
        "price": 10.99,
        "quantity": 100
    }
    response = client.post("/products/", json=new_product)
    # Проверяем статус-код ответа
    assert response.status_code == 201
    # Проверяем, что возвращаемый продукт соответствует отправленным данным
    created_product = response.json()
    assert created_product["name"] == new_product["name"]
    assert created_product["description"] == new_product["description"]
    assert created_product["price"] == new_product["price"]
    assert created_product["quantity"] == new_product["quantity"]
    # Проверяем, что продукт был добавлен в базу данных
    db = TestingSessionLocal()
    db_product = db.query(models.Product).filter(models.Product.name == new_product["name"]).first()
    assert db_product is not None

def test_get_products(test_db):
    response = client.get("/products/")
    assert response.status_code == 200  # Проверяем, что статус ответа 200 (OK)

    products = response.json()  # Получаем данные в формате JSON
    assert len(products) == 1  # Проверяем, что мы получили 1 продукт
    assert products[0]["name"] == "Test Product"  # Проверяем, что название продукта совпадает
    assert products[0]["price"] == 10.99  # Проверяем, что цена продукта совпадает