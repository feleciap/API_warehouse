from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum

Base = declarative_base()

class OrderStatus(enum.Enum):
    processing = "в процессе"
    shipped = "отправлен"
    delivered = "доставлен"

# SQLAlchemy модели
class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    price = Column(Float, nullable=False)
    quantity = Column(Integer, nullable=False)

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(Enum(OrderStatus), default=OrderStatus.processing)
    items = relationship("OrderItem", back_populates="order")

class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer, nullable=False)

    order = relationship("Order", back_populates="items")
    product = relationship("Product")

# Pydantic модели
class OrderItemBase(BaseModel):
    order_id: int
    product_id: int
    quantity: int

class OrderItemCreate(OrderItemBase):
    pass

class OrderItem(OrderItemBase):
    id: int

    class Config:
        from_attributes = True  # Замените orm_mode на from_attributes для Pydantic V2

class ProductBase(BaseModel):
    name: str
    description: str = None
    price: float
    quantity: int

class ProductCreate(ProductBase):
    pass

class Product(ProductBase):
    id: int

    class Config:
        from_attributes = True  # Замените orm_mode на from_attributes для Pydantic V2

class OrderBase(BaseModel):
    status: OrderStatus
    items: list[OrderItemBase]  # Включите в себя список OrderItemBase

class OrderCreate(OrderBase):
    pass

class Order(OrderBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True  # Замените orm_mode на from_attributes для Pydantic V2
