from sqlalchemy import Column, Integer, String, Float, DateTime , ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from sqlalchemy.orm import relationship

Base = declarative_base()

class Product(Base):
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)
    price = Column(Float)
    quantity = Column(Integer)

class Order(Base):
    __tablename__ = 'orders'

   
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String)
    items = relationship("OrderItem", back_populates="order")

class OrderItem(Base):
    __tablename__ = 'order_items'

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey('orders.id'))
    order_id = Column(Integer, ForeignKey('products.id'))
    quantity = Column(Integer)
    order = relationship("Order", back_populates="items")
