from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# Pydantic модели для продуктов
class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    quantity: int

class ProductCreate(ProductBase):
    pass

class Product(ProductBase):
    id: int

    class Config:
        from_attributes = True  

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
        from_attributes = True

# Pydantic модели для заказов
class OrderBase(BaseModel):
    status: str

class OrderCreate(OrderBase):
    items: List[OrderItemCreate]

class Order(OrderBase):
    id: int
    items: List[OrderItem]

    class Config:
        from_attributes = True

# Модель для обновления статуса заказа
class OrderStatusUpdate(BaseModel):
    status: str


class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    quantity: int

    class Config:
        from_attributes = True  # Включаем возможность использования from_orm


class OrderResponse(BaseModel):
    id: int
    created_at: datetime
    status: str
    items: List[OrderItemResponse]

    class Config:
        from_attributes = True  