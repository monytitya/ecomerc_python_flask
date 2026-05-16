from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, TIMESTAMP
from sqlalchemy.orm import relationship
from datetime import datetime
from ..db.session import Base

class AboutUs(Base):
    __tablename__ = "about_us"
    about_id = Column(Integer, primary_key=True, autoincrement=True)
    about_heading = Column(Text, nullable=False)
    about_short_desc = Column(Text, nullable=False)
    about_desc = Column(Text, nullable=False)

class Admin(Base):
    __tablename__ = "admins"
    admin_id = Column(Integer, primary_key=True, autoincrement=True)
    admin_name = Column(String(255), nullable=False)
    admin_email = Column(String(255), nullable=False)
    admin_pass = Column(String(255), nullable=False)
    admin_image = Column(Text, nullable=False)
    admin_contact = Column(String(255), nullable=False)
    admin_country = Column(Text, nullable=False)
    admin_job = Column(String(255), nullable=False)
    admin_about = Column(Text, nullable=False)

class BundleProductRelation(Base):
    __tablename__ = "bundle_product_relation"
    rel_id = Column(Integer, primary_key=True, autoincrement=True)
    rel_title = Column(String(255), nullable=False)
    product_id = Column(Integer, nullable=False)
    bundle_id = Column(Integer, nullable=False)

class Cart(Base):
    __tablename__ = "cart"
    p_id = Column(Integer, primary_key=True)
    ip_add = Column(String(255), nullable=False)
    qty = Column(Integer, nullable=False)
    p_price = Column(String(255), nullable=False)
    size = Column(Text, nullable=False)

class Category(Base):
    __tablename__ = "categories"
    cat_id = Column(Integer, primary_key=True, autoincrement=True)
    cat_title = Column(Text, nullable=False)
    cat_top = Column(Text, nullable=False)
    cat_image = Column(Text, nullable=False)
    
    products = relationship("Product", back_populates="category")

class ContactUs(Base):
    __tablename__ = "contact_us"
    contact_id = Column(Integer, primary_key=True, autoincrement=True)
    contact_email = Column(Text, nullable=False)
    contact_heading = Column(Text, nullable=False)
    contact_desc = Column(Text, nullable=False)

class Coupon(Base):
    __tablename__ = "coupons"
    coupon_id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, nullable=False)
    coupon_title = Column(String(255), nullable=False)
    coupon_price = Column(String(255), nullable=False)
    coupon_code = Column(String(255), nullable=False)
    coupon_limit = Column(Integer, nullable=False)
    coupon_used = Column(Integer, nullable=False)

class Customer(Base):
    __tablename__ = "customers"
    customer_id = Column(Integer, primary_key=True, autoincrement=True)
    customer_name = Column(String(255), nullable=False)
    customer_email = Column(String(255), nullable=False)
    customer_pass = Column(String(255), nullable=False)
    customer_country = Column(Text, nullable=False)
    customer_city = Column(Text, nullable=False)
    customer_contact = Column(String(255), nullable=False)
    customer_address = Column(Text, nullable=False)
    customer_image = Column(Text, nullable=False)
    customer_ip = Column(String(255), nullable=False)
    customer_confirm_code = Column(Text, nullable=False)

class CustomerOrder(Base):
    __tablename__ = "customer_orders"
    order_id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, nullable=False)
    due_amount = Column(Integer, nullable=False)
    invoice_no = Column(Integer, nullable=False)
    qty = Column(Integer, nullable=False)
    size = Column(Text, nullable=False)
    order_date = Column(TIMESTAMP, default=datetime.utcnow)
    order_status = Column(Text, nullable=False)

class EnquiryType(Base):
    __tablename__ = "enquiry_types"
    enquiry_id = Column(Integer, primary_key=True, autoincrement=True)
    enquiry_title = Column(String(255), nullable=False)

class Manufacturer(Base):
    __tablename__ = "manufacturers"
    manufacturer_id = Column(Integer, primary_key=True, autoincrement=True)
    manufacturer_title = Column(Text, nullable=False)
    manufacturer_top = Column(Text, nullable=False)
    manufacturer_image = Column(Text, nullable=False)

class Payment(Base):
    __tablename__ = "payments"
    payment_id = Column(Integer, primary_key=True, autoincrement=True)
    invoice_no = Column(Integer, nullable=False)
    amount = Column(Integer, nullable=False)
    payment_mode = Column(Text, nullable=False)
    ref_no = Column(Integer, nullable=False)
    code = Column(Integer, nullable=False)
    payment_date = Column(Text, nullable=False)

class PendingOrder(Base):
    __tablename__ = "pending_orders"
    order_id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, nullable=False)
    invoice_no = Column(Integer, nullable=False)
    product_id = Column(Text, nullable=False)
    qty = Column(Integer, nullable=False)
    size = Column(Text, nullable=False)
    order_status = Column(Text, nullable=False)

class Product(Base):
    __tablename__ = "products"
    product_id = Column(Integer, primary_key=True, autoincrement=True)
    p_cat_id = Column(Integer, nullable=False)
    cat_id = Column(Integer, ForeignKey("categories.cat_id"), nullable=False)
    manufacturer_id = Column(Integer, nullable=False)
    date = Column(TIMESTAMP, default=datetime.utcnow)
    product_title = Column(Text, nullable=False)
    product_url = Column(Text, nullable=False)
    product_img1 = Column(Text, nullable=False)
    product_img2 = Column(Text, nullable=False)
    product_img3 = Column(Text, nullable=False)
    product_price = Column(Integer, nullable=False)
    product_psp_price = Column(Integer, nullable=False)
    product_desc = Column(Text, nullable=False)
    product_features = Column(Text, nullable=False)
    product_video = Column(Text, nullable=False)
    product_keywords = Column(Text, nullable=False)
    product_label = Column(Text, nullable=False)
    status = Column(String(255), nullable=False)
    
    category = relationship("Category", back_populates="products")

class ProductCategory(Base):
    __tablename__ = "product_categories"
    p_cat_id = Column(Integer, primary_key=True, autoincrement=True)
    p_cat_title = Column(Text, nullable=False)
    p_cat_top = Column(Text, nullable=False)
    p_cat_image = Column(Text, nullable=False)

class Store(Base):
    __tablename__ = "store"
    store_id = Column(Integer, primary_key=True, autoincrement=True)
    store_title = Column(String(255), nullable=False)
    store_image = Column(String(255), nullable=False)
    store_desc = Column(Text, nullable=False)
    store_button = Column(String(255), nullable=False)
    store_url = Column(String(255), nullable=False)

class Term(Base):
    __tablename__ = "terms"
    term_id = Column(Integer, primary_key=True, autoincrement=True)
    term_title = Column(String(100), nullable=False)
    term_link = Column(String(100), nullable=False)
    term_desc = Column(Text, nullable=False)

class Wishlist(Base):
    __tablename__ = "wishlist"
    wishlist_id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, nullable=False)
    product_id = Column(Integer, nullable=False)
