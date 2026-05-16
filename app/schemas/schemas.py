from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class CategoryBase(BaseModel):
    cat_title: str
    cat_top: str
    cat_image: str

class CategoryCreate(CategoryBase):
    pass

class Category(CategoryBase):
    cat_id: int

    class Config:
        from_attributes = True

class ProductBase(BaseModel):
    product_title: str
    product_url: str
    product_price: float
    product_psp_price: Optional[float] = None
    product_desc: Optional[str] = None
    cat_id: int
    status: Optional[str] = None

class ProductCreate(ProductBase):
    pass

class Product(ProductBase):
    product_id: int
    date: datetime

    class Config:
        from_attributes = True

class CustomerBase(BaseModel):
    customer_name: str
    customer_email: str
    customer_country: Optional[str] = None
    customer_city: Optional[str] = None

class CustomerCreate(CustomerBase):
    customer_pass: str

class Customer(CustomerBase):
    customer_id: int

    class Config:
        from_attributes = True
