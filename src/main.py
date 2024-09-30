from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from models import Product, Order, OrderItem, OrderStatus
from database import SessionLocal, engine, Base
from fastapi.middleware.cors import CORSMiddleware
from schemas import ProductCreate, Product, OrderCreate, Order, OrderStatusUpdate

app = FastAPI()

# Разрешенные источники (доменные имена)
origins = [
    "http://127.0.0.1:8000",  # разрешаем ваш API локально
    "http://localhost:8000",  # если работаете с другим хостом
]

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # разрешенные домены
    allow_credentials=True,
    allow_methods=["*"],  # разрешаем все методы (GET, POST, PUT и т.д.)
    allow_headers=["*"],  # разрешаем все заголовки
)

# Автоматическое создание таблиц при запуске приложения
@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)

# Зависимость для создания сессии
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Продукты

@app.post("/products/", response_model=Product)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    db_product = Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

@app.get("/products/", response_model=List[Product])
def get_products(db: Session = Depends(get_db)):
    return db.query(Product).all()

@app.get("/products/{product_id}", response_model=Product)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@app.put("/products/{product_id}", response_model=Product)
def update_product(product_id: int, product_data: ProductCreate, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    
    for key, value in product_data.dict().items():
        setattr(product, key, value)
    
    db.commit()
    db.refresh(product)
    return product

@app.delete("/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    
    db.delete(product)
    db.commit()
    return {"ok": True}

# Заказы

@app.post("/orders/", response_model=Order)
def create_order(order_data: OrderCreate, db: Session = Depends(get_db)):
    db_order = Order(status=order_data.status)
    
    for item_data in order_data.items:
        product = db.query(Product).filter(Product.id == item_data.product_id).first()
        if product is None or product.quantity < item_data.quantity:
            raise HTTPException(status_code=400, detail="Not enough stock for product")
        
        product.quantity -= item_data.quantity
        db_item = OrderItem(product_id=item_data.product_id, quantity=item_data.quantity)
        db_order.items.append(db_item)
    
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order

@app.get("/orders/", response_model=List[Order])
def get_orders(db: Session = Depends(get_db)):
    return db.query(Order).all()

@app.get("/orders/{order_id}", response_model=Order)
def get_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@app.patch("/orders/{order_id}/status", response_model=Order)
def update_order_status(order_id: int, status: OrderStatusUpdate, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    
    order.status = status.status
    db.commit()
    db.refresh(order)
    return order
