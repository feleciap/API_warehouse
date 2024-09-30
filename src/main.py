from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from typing import List  
import models, schemas
from database import SessionLocal, engine

# Создаем все таблицы
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Получение базы данных
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Создание продукта
@app.post("/products/", response_model=schemas.Product)
def create_product(product: schemas.ProductCreate, db: Session = Depends(get_db)):
    db_product = models.Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

# Получение всех продуктов
@app.get("/products/", response_model=List[schemas.Product])  
def get_products(db: Session = Depends(get_db)):
    return db.query(models.Product).all()

# Создание заказа
@app.post("/orders/", response_model=schemas.Order)
def create_order(order: schemas.OrderCreate, db: Session = Depends(get_db)):
    db_order = models.Order(status=order.status)
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    
    for item in order.items:
        db_order_item = models.OrderItem(product_id=item.product_id, order_id=db_order.id, quantity=item.quantity)
        db.add(db_order_item)
        db.commit()
        db.refresh(db_order_item)
    
    return db_order

# Получение всех заказов
@app.get("/orders/", response_model=List[schemas.Order])  
def get_orders(db: Session = Depends(get_db)):
    return db.query(models.Order).all()
