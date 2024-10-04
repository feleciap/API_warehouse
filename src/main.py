from fastapi import FastAPI, Depends, HTTPException, Form
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
from fastapi.staticfiles import StaticFiles

models.Base.metadata.create_all(bind=engine)

app = FastAPI()
app.mount("/static", StaticFiles(directory="src/static"), name="static")

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
@app.post("/products/", response_model=schemas.Product)
def create_product(product: schemas.ProductCreate, db: Session = Depends(get_db)):
    db_product = models.Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

# Получение всех продуктов
@app.get("/products/", response_class=HTMLResponse)
def get_products(request: Request, db: Session = Depends(get_db)):
    products = db.query(models.Product).all()
    return templates.TemplateResponse("products.html", {"request": request, "products": products})

# Получение информации о товаре по id
@app.get("/products/{id}", response_class=HTMLResponse)
async def get_product(request: Request, id: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.id == id).first()
    return templates.TemplateResponse("product_detail.html", {"request": request, "product": product})

# Обновление информации о товаре
@app.put("/products/{id}", response_model=ProductSchema)
def update_product(id: int, product: ProductCreate, db: Session = Depends(get_db)):
    db_product = db.query(Product).filter(Product.id == id).first()
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    db_product.name = product.name
    db_product.price = product.price
    db_product.description = product.description  # Обновление поля description
    db.commit()
    db.refresh(db_product)
    return db_product

@app.get("/products/{id}/edit", response_class=HTMLResponse)
def edit_product(request: Request, id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == id).first()
    return templates.TemplateResponse("update_product.html", {"request": request, "product": product})

@app.post("/products/{id}/edit")
def update_product(id: int, request: Request, name: str = Form(...), price: float = Form(...), description: str = Form(...), db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    # Обновление полей продукта
    product.name = name
    product.price = price
    product.description = description
    db.commit()

    # Перенаправление на страницу с сообщением об успешном обновлении
    return templates.TemplateResponse("product_updated.html", {"request": request})


# Удаление товара
@app.post("/products/{id}/delete", response_class=HTMLResponse)
def delete_product(request: Request, id: int, db: Session = Depends(get_db)):
    db_product = db.query(models.Product).filter(models.Product.id == id).first()
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(db_product)
    db.commit()
    return templates.TemplateResponse("product_deleted.html", {"request": request})

@app.get("/products/{id}/delete", response_class=HTMLResponse)
def confirm_delete_product(request: Request, id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == id).first()
    return templates.TemplateResponse("delete_product.html", {"request": request, "product": product})


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
@app.get("/orders/", response_class=HTMLResponse)
def get_orders(request: Request, db: Session = Depends(get_db)):
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

    return templates.TemplateResponse("orders.html", {"request": request, "orders": order_responses})


# Получение информации о заказе по id
@app.get("/orders/{id}", response_class=HTMLResponse)
def get_order(id: int, request: Request, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == id).first()
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    
    items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
    order_response = OrderResponse(
        id=order.id,
        created_at=order.created_at.isoformat(),
        status=order.status,
        items=[OrderItemResponse(id=item.id, product_id=item.product_id, quantity=item.quantity) for item in items]
    )

    return templates.TemplateResponse("order_detail.html", {"request": request, "order": order_response})

# Обновление статуса заказа
@app.patch("/orders/{id}/status", response_model=OrderResponse)
def update_order_status(id: int, status: str = Form(...), db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == id).first()
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    order.status = status
    db.commit()
    db.refresh(order)
    return order
