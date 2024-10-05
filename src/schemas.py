from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

# Pydantic модели для продуктов
class ProductBase(BaseModel):
    description: Optional[str] = None
    price: float
    quantity: int

class ProductCreate(ProductBase):
    name: str = Field(..., min_length=1, max_length=100)
    price: float = Field(..., gt=0)
    description: Optional[str] = None
    quantity: int

class Product(ProductBase):
    id: int

    class Config:
        orm_mode = True  

class ProductResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    price: float
    quantity: int
    class Config:
        orm_mode = True
# Pydantic модели для элементов заказа
class OrderItemBase(BaseModel):
    id: int
    order_id: int
    product_id: int
    quantity: int

class OrderItemCreate(OrderItemBase):
    pass

class OrderItem(OrderItemBase):
    id: int
    product: Product

    class Config:
        orm_mode = True

# Pydantic модели для заказов
class OrderBase(BaseModel):
    status: str

class OrderCreate(OrderBase):
    items: List[OrderItemCreate]

class Order(OrderBase):
    id: int
    items: List[OrderItem]

    class Config:
        orm_mode = True

# Модель для обновления статуса заказа
class OrderStatusUpdate(BaseModel):
    status: str


class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    quantity: int

    class Config:
        orm_mode = True 


class OrderResponse(BaseModel):
    id: int
    created_at: datetime
    status: str
    items: List[OrderItemResponse]

    class Config:
        orm_mode = True
