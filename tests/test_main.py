import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.main import app  
from src.database import TestingSessionLocal, Base  , get_db
from src import models  

DATABASE_URL = "postgresql://feleciap:123@localhost/warehouse"
engine = create_engine(DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

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
    try:
        db.query(models.OrderItem).delete()
        db.query(models.Order).delete()
        db.query(models.Product).delete()
        db.commit()
        
        test_product = models.Product(name="Initial Product", description="Initial description", price=5.99, quantity=50)
        db.add(test_product)
        db.commit()
        db.refresh(test_product)
        yield db
    finally:
        db.query(models.OrderItem).delete()
        db.query(models.Order).delete()
        db.query(models.Product).delete()
        db.commit()

def test_create_product(setup_database):
    new_product = {
        "name": "Test Product",
        "description": "This is a test product.",
        "price": 10.99,
        "quantity": 100
    }
    response = client.post("/products/", json=new_product)
    assert response.status_code == 201
    created_product = response.json()
    assert created_product["name"] == new_product["name"]
    assert created_product["description"] == new_product["description"]
    assert created_product["price"] == new_product["price"]
    assert created_product["quantity"] == new_product["quantity"]
    db = TestingSessionLocal()
    db_product = db.query(models.Product).filter(models.Product.name == new_product["name"]).first()
    assert db_product is not None

def test_get_products(setup_database):
    response = client.get("/products/")
    assert response.status_code == 200  # Проверяем, что статус ответа 200 (OK)

    products = response.json()
    assert len(products) == 2  
    assert products[0]["name"] == "Initial Product"  
    assert products[0]["price"] == 5.99  

def test_confirm_delete_product(setup_database):
    product_data = {
        "name": "Test Product",
        "description": "A product for testing",
        "price": 19.99,
        "quantity": 100
    }
    new_product = models.Product(**product_data)
    setup_database.add(new_product)
    setup_database.commit()
    
    response = client.delete(f"/products/{new_product.id}")
    assert response.status_code == 200
    assert response.json() == {"detail": "Product deleted successfully"}

    response_get_after_delete = client.get(f"/products/{new_product.id}")
    assert response_get_after_delete.status_code == 404  # Продукт должен быть удалён

def test_create_order_product_not_found(setup_database):
    OrderCreate = {
        "items": [
            {"product_id": 999, "quantity": 1}  # Продукт с id 999 не существует
        ]
    }

    response = client.post("/orders/", json=OrderCreate)
    assert response.status_code == 404
    assert response.json() == {"detail": "Product with id 999 not found"}

def test_create_order_product_not_found(setup_database):
    OrderCreate = {
        "items": [
            {"product_id": 999, "quantity": 1}  # Продукт с id 999 не существует
        ]
    }

    response = client.post("/orders/", json=OrderCreate)
    assert response.status_code == 404
    assert response.json() == {"detail": "Product with id 999 not found"}

def test_create_order_insufficient_stock(setup_database):
    test_product = models.Product(name="Test Product", description="A product for testing", price=19.99, quantity=1)
    setup_database.add(test_product)
    setup_database.commit()

    OrderCreate = {
        "items": [
            {"product_id": test_product.id, "quantity": 2}  # Запрашиваем 2 товара, хотя на складе только 1
        ]
    }

    response = client.post("/orders/", json=OrderCreate)
    assert response.status_code == 400
    assert response.json() == {"detail": "Insufficient stock for product Test Product"}



def test_get_order_success(setup_database):
    test_product = models.Product(name="Test Product", description="A product for testing", price=19.99, quantity=10)
    setup_database.add(test_product)
    setup_database.commit()

    order_data = {
        "items": [
            {"product_id": test_product.id, "quantity": 1}
        ]
    }
    response = client.post("/orders/", json=order_data)
    assert response.status_code == 200  # Или 201, в зависимости от реализации
    order_id = response.json()["id"]  

    response = client.get(f"/orders/{order_id}")
    assert response.status_code == 200  
    order_response = response.json()
    
    assert order_response["id"] == order_id
    assert len(order_response["items"]) == 1
    assert order_response["items"][0]["product_id"] == test_product.id
    assert order_response["items"][0]["product_name"] == test_product.name
    assert order_response["items"][0]["quantity"] == 1

def test_get_order_not_found(setup_database):
    response = client.get("/orders/999")  
    assert response.status_code == 404
    assert response.json() == {"detail": "Order not found"}

def test_update_order_status_success(setup_database):
    test_product = models.Product(name="Test Product", description="A product for testing", price=19.99, quantity=10)
    setup_database.add(test_product)
    setup_database.commit()

    order_data = {
        "items": [
            {"product_id": test_product.id, "quantity": 1}
        ]
    }
    response = client.post("/orders/", json=order_data)
    assert response.status_code == 200  
    order_id = response.json()["id"]  

    new_status = "отправлен"
    response = client.patch(f"/orders/{order_id}/status", data={"status": new_status})
    assert response.status_code == 200
    assert response.json()["status"] == new_status  # Проверяем обновленный статус

def test_update_order_status_not_found(setup_database):
    new_status = "отправлен"
    response = client.patch("/orders/999/status", data={"status": new_status}) 
    assert response.status_code == 404
    assert response.json() == {"detail": "Order not found"}

def test_update_order_status_invalid_status(setup_database):
    test_product = models.Product(name="Test Product", description="A product for testing", price=19.99, quantity=10)
    setup_database.add(test_product)
    setup_database.commit()

    order_data = {
        "items": [
            {"product_id": test_product.id, "quantity": 1}
        ]
    }
    response = client.post("/orders/", json=order_data)
    assert response.status_code == 200  
    order_id = response.json()["id"] 

    invalid_status = "неизвестный статус"
    response = client.patch(f"/orders/{order_id}/status", data={"status": invalid_status})
    assert response.status_code == 400
    assert response.json() == {"detail": f"Invalid status: {invalid_status}"}
