from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# URL вашей базы данных
SQLALCHEMY_DATABASE_URL = "postgresql://feleciap:123@localhost/warehouse"

# Создание движка базы данных
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Создание локальной сессии для работы с базой данных
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=create_engine("postgresql://feleciap:123@localhost/test_warehouse"))


# Создание базы данных для декларативного стиля
Base = declarative_base()

# Функция для получения доступа к базе данных
def get_db():
    db = SessionLocal()
    try:
        yield db  # Используем генератор для возвращения сессии
    finally:
        db.close()  # Закрываем сессию после использования
