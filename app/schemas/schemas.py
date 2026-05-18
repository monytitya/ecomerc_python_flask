from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class BaseConfig:
    from_attributes = True

# AboutUs
class AboutUsBase(BaseModel):
    about_heading: str
    about_short_desc: str
    about_desc: str

class AboutUsCreate(AboutUsBase):
    pass

class AboutUs(AboutUsBase):
    about_id: int
    class Config(BaseConfig): pass

# Admin
class AdminBase(BaseModel):
    admin_name: str
    admin_email: str
    admin_contact: str
    admin_country: str
    admin_job: str
    admin_about: str

class AdminCreate(AdminBase):
    admin_pass: str
    admin_image: str

class Admin(AdminBase):
    admin_id: int
    admin_image: str
    class Config(BaseConfig): pass

# BundleProductRelation
class BundleProductRelationBase(BaseModel):
    rel_title: str
    product_id: int
    bundle_id: int

class BundleProductRelationCreate(BundleProductRelationBase):
    pass

class BundleProductRelation(BundleProductRelationBase):
    rel_id: int
    class Config(BaseConfig): pass

# Cart
class CartBase(BaseModel):
    p_id: int
    ip_add: str
    qty: int
    p_price: str
    size: str

class CartCreate(CartBase):
    pass

class Cart(CartBase):
    class Config(BaseConfig): pass

# Category
class CategoryBase(BaseModel):
    cat_title: str
    cat_top: str

class CategoryCreate(CategoryBase):
    cat_image: str

class Category(CategoryBase):
    cat_id: int
    cat_image: str
    class Config(BaseConfig): pass

# ContactUs
class ContactUsBase(BaseModel):
    contact_email: str
    contact_heading: str
    contact_desc: str

class ContactUsCreate(ContactUsBase):
    pass

class ContactUs(ContactUsBase):
    contact_id: int
    class Config(BaseConfig): pass

# Coupon
class CouponBase(BaseModel):
    product_id: int
    coupon_title: str
    coupon_price: str
    coupon_code: str
    coupon_limit: int
    coupon_used: int

class CouponCreate(CouponBase):
    pass

class Coupon(CouponBase):
    coupon_id: int
    class Config(BaseConfig): pass

# Customer
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
    customer_image: str
    customer_ip: str
    customer_confirm_code: str
    class Config(BaseConfig): pass

# CustomerOrder
class OrderBase(BaseModel):
    customer_id: int
    due_amount: float
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

# EnquiryType
class EnquiryTypeBase(BaseModel):
    enquiry_title: str

class EnquiryTypeCreate(EnquiryTypeBase):
    pass

class EnquiryType(EnquiryTypeBase):
    enquiry_id: int
    class Config(BaseConfig): pass

# Manufacturer
class ManufacturerBase(BaseModel):
    manufacturer_title: str
    manufacturer_top: str

class ManufacturerCreate(ManufacturerBase):
    manufacturer_image: str

class Manufacturer(ManufacturerBase):
    manufacturer_id: int
    manufacturer_image: str
    class Config(BaseConfig): pass

# Payment
class PaymentBase(BaseModel):
    invoice_no: int
    amount: float
    payment_mode: str
    ref_no: str
    code: int
    payment_date: str

class PaymentCreate(PaymentBase):
    pass

class Payment(PaymentBase):
    payment_id: int
    class Config(BaseConfig): pass

# PendingOrder
class PendingOrderBase(BaseModel):
    customer_id: int
    invoice_no: int
    product_id: str
    qty: int
    size: str
    order_status: str

class PendingOrderCreate(PendingOrderBase):
    pass

class PendingOrder(PendingOrderBase):
    order_id: int
    class Config(BaseConfig): pass

# Product
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
    p_cat_id: int
    date: datetime
    product_img1: str
    product_img2: str
    product_img3: str
    product_video: str
    product_keywords: str
    product_label: str
    class Config(BaseConfig): pass

# ProductCategory
class ProductCategoryBase(BaseModel):
    p_cat_title: str
    p_cat_top: str

class ProductCategoryCreate(ProductCategoryBase):
    p_cat_image: str

class ProductCategory(ProductCategoryBase):
    p_cat_id: int
    p_cat_image: str
    class Config(BaseConfig): pass

# Store
class StoreBase(BaseModel):
    store_title: str
    store_desc: str
    store_button: str
    store_url: str

class StoreCreate(StoreBase):
    store_image: str

class Store(StoreBase):
    store_id: int
    store_image: str
    class Config(BaseConfig): pass

# Term
class TermBase(BaseModel):
    term_title: str
    term_link: str
    term_desc: str

class TermCreate(TermBase):
    pass

class Term(TermBase):
    term_id: int
    class Config(BaseConfig): pass

# Wishlist
class WishlistBase(BaseModel):
    customer_id: int
    product_id: int

class WishlistCreate(WishlistBase):
    pass

class Wishlist(WishlistBase):
    wishlist_id: int
    class Config(BaseConfig): pass

# ==================== Bakong Payment Gateway (Checkout Flow) ====================

class BakongCheckoutRequest(BaseModel):
    """
    Step 1: Customer initiates checkout.
    Creates an order + generates Bakong KHQR QR code in one call.
    """
    customer_id: int
    invoice_no: int
    qty: int
    size: str = "M"
    amount: float                       # Total due amount
    currency: str = "USD"               # USD or KHR
    store_label: str = "Ecomerc Shop"
    phone_number: str = "85512345678"

class BakongCheckoutResponse(BaseModel):
    """Response after checkout: order created + QR ready for scanning."""
    order_id: int
    invoice_no: int
    amount: float
    currency: str
    order_status: str
    qr_string: str
    md5: str
    deeplink: str
    message: str

class BakongCheckStatusRequest(BaseModel):
    """Step 2: Frontend polls this every ~5s with the MD5 hash."""
    md5: str

class BakongCheckStatusResponse(BaseModel):
    """Response from payment status check."""
    md5: str
    is_paid: bool
    status: str                         # "Paid" | "Unpaid"
    order_id: Optional[int] = None
    order_status: Optional[str] = None
    # Bakong transaction details (populated when paid)
    bakong_hash: Optional[str] = None
    from_account: Optional[str] = None
    to_account: Optional[str] = None
    currency: Optional[str] = None
    amount: Optional[float] = None
    description: Optional[str] = None

class BakongTransactionSchema(BaseModel):
    """Full Bakong transaction record from DB."""
    transaction_id: int
    order_id: int
    customer_id: int
    md5: str
    qr_string: str
    deeplink: Optional[str] = None
    currency: str
    amount: float
    payment_status: str
    bakong_hash: Optional[str] = None
    from_account: Optional[str] = None
    to_account: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    class Config(BaseConfig): pass

# Keep the simple generate/check for standalone use (no order linking)
class BakongPaymentRequest(BaseModel):
    """Request body for generating a standalone Bakong KHQR QR code."""
    amount: float
    currency: str = "USD"
    bill_number: str
    store_label: str = "Ecomerc Shop"
    phone_number: str = "85512345678"

class BakongPaymentResponse(BaseModel):
    """Response from standalone QR code generation."""
    qr_string: str
    md5: str
    deeplink: str
    currency: str
    amount: float
    status: str

class BakongCheckPaymentRequest(BaseModel):
    """Request body for checking payment status by MD5."""
    md5: str

