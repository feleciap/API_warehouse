from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# URL для подключения к базе данных PostgreSQL
DATABASE_URL = "postgresql://feleciap:123@localhost/warehouse"

# Создаем движок для работы с базой данных
engine = create_engine(DATABASE_URL)

# Создаем фабрику сессий
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Создаем базовый класс для моделей
Base = declarative_base()
