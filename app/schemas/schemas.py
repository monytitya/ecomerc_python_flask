from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# --- Common Config ---
class BaseConfig:
    from_attributes = True

# --- Category ---
class CategoryBase(BaseModel):
    cat_title: str
    cat_top: str
    cat_image: str

class CategoryCreate(CategoryBase):
    pass

class Category(CategoryBase):
    cat_id: int
    class Config(BaseConfig): pass

# --- Product ---
class ProductBase(BaseModel):
    product_title: str
    product_url: str
    product_price: int
    product_psp_price: int
    product_desc: str
    product_features: str
    cat_id: int
    manufacturer_id: int
    status: str

class ProductCreate(ProductBase):
    p_cat_id: int
    product_img1: str
    product_img2: str
    product_img3: str
    product_video: str
    product_keywords: str
    product_label: str

class Product(ProductBase):
    product_id: int
    date: datetime
    product_img1: str
    product_img2: str
    product_img3: str
    class Config(BaseConfig): pass

# --- Customer ---
class CustomerBase(BaseModel):
    customer_name: str
    customer_email: str
    customer_country: str
    customer_city: str
    customer_contact: str
    customer_address: str

class CustomerCreate(CustomerBase):
    customer_pass: str
    customer_image: str
    customer_ip: str
    customer_confirm_code: str

class Customer(CustomerBase):
    customer_id: int
    class Config(BaseConfig): pass

# --- Order ---
class OrderBase(BaseModel):
    customer_id: int
    due_amount: int
    invoice_no: int
    qty: int
    size: str
    order_status: str

class OrderCreate(OrderBase):
    pass

class Order(OrderBase):
    order_id: int
    order_date: datetime
    class Config(BaseConfig): pass
