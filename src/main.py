from fastapi import FastAPI, Depends, HTTPException, Form 
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import List
from fastapi import Request
from datetime import datetime, timezone
import models, schemas
from database import SessionLocal, engine
from models import Product, Order, OrderItem
from schemas import Product as ProductSchema, ProductCreate, Order as OrderSchema, OrderCreate, OrderResponse, OrderItemResponse , ProductResponse
from src.models import Product


models.Base.metadata.create_all(bind=engine)

app = FastAPI()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 1. **Эндпоинты для товаров**:
@app.post("/products/", response_model=schemas.Product, status_code=201)
def create_product(product: schemas.ProductCreate, db: Session = Depends(get_db)):
    db_product = models.Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

# Получение всех продуктов
@app.get("/products/")
def get_products(request: Request, db: Session = Depends(get_db)):
    return db.query(models.Product).all()

# Получение информации о товаре по id
@app.get("/products/{id}", response_model=schemas.Product)
def get_product(id: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.id == id).first()  # Используйте .first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product 

# Обновление информации о товаре
@app.put("/products/{id}")
async def update_or_create_product(id: int, product_data: ProductCreate, request: Request, db: Session = Depends(get_db)):
    db_product = db.query(Product).filter(Product.id == id).first()
    
    if db_product:
        db_product.name = product_data.name
        db_product.description = product_data.description
        db_product.price = product_data.price
        db_product.quantity = product_data.quantity
        db.commit()
        db.refresh(db_product)
    else:
        new_product = Product(id=id, **product_data.dict())
        db.add(new_product)
        db.commit()
        db.refresh(new_product)
        db_product = new_product

    return db_product


@app.get("/products/{id}/delete")
def confirm_delete_product(request: Request, id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == id).first()
    return product

# 2. **Эндпоинты для заказов**:

# Создание заказа с проверкой наличия товара на складе

from fastapi import Response

@app.post("/orders/")
def create_order(order: OrderCreate, db: Session = Depends(get_db)):
    try:
        db_order = Order(status="in_progress", created_at=datetime.now(timezone.utc))
        db.add(db_order)
        db.commit()
        db.refresh(db_order)

        for item in order.items:
            db_product = db.query(Product).filter(Product.id == item.product_id).first()
            if db_product is None:
                db.rollback()  
                raise HTTPException(status_code=404, detail=f"Product with id {item.product_id} not found")
            if db_product.quantity < item.quantity:
                db.rollback()  
                raise HTTPException(status_code=400, detail=f"Insufficient stock for product {db_product.name}")

            db_product.quantity -= item.quantity
            db.add(db_product)
            db_order_item = OrderItem(product_id=item.product_id, order_id=db_order.id, quantity=item.quantity)
            db.add(db_order_item)

        db.commit()
        db_order.status = "в процессе"
        db.commit()

    except Exception as e:
        db.rollback()
        raise e

    return Response(status_code=200)


    
# Получение списка заказов
@app.get("/orders/")
def get_orders(db: Session = Depends(get_db)):
    orders = db.query(Order).all()
    order_responses = []

    for order in orders:
        items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
        order_response = {
            "id": order.id,
            "created_at": order.created_at.isoformat(),
            "status": order.status,
            "items": [{"product_id": item.product_id, "quantity": item.quantity} for item in items]
        }
        order_responses.append(order_response)

    return order_responses


# Получение информации о заказе по id
@app.get("/orders/{id}")
def get_order(id: int, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == id).first()
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")

    items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()

    order_response = {
        "id": order.id,
        "created_at": order.created_at.isoformat(),
        "status": order.status,
        "items": []
    }

    for item in items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if product:
            order_response["items"].append({
                "product_id": product.id,
                "product_name": product.name,  
                "product_description": product.description,
                "quantity": item.quantity,
                "price": product.price  
            })

    return order_response

# Обновление статуса заказа
@app.patch("/orders/{id}/status", response_model=OrderResponse)
def update_order_status(id: int, status: str = Form(...), db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == id).first()
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")

    valid_statuses = ["в процессе", "отправлен", "доставлен"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status: {status}")

    order.status = status
    db.commit()
    db.refresh(order)
    return order