from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from ..db.session import Base

class Category(Base):
    __tablename__ = "categories"

    cat_id = Column(Integer, primary_key=True, index=True)
    cat_title = Column(Text, nullable=False)
    cat_top = Column(String(10), nullable=False)
    cat_image = Column(Text, nullable=False)

    products = relationship("Product", back_populates="category")

class Product(Base):
    __tablename__ = "products"

    product_id = Column(Integer, primary_key=True, index=True)
    p_cat_id = Column(Integer)  # Simplified for now
    cat_id = Column(Integer, ForeignKey("categories.cat_id"))
    manufacturer_id = Column(Integer)
    date = Column(DateTime, default=datetime.utcnow)
    product_title = Column(Text, nullable=False)
    product_url = Column(Text, nullable=False)
    product_img1 = Column(Text)
    product_img2 = Column(Text)
    product_img3 = Column(Text)
    product_price = Column(Float, nullable=False)
    product_psp_price = Column(Float)
    product_desc = Column(Text)
    product_features = Column(Text)
    product_video = Column(Text)
    product_keywords = Column(Text)
    product_label = Column(String(255))
    status = Column(String(255))

    category = relationship("Category", back_populates="products")

class Customer(Base):
    __tablename__ = "customers"

    customer_id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String(255), nullable=False)
    customer_email = Column(String(255), unique=True, index=True, nullable=False)
    customer_pass = Column(String(255), nullable=False)
    customer_country = Column(Text)
    customer_city = Column(Text)
    customer_contact = Column(String(255))
    customer_address = Column(Text)
    customer_image = Column(Text)
    customer_ip = Column(String(255))
    customer_confirm_code = Column(Text)
