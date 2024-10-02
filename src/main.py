from fastapi import FastAPI, Depends, APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List
from fastapi import Request
from datetime import datetime, timezone
import models, schemas
from database import SessionLocal, engine
from models import Product, Order, OrderItem
from schemas import Product as ProductSchema, ProductCreate, Order as OrderSchema, OrderCreate, OrderResponse, OrderItemResponse

router = APIRouter()

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

templates = Jinja2Templates(directory="src/templates")


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


# 1. **Эндпоинты для товаров**:

# Создание товара
@app.post("/products/", response_model=ProductSchema)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    db_product = Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

# Получение списка товаров
@app.get("/products/", response_class=HTMLResponse)
def get_products(request: Request, db: Session = Depends(get_db)):
    products = db.query(models.Product).all()
    return templates.TemplateResponse("products.html", {"request": request, "products": products})

# Получение информации о товаре по id
@app.get("/products/{id}", response_model=ProductSchema)
def get_product(id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

# Обновление информации о товаре
@app.put("/products/{id}", response_model=ProductSchema)
def update_product(id: int, product: ProductCreate, db: Session = Depends(get_db)):
    db_product = db.query(Product).filter(Product.id == id).first()
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    for key, value in product.dict().items():
        setattr(db_product, key, value)
    db.commit()
    db.refresh(db_product)
    return db_product

# Удаление товара
@app.delete("/products/{id}", response_model=dict)
def delete_product(id: int, db: Session = Depends(get_db)):
    db_product = db.query(Product).filter(Product.id == id).first()
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(db_product)
    db.commit()
    return {"message": "Product deleted successfully"}

# 2. **Эндпоинты для заказов**:

# Создание заказа с проверкой наличия товара на складе
@app.post("/orders/", response_model=OrderResponse)
def create_order(order: OrderCreate, db: Session = Depends(get_db)):
    db_order = Order(status=order.status, created_at=datetime.now(timezone.utc))
    db.add(db_order)
    db.commit()
    db.refresh(db_order)

    for item in order.items:
        # Проверка наличия достаточного количества товара
        db_product = db.query(Product).filter(Product.id == item.product_id).first()
        if db_product is None:
            raise HTTPException(status_code=404, detail=f"Product with id {item.product_id} not found")
        if db_product.stock < item.quantity:
            raise HTTPException(status_code=400, detail=f"Insufficient stock for product {db_product.name}")

        # Обновление количества товара на складе
        db_product.stock -= item.quantity
        db.add(db_product)

        db_order_item = OrderItem(product_id=item.product_id, order_id=db_order.id, quantity=item.quantity)
        db.add(db_order_item)

    db.commit()
    return db_order

# Получение списка заказов
@app.get("/orders/", response_model=List[OrderResponse])
def get_orders(db: Session = Depends(get_db)):
    orders = db.query(Order).all()
    order_responses = []

    for order in orders:
        items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
        order_response = OrderResponse(
            id=order.id,
            created_at=order.created_at.isoformat(),
            status=order.status,
            items=[OrderItemResponse(id=item.id, product_id=item.product_id, quantity=item.quantity) for item in items]
        )
        order_responses.append(order_response)

    return order_responses

# Получение информации о заказе по id
@app.get("/orders/{id}", response_model=OrderResponse)
def get_order(id: int, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == id).first()
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    
    items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
    return OrderResponse(
        id=order.id,
        created_at=order.created_at.isoformat(),
        status=order.status,
        items=[OrderItemResponse(id=item.id, product_id=item.product_id, quantity=item.quantity) for item in items]
    )

# Обновление статуса заказа
@app.patch("/orders/{id}/status", response_model=OrderResponse)
def update_order_status(id: int, status: str, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == id).first()
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    order.status = status
    db.commit()
    db.refresh(order)
    return order

# Подключение маршрутизатора
app.include_router(router)
