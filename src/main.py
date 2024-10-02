from fastapi import FastAPI, Depends, APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List
from fastapi import Request
from datetime import datetime, timezone  # для временных меток
import models, schemas
from database import SessionLocal, engine
from models import Order, OrderItem
from schemas import Order as OrderSchema, OrderCreate, OrderResponse, OrderItemCreate, OrderItemResponse

router = APIRouter()

# Создаем все таблицы
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

templates = Jinja2Templates(directory="src/templates")

# Получение базы данных
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Главная страница с кнопками
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

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
    db_order = models.Order(status=order.status, created_at=datetime.now(timezone.utc))  # Добавил временную метку
    db.add(db_order)
    db.commit()
    db.refresh(db_order)

    for item in order.items:
        db_order_item = models.OrderItem(product_id=item.product_id, order_id=db_order.id, quantity=item.quantity)
        db.add(db_order_item)
    
    db.commit()  # Перенес коммит вне цикла, чтобы уменьшить количество операций
    
    return db_order

# Получение всех заказов
@app.get("/orders/", response_model=List[OrderResponse])
def get_orders(db: Session = Depends(get_db)):
    orders = db.query(Order).all()  # Получение всех заказов
    order_responses = []

    for order in orders:
        # Получаем связанные элементы заказа
        items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
        order_response = OrderResponse(
            id=order.id,
            created_at=order.created_at.isoformat(),
            status=order.status,
            items=[OrderItemResponse(id=item.id, product_id=item.product_id, quantity=item.quantity) for item in items]
        )
        order_responses.append(order_response)

    return order_responses

# Подключение маршрутизатора
app.include_router(router)
