# db/models.py
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Customer(Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    region = Column(String, nullable=False)
    address = Column(String)
    orders = relationship("Order", back_populates="customer")

class Driver(Base):
    __tablename__ = "drivers"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    is_available = Column(Boolean, default=True)
    region = Column(String, nullable=False)
    address = Column(String)
    orders = relationship("Order", back_populates="driver")

class Restaurant(Base):
    __tablename__ = "restaurants"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    region = Column(String, nullable=False)
    address = Column(String)
    cuisine = Column(String)
    orders = relationship("Order", back_populates="restaurant")

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), nullable=False)
    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=True)
    order_time = Column(DateTime, default=datetime.utcnow)
    order_status = Column(String, default="pending")
    customer_lat = Column(Float)
    customer_lng = Column(Float)
    restaurant_lat = Column(Float)
    restaurant_lng = Column(Float)
    region = Column(String)
    customer = relationship("Customer", back_populates="orders")
    restaurant = relationship("Restaurant", back_populates="orders")
    driver = relationship("Driver", back_populates="orders")
