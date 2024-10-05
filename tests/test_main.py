import pytest
from fastapi.testclient import TestClient
from src.main import app
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database import get_db
from src.models import Base  # Импортируем Base из models
from jinja2 import Environment, FileSystemLoader

env = Environment(loader=FileSystemLoader('src/templates'))


# Создаем новую базу данных для тестирования
DATABASE_URL = "sqlite:///./test.db"  # Можно использовать SQLite для тестов
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
    # Код для настройки базы данных (если необходимо)
    yield
    # Код для очистки базы данных после тестов (опционально)
    Base.metadata.drop_all(bind=engine)




def test_update_order_status():
    response = client.patch("/orders/1/status", data={"status": "Shipped"})  # Предполагается, что заказ ID 1 существует
    assert response.status_code == 200
    assert response.json()["status"] == "Shipped"
