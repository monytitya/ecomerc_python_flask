from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, StreamingResponse, HTMLResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import shutil
import uuid
import hashlib
import json
import io
import base64
from datetime import date
from .db.session import engine, get_db, Base
from .models import models
from .schemas import schemas
from .services.bakong_service import (
    generate_qr,
    generate_deeplink,
    check_payment_status,
    get_payment_info
)
from fastapi.middleware.cors import CORSMiddleware

try:
    models.Base.metadata.create_all(bind=engine)
    print("Database tables synchronized.")
except Exception as e:
    print(f"Warning: Could not create tables on startup: {e}")
    print("Ensure your MySQL credentials in .env are correct.")

app = FastAPI(title="Ecomerc API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

def _save_upload(file: UploadFile) -> str:
    """Save an UploadFile to UPLOAD_DIR with a unique prefix and return the filename."""
    ext = os.path.splitext(file.filename)[1] if file.filename else ""
    unique_name = f"{uuid.uuid4().hex[:8]}_{file.filename or ('upload' + ext)}"
    dest = os.path.join(UPLOAD_DIR, unique_name)
    with open(dest, "wb") as buf:
        shutil.copyfileobj(file.file, buf)
    return unique_name


@app.get("/")
def read_root():
    return {
        "message": "Welcome to Ecomerc API",
        "documentation": "/swagger-ui"
    }


@app.post("/upload", tags=["Image Upload"])
def upload_file(file: UploadFile = File(...)):
    saved = _save_upload(file)
    return {
        "filename": saved,
        "url": f"/uploads/{saved}",
        "status": "success"
    }

@app.get("/uploads/list", tags=["Image Upload"])
def list_uploaded_images():
    """List all uploaded images."""
    files = os.listdir(UPLOAD_DIR)
    return [{"filename": f, "url": f"/uploads/{f}"} for f in files if not f.startswith(".")]

@app.delete("/uploads/{filename}", tags=["Image Upload"])
def delete_uploaded_image(filename: str):
    """Delete a specific uploaded image."""
    path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="File not found")
    os.remove(path)
    return {"message": f"'{filename}' deleted successfully"}


@app.get("/about_us", response_model=List[schemas.AboutUs], tags=["AboutUs"])
def get_about_us(db: Session = Depends(get_db)):
    return db.query(models.AboutUs).all()

@app.get("/about_us/{about_id}", response_model=schemas.AboutUs, tags=["AboutUs"])
def get_about_us_by_id(about_id: int, db: Session = Depends(get_db)):
    item = db.query(models.AboutUs).filter(models.AboutUs.about_id == about_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="AboutUs not found")
    return item

@app.post("/about_us", response_model=schemas.AboutUs, tags=["AboutUs"])
def create_about_us(item: schemas.AboutUsCreate, db: Session = Depends(get_db)):
    new_item = models.AboutUs(**item.model_dump())
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return new_item

@app.put("/about_us/{about_id}", response_model=schemas.AboutUs, tags=["AboutUs"])
def update_about_us(about_id: int, item: schemas.AboutUsCreate, db: Session = Depends(get_db)):
    db_item = db.query(models.AboutUs).filter(models.AboutUs.about_id == about_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="AboutUs not found")
    for key, value in item.model_dump().items():
        setattr(db_item, key, value)
    db.commit()
    db.refresh(db_item)
    return db_item

@app.delete("/about_us/{about_id}", tags=["AboutUs"])
def delete_about_us(about_id: int, db: Session = Depends(get_db)):
    db_item = db.query(models.AboutUs).filter(models.AboutUs.about_id == about_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="AboutUs not found")
    db.delete(db_item)
    db.commit()
    return {"message": "AboutUs deleted successfully"}


@app.get("/admins", response_model=List[schemas.Admin], tags=["Admin"])
def get_admins(db: Session = Depends(get_db)):
    return db.query(models.Admin).all()

@app.get("/admins/{admin_id}", response_model=schemas.Admin, tags=["Admin"])
def get_admin(admin_id: int, db: Session = Depends(get_db)):
    admin = db.query(models.Admin).filter(models.Admin.admin_id == admin_id).first()
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")
    return admin

@app.post("/admins", response_model=schemas.Admin, tags=["Admin"])
def create_admin(
    admin_name: str = Form(...),
    admin_email: str = Form(...),
    admin_pass: str = Form(...),
    admin_contact: str = Form(...),
    admin_country: str = Form(...),
    admin_job: str = Form(...),
    admin_about: str = Form(...),
    admin_image: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Create a new admin with image upload."""
    saved_filename = _save_upload(admin_image)
    new_admin = models.Admin(
        admin_name=admin_name,
        admin_email=admin_email,
        admin_pass=admin_pass,
        admin_contact=admin_contact,
        admin_country=admin_country,
        admin_job=admin_job,
        admin_about=admin_about,
        admin_image=saved_filename,
    )
    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)
    return new_admin

@app.put("/admins/{admin_id}", response_model=schemas.Admin, tags=["Admin"])
def update_admin(
    admin_id: int,
    admin_name: str = Form(...),
    admin_email: str = Form(...),
    admin_pass: str = Form(...),
    admin_contact: str = Form(...),
    admin_country: str = Form(...),
    admin_job: str = Form(...),
    admin_about: str = Form(...),
    admin_image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    """Update an admin. Image is optional — if omitted, existing image is kept."""
    db_admin = db.query(models.Admin).filter(models.Admin.admin_id == admin_id).first()
    if not db_admin:
        raise HTTPException(status_code=404, detail="Admin not found")
    db_admin.admin_name = admin_name
    db_admin.admin_email = admin_email
    db_admin.admin_pass = admin_pass
    db_admin.admin_contact = admin_contact
    db_admin.admin_country = admin_country
    db_admin.admin_job = admin_job
    db_admin.admin_about = admin_about
    if admin_image and admin_image.filename:
        db_admin.admin_image = _save_upload(admin_image)
    db.commit()
    db.refresh(db_admin)
    return db_admin

@app.delete("/admins/{admin_id}", tags=["Admin"])
def delete_admin(admin_id: int, db: Session = Depends(get_db)):
    db_admin = db.query(models.Admin).filter(models.Admin.admin_id == admin_id).first()
    if not db_admin:
        raise HTTPException(status_code=404, detail="Admin not found")
    img_path = os.path.join(UPLOAD_DIR, db_admin.admin_image) if db_admin.admin_image else None
    db.delete(db_admin)
    db.commit()
    if img_path and os.path.isfile(img_path):
        os.remove(img_path)
    return {"message": "Admin deleted successfully"}


@app.get("/bundle_product_relations", response_model=List[schemas.BundleProductRelation], tags=["BundleProductRelation"])
def get_bundle_product_relations(db: Session = Depends(get_db)):
    return db.query(models.BundleProductRelation).all()

@app.get("/bundle_product_relations/{rel_id}", response_model=schemas.BundleProductRelation, tags=["BundleProductRelation"])
def get_bundle_product_relation(rel_id: int, db: Session = Depends(get_db)):
    rel = db.query(models.BundleProductRelation).filter(models.BundleProductRelation.rel_id == rel_id).first()
    if not rel:
        raise HTTPException(status_code=404, detail="Relation not found")
    return rel

@app.post("/bundle_product_relations", response_model=schemas.BundleProductRelation, tags=["BundleProductRelation"])
def create_bundle_product_relation(item: schemas.BundleProductRelationCreate, db: Session = Depends(get_db)):
    new_rel = models.BundleProductRelation(**item.model_dump())
    db.add(new_rel)
    db.commit()
    db.refresh(new_rel)
    return new_rel

@app.put("/bundle_product_relations/{rel_id}", response_model=schemas.BundleProductRelation, tags=["BundleProductRelation"])
def update_bundle_product_relation(rel_id: int, item: schemas.BundleProductRelationCreate, db: Session = Depends(get_db)):
    db_rel = db.query(models.BundleProductRelation).filter(models.BundleProductRelation.rel_id == rel_id).first()
    if not db_rel:
        raise HTTPException(status_code=404, detail="Relation not found")
    for key, value in item.model_dump().items():
        setattr(db_rel, key, value)
    db.commit()
    db.refresh(db_rel)
    return db_rel

@app.delete("/bundle_product_relations/{rel_id}", tags=["BundleProductRelation"])
def delete_bundle_product_relation(rel_id: int, db: Session = Depends(get_db)):
    db_rel = db.query(models.BundleProductRelation).filter(models.BundleProductRelation.rel_id == rel_id).first()
    if not db_rel:
        raise HTTPException(status_code=404, detail="Relation not found")
    db.delete(db_rel)
    db.commit()
    return {"message": "Relation deleted successfully"}


@app.get("/cart", response_model=List[schemas.Cart], tags=["Cart"])
def get_cart_items(db: Session = Depends(get_db)):
    return db.query(models.Cart).all()

@app.get("/cart/{p_id}", response_model=schemas.Cart, tags=["Cart"])
def get_cart_item(p_id: int, db: Session = Depends(get_db)):
    item = db.query(models.Cart).filter(models.Cart.p_id == p_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    return item

@app.post("/cart", response_model=schemas.Cart, tags=["Cart"])
def create_cart_item(item: schemas.CartCreate, db: Session = Depends(get_db)):
    db_item = db.query(models.Cart).filter(models.Cart.p_id == item.p_id).first()
    if db_item:
        db_item.qty += item.qty
        db.commit()
        db.refresh(db_item)
        return db_item
    
    new_item = models.Cart(**item.model_dump())
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return new_item

@app.put("/cart/{p_id}", response_model=schemas.Cart, tags=["Cart"])
def update_cart_item(p_id: int, item: schemas.CartCreate, db: Session = Depends(get_db)):
    db_item = db.query(models.Cart).filter(models.Cart.p_id == p_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    for key, value in item.model_dump().items():
        setattr(db_item, key, value)
    db.commit()
    db.refresh(db_item)
    return db_item

@app.delete("/cart/{p_id}", tags=["Cart"])
def delete_cart_item(p_id: int, db: Session = Depends(get_db)):
    db_item = db.query(models.Cart).filter(models.Cart.p_id == p_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    db.delete(db_item)
    db.commit()
    return {"message": "Cart item deleted successfully"}


@app.get("/categories", response_model=List[schemas.Category], tags=["Category"])
def get_categories(db: Session = Depends(get_db)):
    return db.query(models.Category).all()

@app.get("/categories/{cat_id}", response_model=schemas.Category, tags=["Category"])
def get_category(cat_id: int, db: Session = Depends(get_db)):
    category = db.query(models.Category).filter(models.Category.cat_id == cat_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category

@app.get("/categories/{cat_id}/products", response_model=List[schemas.Product], tags=["Category"])
def get_products_by_category(cat_id: int, db: Session = Depends(get_db)):
    return db.query(models.Product).filter(models.Product.cat_id == cat_id).all()

@app.post("/categories", response_model=schemas.Category, tags=["Category"])
def create_category(
    cat_title: str = Form(...),
    cat_top: str = Form("no"),
    cat_image: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    saved = _save_upload(cat_image)
    new_cat = models.Category(cat_title=cat_title, cat_top=cat_top, cat_image=saved)
    db.add(new_cat)
    db.commit()
    db.refresh(new_cat)
    return new_cat

@app.put("/categories/{cat_id}", response_model=schemas.Category, tags=["Category"])
def update_category(
    cat_id: int,
    cat_title: str = Form(...),
    cat_top: str = Form("no"),
    cat_image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    db_cat = db.query(models.Category).filter(models.Category.cat_id == cat_id).first()
    if not db_cat:
        raise HTTPException(status_code=404, detail="Category not found")
    db_cat.cat_title = cat_title
    db_cat.cat_top = cat_top
    if cat_image and cat_image.filename:
        db_cat.cat_image = _save_upload(cat_image)
    db.commit()
    db.refresh(db_cat)
    return db_cat

@app.delete("/categories/{cat_id}", tags=["Category"])
def delete_category(cat_id: int, db: Session = Depends(get_db)):
    db_cat = db.query(models.Category).filter(models.Category.cat_id == cat_id).first()
    if not db_cat:
        raise HTTPException(status_code=404, detail="Category not found")
    db.delete(db_cat)
    db.commit()
    return {"message": "Category deleted successfully"}


@app.get("/contact_us", response_model=List[schemas.ContactUs], tags=["ContactUs"])
def get_contact_messages(db: Session = Depends(get_db)):
    return db.query(models.ContactUs).all()

@app.get("/contact_us/{contact_id}", response_model=schemas.ContactUs, tags=["ContactUs"])
def get_contact_message(contact_id: int, db: Session = Depends(get_db)):
    msg = db.query(models.ContactUs).filter(models.ContactUs.contact_id == contact_id).first()
    if not msg:
        raise HTTPException(status_code=404, detail="Contact entry not found")
    return msg

@app.post("/contact_us", response_model=schemas.ContactUs, tags=["ContactUs"])
def create_contact_message(item: schemas.ContactUsCreate, db: Session = Depends(get_db)):
    new_msg = models.ContactUs(**item.model_dump())
    db.add(new_msg)
    db.commit()
    db.refresh(new_msg)
    return new_msg

@app.put("/contact_us/{contact_id}", response_model=schemas.ContactUs, tags=["ContactUs"])
def update_contact_message(contact_id: int, item: schemas.ContactUsCreate, db: Session = Depends(get_db)):
    db_msg = db.query(models.ContactUs).filter(models.ContactUs.contact_id == contact_id).first()
    if not db_msg:
        raise HTTPException(status_code=404, detail="Contact entry not found")
    for key, value in item.model_dump().items():
        setattr(db_msg, key, value)
    db.commit()
    db.refresh(db_msg)
    return db_msg

@app.delete("/contact_us/{contact_id}", tags=["ContactUs"])
def delete_contact_message(contact_id: int, db: Session = Depends(get_db)):
    db_msg = db.query(models.ContactUs).filter(models.ContactUs.contact_id == contact_id).first()
    if not db_msg:
        raise HTTPException(status_code=404, detail="Contact entry not found")
    db.delete(db_msg)
    db.commit()
    return {"message": "Contact entry deleted successfully"}


@app.get("/coupons", response_model=List[schemas.Coupon], tags=["Coupon"])
def get_coupons(db: Session = Depends(get_db)):
    return db.query(models.Coupon).all()

@app.get("/coupons/{coupon_id}", response_model=schemas.Coupon, tags=["Coupon"])
def get_coupon(coupon_id: int, db: Session = Depends(get_db)):
    coupon = db.query(models.Coupon).filter(models.Coupon.coupon_id == coupon_id).first()
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")
    return coupon

@app.post("/coupons", response_model=schemas.Coupon, tags=["Coupon"])
def create_coupon(item: schemas.CouponCreate, db: Session = Depends(get_db)):
    new_coupon = models.Coupon(**item.model_dump())
    db.add(new_coupon)
    db.commit()
    db.refresh(new_coupon)
    return new_coupon

@app.put("/coupons/{coupon_id}", response_model=schemas.Coupon, tags=["Coupon"])
def update_coupon(coupon_id: int, item: schemas.CouponCreate, db: Session = Depends(get_db)):
    db_coupon = db.query(models.Coupon).filter(models.Coupon.coupon_id == coupon_id).first()
    if not db_coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")
    for key, value in item.model_dump().items():
        setattr(db_coupon, key, value)
    db.commit()
    db.refresh(db_coupon)
    return db_coupon

@app.delete("/coupons/{coupon_id}", tags=["Coupon"])
def delete_coupon(coupon_id: int, db: Session = Depends(get_db)):
    db_coupon = db.query(models.Coupon).filter(models.Coupon.coupon_id == coupon_id).first()
    if not db_coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")
    db.delete(db_coupon)
    db.commit()
    return {"message": "Coupon deleted successfully"}


@app.get("/customers", response_model=List[schemas.Customer], tags=["Customer"])
def get_customers(db: Session = Depends(get_db)):
    return db.query(models.Customer).all()

@app.get("/customers/{customer_id}", response_model=schemas.Customer, tags=["Customer"])
def get_customer(customer_id: int, db: Session = Depends(get_db)):
    customer = db.query(models.Customer).filter(models.Customer.customer_id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer

@app.post("/customers/register", response_model=schemas.Customer, tags=["Customer"])
def register_customer(
    customer_name: str = Form(...),
    customer_email: str = Form(...),
    customer_pass: str = Form(...),
    customer_country: str = Form(...),
    customer_city: str = Form(...),
    customer_contact: str = Form(...),
    customer_address: str = Form(...),
    customer_ip: str = Form(...),
    customer_confirm_code: str = Form(...),
    customer_image: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Register a new customer with image upload."""
    db_customer = db.query(models.Customer).filter(models.Customer.customer_email == customer_email).first()
    if db_customer:
        raise HTTPException(status_code=400, detail="Email already registered")

    saved_filename = _save_upload(customer_image)
    new_customer = models.Customer(
        customer_name=customer_name,
        customer_email=customer_email,
        customer_pass=customer_pass,
        customer_country=customer_country,
        customer_city=customer_city,
        customer_contact=customer_contact,
        customer_address=customer_address,
        customer_image=saved_filename,
        customer_ip=customer_ip,
        customer_confirm_code=customer_confirm_code,
    )
    db.add(new_customer)
    db.commit()
    db.refresh(new_customer)
    return new_customer

@app.put("/customers/{customer_id}", response_model=schemas.Customer, tags=["Customer"])
def update_customer(
    customer_id: int,
    customer_name: str = Form(...),
    customer_email: str = Form(...),
    customer_pass: str = Form(...),
    customer_country: str = Form(...),
    customer_city: str = Form(...),
    customer_contact: str = Form(...),
    customer_address: str = Form(...),
    customer_ip: str = Form(...),
    customer_confirm_code: str = Form(...),
    customer_image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    """Update a customer. Image is optional — if omitted, existing image is kept."""
    db_customer = db.query(models.Customer).filter(models.Customer.customer_id == customer_id).first()
    if not db_customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    db_customer.customer_name = customer_name
    db_customer.customer_email = customer_email
    db_customer.customer_pass = customer_pass
    db_customer.customer_country = customer_country
    db_customer.customer_city = customer_city
    db_customer.customer_contact = customer_contact
    db_customer.customer_address = customer_address
    db_customer.customer_ip = customer_ip
    db_customer.customer_confirm_code = customer_confirm_code
    if customer_image and customer_image.filename:
        db_customer.customer_image = _save_upload(customer_image)
    db.commit()
    db.refresh(db_customer)
    return db_customer

@app.delete("/customers/{customer_id}", tags=["Customer"])
def delete_customer(customer_id: int, db: Session = Depends(get_db)):
    db_customer = db.query(models.Customer).filter(models.Customer.customer_id == customer_id).first()
    if not db_customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    # Also delete the image file if it exists
    img_path = os.path.join(UPLOAD_DIR, db_customer.customer_image) if db_customer.customer_image else None
    db.delete(db_customer)
    db.commit()
    if img_path and os.path.isfile(img_path):
        os.remove(img_path)
    return {"message": "Customer deleted successfully"}


@app.get("/orders", response_model=List[schemas.Order], tags=["CustomerOrder"])
def get_orders(db: Session = Depends(get_db)):
    return db.query(models.CustomerOrder).all()

@app.get("/orders/{order_id}", response_model=schemas.Order, tags=["CustomerOrder"])
def get_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(models.CustomerOrder).filter(models.CustomerOrder.order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@app.get("/orders/customer/{customer_id}", response_model=List[schemas.Order], tags=["CustomerOrder"])
def get_customer_orders(customer_id: int, db: Session = Depends(get_db)):
    return db.query(models.CustomerOrder).filter(models.CustomerOrder.customer_id == customer_id).all()

@app.post("/orders", response_model=schemas.Order, tags=["CustomerOrder"])
def create_order(order: schemas.OrderCreate, db: Session = Depends(get_db)):
    new_order = models.CustomerOrder(**order.model_dump())
    db.add(new_order)
    db.commit()
    db.refresh(new_order)
    return new_order

@app.put("/orders/{order_id}", response_model=schemas.Order, tags=["CustomerOrder"])
def update_order(order_id: int, item: schemas.OrderCreate, db: Session = Depends(get_db)):
    db_order = db.query(models.CustomerOrder).filter(models.CustomerOrder.order_id == order_id).first()
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")
    for key, value in item.model_dump().items():
        setattr(db_order, key, value)
    db.commit()
    db.refresh(db_order)
    return db_order

@app.delete("/orders/{order_id}", tags=["CustomerOrder"])
def delete_order(order_id: int, db: Session = Depends(get_db)):
    db_order = db.query(models.CustomerOrder).filter(models.CustomerOrder.order_id == order_id).first()
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")
    db.delete(db_order)
    db.commit()
    return {"message": "Order deleted successfully"}


@app.get("/enquiry_types", response_model=List[schemas.EnquiryType], tags=["EnquiryType"])
def get_enquiry_types(db: Session = Depends(get_db)):
    return db.query(models.EnquiryType).all()

@app.get("/enquiry_types/{enquiry_id}", response_model=schemas.EnquiryType, tags=["EnquiryType"])
def get_enquiry_type(enquiry_id: int, db: Session = Depends(get_db)):
    enquiry = db.query(models.EnquiryType).filter(models.EnquiryType.enquiry_id == enquiry_id).first()
    if not enquiry:
        raise HTTPException(status_code=404, detail="EnquiryType not found")
    return enquiry

@app.post("/enquiry_types", response_model=schemas.EnquiryType, tags=["EnquiryType"])
def create_enquiry_type(item: schemas.EnquiryTypeCreate, db: Session = Depends(get_db)):
    new_enquiry = models.EnquiryType(**item.model_dump())
    db.add(new_enquiry)
    db.commit()
    db.refresh(new_enquiry)
    return new_enquiry

@app.put("/enquiry_types/{enquiry_id}", response_model=schemas.EnquiryType, tags=["EnquiryType"])
def update_enquiry_type(enquiry_id: int, item: schemas.EnquiryTypeCreate, db: Session = Depends(get_db)):
    db_enquiry = db.query(models.EnquiryType).filter(models.EnquiryType.enquiry_id == enquiry_id).first()
    if not db_enquiry:
        raise HTTPException(status_code=404, detail="EnquiryType not found")
    for key, value in item.model_dump().items():
        setattr(db_enquiry, key, value)
    db.commit()
    db.refresh(db_enquiry)
    return db_enquiry

@app.delete("/enquiry_types/{enquiry_id}", tags=["EnquiryType"])
def delete_enquiry_type(enquiry_id: int, db: Session = Depends(get_db)):
    db_enquiry = db.query(models.EnquiryType).filter(models.EnquiryType.enquiry_id == enquiry_id).first()
    if not db_enquiry:
        raise HTTPException(status_code=404, detail="EnquiryType not found")
    db.delete(db_enquiry)
    db.commit()
    return {"message": "EnquiryType deleted successfully"}


@app.get("/manufacturers", response_model=List[schemas.Manufacturer], tags=["Manufacturer"])
def get_manufacturers(db: Session = Depends(get_db)):
    return db.query(models.Manufacturer).all()

@app.get("/manufacturers/{manufacturer_id}", response_model=schemas.Manufacturer, tags=["Manufacturer"])
def get_manufacturer(manufacturer_id: int, db: Session = Depends(get_db)):
    man = db.query(models.Manufacturer).filter(models.Manufacturer.manufacturer_id == manufacturer_id).first()
    if not man:
        raise HTTPException(status_code=404, detail="Manufacturer not found")
    return man

@app.post("/manufacturers", response_model=schemas.Manufacturer, tags=["Manufacturer"])
def create_manufacturer(
    manufacturer_title: str = Form(...),
    manufacturer_top: str = Form("no"),
    manufacturer_image: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    saved = _save_upload(manufacturer_image)
    new_man = models.Manufacturer(
        manufacturer_title=manufacturer_title,
        manufacturer_top=manufacturer_top,
        manufacturer_image=saved,
    )
    db.add(new_man)
    db.commit()
    db.refresh(new_man)
    return new_man

@app.put("/manufacturers/{manufacturer_id}", response_model=schemas.Manufacturer, tags=["Manufacturer"])
def update_manufacturer(
    manufacturer_id: int,
    manufacturer_title: str = Form(...),
    manufacturer_top: str = Form("no"),
    manufacturer_image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    db_man = db.query(models.Manufacturer).filter(models.Manufacturer.manufacturer_id == manufacturer_id).first()
    if not db_man:
        raise HTTPException(status_code=404, detail="Manufacturer not found")
    db_man.manufacturer_title = manufacturer_title
    db_man.manufacturer_top = manufacturer_top
    if manufacturer_image and manufacturer_image.filename:
        db_man.manufacturer_image = _save_upload(manufacturer_image)
    db.commit()
    db.refresh(db_man)
    return db_man

@app.delete("/manufacturers/{manufacturer_id}", tags=["Manufacturer"])
def delete_manufacturer(manufacturer_id: int, db: Session = Depends(get_db)):
    db_man = db.query(models.Manufacturer).filter(models.Manufacturer.manufacturer_id == manufacturer_id).first()
    if not db_man:
        raise HTTPException(status_code=404, detail="Manufacturer not found")
    db.delete(db_man)
    db.commit()
    return {"message": "Manufacturer deleted successfully"}


@app.get("/payments", response_model=List[schemas.Payment], tags=["Payment"])
def get_payments(db: Session = Depends(get_db)):
    return db.query(models.Payment).all()

@app.get("/payments/{payment_id}", response_model=schemas.Payment, tags=["Payment"])
def get_payment(payment_id: int, db: Session = Depends(get_db)):
    payment = db.query(models.Payment).filter(models.Payment.payment_id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment

@app.post("/payments", response_model=schemas.Payment, tags=["Payment"])
def create_payment(item: schemas.PaymentCreate, db: Session = Depends(get_db)):
    new_payment = models.Payment(**item.model_dump())
    db.add(new_payment)
    db.commit()
    db.refresh(new_payment)
    return new_payment

@app.put("/payments/{payment_id}", response_model=schemas.Payment, tags=["Payment"])
def update_payment(payment_id: int, item: schemas.PaymentCreate, db: Session = Depends(get_db)):
    db_payment = db.query(models.Payment).filter(models.Payment.payment_id == payment_id).first()
    if not db_payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    for key, value in item.model_dump().items():
        setattr(db_payment, key, value)
    db.commit()
    db.refresh(db_payment)
    return db_payment

@app.delete("/payments/{payment_id}", tags=["Payment"])
def delete_payment(payment_id: int, db: Session = Depends(get_db)):
    db_payment = db.query(models.Payment).filter(models.Payment.payment_id == payment_id).first()
    if not db_payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    db.delete(db_payment)
    db.commit()
    return {"message": "Payment deleted successfully"}


@app.get("/pending_orders", response_model=List[schemas.PendingOrder], tags=["PendingOrder"])
def get_pending_orders(db: Session = Depends(get_db)):
    return db.query(models.PendingOrder).all()

@app.get("/pending_orders/{order_id}", response_model=schemas.PendingOrder, tags=["PendingOrder"])
def get_pending_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(models.PendingOrder).filter(models.PendingOrder.order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Pending order not found")
    return order

@app.post("/pending_orders", response_model=schemas.PendingOrder, tags=["PendingOrder"])
def create_pending_order(item: schemas.PendingOrderCreate, db: Session = Depends(get_db)):
    new_order = models.PendingOrder(**item.model_dump())
    db.add(new_order)
    db.commit()
    db.refresh(new_order)
    return new_order

@app.put("/pending_orders/{order_id}", response_model=schemas.PendingOrder, tags=["PendingOrder"])
def update_pending_order(order_id: int, item: schemas.PendingOrderCreate, db: Session = Depends(get_db)):
    db_order = db.query(models.PendingOrder).filter(models.PendingOrder.order_id == order_id).first()
    if not db_order:
        raise HTTPException(status_code=404, detail="Pending order not found")
    for key, value in item.model_dump().items():
        setattr(db_order, key, value)
    db.commit()
    db.refresh(db_order)
    return db_order

@app.delete("/pending_orders/{order_id}", tags=["PendingOrder"])
def delete_pending_order(order_id: int, db: Session = Depends(get_db)):
    db_order = db.query(models.PendingOrder).filter(models.PendingOrder.order_id == order_id).first()
    if not db_order:
        raise HTTPException(status_code=404, detail="Pending order not found")
    db.delete(db_order)
    db.commit()
    return {"message": "Pending order deleted successfully"}


@app.get("/products", response_model=List[schemas.Product], tags=["Product"])
def get_products(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.Product).offset(skip).limit(limit).all()

@app.get("/products/{product_id}", response_model=schemas.Product, tags=["Product"])
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.product_id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@app.post("/products", response_model=schemas.Product, tags=["Product"])
def create_product(
    product_title: str = Form(...),
    product_url: str = Form(...),
    product_price: int = Form(...),
    product_psp_price: int = Form(0),
    product_desc: str = Form(...),
    product_features: str = Form(""),
    cat_id: int = Form(...),
    p_cat_id: int = Form(...),
    manufacturer_id: int = Form(...),
    product_video: str = Form(""),
    product_keywords: str = Form(""),
    product_label: str = Form(""),
    status: str = Form("product"),
    product_img1: UploadFile = File(...),
    product_img2: Optional[UploadFile] = File(None),
    product_img3: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    """Create a product with up to 3 image uploads."""
    img1 = _save_upload(product_img1)
    img2 = _save_upload(product_img2) if product_img2 and product_img2.filename else img1
    img3 = _save_upload(product_img3) if product_img3 and product_img3.filename else img1
    new_product = models.Product(
        product_title=product_title, product_url=product_url,
        product_price=product_price, product_psp_price=product_psp_price,
        product_desc=product_desc, product_features=product_features,
        cat_id=cat_id, p_cat_id=p_cat_id, manufacturer_id=manufacturer_id,
        product_video=product_video, product_keywords=product_keywords,
        product_label=product_label, status=status,
        product_img1=img1, product_img2=img2, product_img3=img3,
    )
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product

@app.put("/products/{product_id}", response_model=schemas.Product, tags=["Product"])
def update_product(
    product_id: int,
    product_title: str = Form(...),
    product_url: str = Form(...),
    product_price: int = Form(...),
    product_psp_price: int = Form(0),
    product_desc: str = Form(...),
    product_features: str = Form(""),
    cat_id: int = Form(...),
    p_cat_id: int = Form(...),
    manufacturer_id: int = Form(...),
    product_video: str = Form(""),
    product_keywords: str = Form(""),
    product_label: str = Form(""),
    status: str = Form("product"),
    product_img1: Optional[UploadFile] = File(None),
    product_img2: Optional[UploadFile] = File(None),
    product_img3: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    """Update a product. Images are optional — if omitted, existing images are kept."""
    db_product = db.query(models.Product).filter(models.Product.product_id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    db_product.product_title = product_title
    db_product.product_url = product_url
    db_product.product_price = product_price
    db_product.product_psp_price = product_psp_price
    db_product.product_desc = product_desc
    db_product.product_features = product_features
    db_product.cat_id = cat_id
    db_product.p_cat_id = p_cat_id
    db_product.manufacturer_id = manufacturer_id
    db_product.product_video = product_video
    db_product.product_keywords = product_keywords
    db_product.product_label = product_label
    db_product.status = status
    if product_img1 and product_img1.filename:
        db_product.product_img1 = _save_upload(product_img1)
    if product_img2 and product_img2.filename:
        db_product.product_img2 = _save_upload(product_img2)
    if product_img3 and product_img3.filename:
        db_product.product_img3 = _save_upload(product_img3)
    db.commit()
    db.refresh(db_product)
    return db_product

@app.delete("/products/{product_id}", tags=["Product"])
def delete_product(product_id: int, db: Session = Depends(get_db)):
    db_product = db.query(models.Product).filter(models.Product.product_id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(db_product)
    db.commit()
    return {"message": "Product deleted successfully"}


@app.get("/product_categories", response_model=List[schemas.ProductCategory], tags=["ProductCategory"])
def get_product_categories(db: Session = Depends(get_db)):
    return db.query(models.ProductCategory).all()

@app.get("/product_categories/{p_cat_id}", response_model=schemas.ProductCategory, tags=["ProductCategory"])
def get_product_category(p_cat_id: int, db: Session = Depends(get_db)):
    p_cat = db.query(models.ProductCategory).filter(models.ProductCategory.p_cat_id == p_cat_id).first()
    if not p_cat:
        raise HTTPException(status_code=404, detail="ProductCategory not found")
    return p_cat

@app.post("/product_categories", response_model=schemas.ProductCategory, tags=["ProductCategory"])
def create_product_category(
    p_cat_title: str = Form(...),
    p_cat_top: str = Form("no"),
    p_cat_image: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    saved = _save_upload(p_cat_image)
    new_p_cat = models.ProductCategory(p_cat_title=p_cat_title, p_cat_top=p_cat_top, p_cat_image=saved)
    db.add(new_p_cat)
    db.commit()
    db.refresh(new_p_cat)
    return new_p_cat

@app.put("/product_categories/{p_cat_id}", response_model=schemas.ProductCategory, tags=["ProductCategory"])
def update_product_category(
    p_cat_id: int,
    p_cat_title: str = Form(...),
    p_cat_top: str = Form("no"),
    p_cat_image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    db_p_cat = db.query(models.ProductCategory).filter(models.ProductCategory.p_cat_id == p_cat_id).first()
    if not db_p_cat:
        raise HTTPException(status_code=404, detail="ProductCategory not found")
    db_p_cat.p_cat_title = p_cat_title
    db_p_cat.p_cat_top = p_cat_top
    if p_cat_image and p_cat_image.filename:
        db_p_cat.p_cat_image = _save_upload(p_cat_image)
    db.commit()
    db.refresh(db_p_cat)
    return db_p_cat

@app.delete("/product_categories/{p_cat_id}", tags=["ProductCategory"])
def delete_product_category(p_cat_id: int, db: Session = Depends(get_db)):
    db_p_cat = db.query(models.ProductCategory).filter(models.ProductCategory.p_cat_id == p_cat_id).first()
    if not db_p_cat:
        raise HTTPException(status_code=404, detail="ProductCategory not found")
    db.delete(db_p_cat)
    db.commit()
    return {"message": "ProductCategory deleted successfully"}


@app.get("/store", response_model=List[schemas.Store], tags=["Store"])
def get_stores(db: Session = Depends(get_db)):
    return db.query(models.Store).all()

@app.get("/store/{store_id}", response_model=schemas.Store, tags=["Store"])
def get_store(store_id: int, db: Session = Depends(get_db)):
    store = db.query(models.Store).filter(models.Store.store_id == store_id).first()
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    return store

@app.post("/store", response_model=schemas.Store, tags=["Store"])
def create_store(
    store_title: str = Form(...),
    store_desc: str = Form(...),
    store_button: str = Form(""),
    store_url: str = Form(""),
    store_image: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    saved = _save_upload(store_image)
    new_store = models.Store(
        store_title=store_title, store_desc=store_desc,
        store_button=store_button, store_url=store_url,
        store_image=saved,
    )
    db.add(new_store)
    db.commit()
    db.refresh(new_store)
    return new_store

@app.put("/store/{store_id}", response_model=schemas.Store, tags=["Store"])
def update_store(
    store_id: int,
    store_title: str = Form(...),
    store_desc: str = Form(...),
    store_button: str = Form(""),
    store_url: str = Form(""),
    store_image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    db_store = db.query(models.Store).filter(models.Store.store_id == store_id).first()
    if not db_store:
        raise HTTPException(status_code=404, detail="Store not found")
    db_store.store_title = store_title
    db_store.store_desc = store_desc
    db_store.store_button = store_button
    db_store.store_url = store_url
    if store_image and store_image.filename:
        db_store.store_image = _save_upload(store_image)
    db.commit()
    db.refresh(db_store)
    return db_store

@app.delete("/store/{store_id}", tags=["Store"])
def delete_store(store_id: int, db: Session = Depends(get_db)):
    db_store = db.query(models.Store).filter(models.Store.store_id == store_id).first()
    if not db_store:
        raise HTTPException(status_code=404, detail="Store not found")
    db.delete(db_store)
    db.commit()
    return {"message": "Store deleted successfully"}


@app.get("/terms", response_model=List[schemas.Term], tags=["Term"])
def get_terms(db: Session = Depends(get_db)):
    return db.query(models.Term).all()

@app.get("/terms/{term_id}", response_model=schemas.Term, tags=["Term"])
def get_term(term_id: int, db: Session = Depends(get_db)):
    term = db.query(models.Term).filter(models.Term.term_id == term_id).first()
    if not term:
        raise HTTPException(status_code=404, detail="Term not found")
    return term

@app.post("/terms", response_model=schemas.Term, tags=["Term"])
def create_term(item: schemas.TermCreate, db: Session = Depends(get_db)):
    new_term = models.Term(**item.model_dump())
    db.add(new_term)
    db.commit()
    db.refresh(new_term)
    return new_term

@app.put("/terms/{term_id}", response_model=schemas.Term, tags=["Term"])
def update_term(term_id: int, item: schemas.TermCreate, db: Session = Depends(get_db)):
    db_term = db.query(models.Term).filter(models.Term.term_id == term_id).first()
    if not db_term:
        raise HTTPException(status_code=404, detail="Term not found")
    for key, value in item.model_dump().items():
        setattr(db_term, key, value)
    db.commit()
    db.refresh(db_term)
    return db_term

@app.delete("/terms/{term_id}", tags=["Term"])
def delete_term(term_id: int, db: Session = Depends(get_db)):
    db_term = db.query(models.Term).filter(models.Term.term_id == term_id).first()
    if not db_term:
        raise HTTPException(status_code=404, detail="Term not found")
    db.delete(db_term)
    db.commit()
    return {"message": "Term deleted successfully"}


@app.get("/wishlist", response_model=List[schemas.Wishlist], tags=["Wishlist"])
def get_wishlist_items(db: Session = Depends(get_db)):
    return db.query(models.Wishlist).all()

@app.get("/wishlist/{wishlist_id}", response_model=schemas.Wishlist, tags=["Wishlist"])
def get_wishlist_item(wishlist_id: int, db: Session = Depends(get_db)):
    item = db.query(models.Wishlist).filter(models.Wishlist.wishlist_id == wishlist_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Wishlist item not found")
    return item

@app.post("/wishlist", response_model=schemas.Wishlist, tags=["Wishlist"])
def create_wishlist_item(item: schemas.WishlistCreate, db: Session = Depends(get_db)):
    new_item = models.Wishlist(**item.model_dump())
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return new_item

@app.put("/wishlist/{wishlist_id}", response_model=schemas.Wishlist, tags=["Wishlist"])
def update_wishlist_item(wishlist_id: int, item: schemas.WishlistCreate, db: Session = Depends(get_db)):
    db_item = db.query(models.Wishlist).filter(models.Wishlist.wishlist_id == wishlist_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Wishlist item not found")
    for key, value in item.model_dump().items():
        setattr(db_item, key, value)
    db.commit()
    db.refresh(db_item)
    return db_item

@app.delete("/wishlist/{wishlist_id}", tags=["Wishlist"])
def delete_wishlist_item(wishlist_id: int, db: Session = Depends(get_db)):
    db_item = db.query(models.Wishlist).filter(models.Wishlist.wishlist_id == wishlist_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Wishlist item not found")
    db.delete(db_item)
    db.commit()
    return {"message": "Wishlist item deleted successfully"}

@app.post("/bakong/checkout", response_model=schemas.BakongCheckoutResponse, tags=["Bakong Payment"])
def bakong_checkout(data: schemas.BakongCheckoutRequest, db: Session = Depends(get_db)):
    """
    **Full Checkout Flow — Step 1**
    
    Creates a new customer order with status "Pending Payment" and generates
    a Bakong KHQR QR code for the customer to scan.
    
    - **customer_id**: ID of the customer placing the order
    - **invoice_no**: Your unique invoice number
    - **qty**: Quantity of items
    - **size**: Product size (e.g. S, M, L, XL)
    - **amount**: Total payment amount (e.g. 49.99)
    - **currency**: 'USD' or 'KHR'
    - **store_label**: Merchant label shown on QR
    - **phone_number**: Customer phone (format: 85512345678)
    
    Returns order details + QR string + MD5 hash (for polling) + deeplink.
    """
    try:
        new_order = models.CustomerOrder(
            customer_id=data.customer_id,
            due_amount=data.amount,
            invoice_no=data.invoice_no,
            qty=data.qty,
            size=data.size,
            order_status="Pending Payment"
        )
        db.add(new_order)
        db.commit()
        db.refresh(new_order)

        bill_number = f"ORD-{new_order.order_id}-INV-{data.invoice_no}"
        qr_string = generate_qr(
            amount=data.amount,
            currency=data.currency,
            bill_number=bill_number,
            store_label=data.store_label,
            phone_number=data.phone_number
        )

        from .services.bakong_service import khqr
        md5 = khqr.generate_md5(qr_string)

        deeplink = generate_deeplink(
            qr_string,
            callback_url=f"https://yourshop.com/payment/success?order_id={new_order.order_id}"
        )
        bakong_txn = models.BakongTransaction(
            order_id=new_order.order_id,
            customer_id=data.customer_id,
            md5=md5,
            qr_string=qr_string,
            deeplink=deeplink,
            currency=data.currency,
            amount=data.amount,
            payment_status="PENDING"
        )
        db.add(bakong_txn)
        db.commit()

        return {
            "order_id": new_order.order_id,
            "invoice_no": data.invoice_no,
            "amount": data.amount,
            "currency": data.currency,
            "order_status": "Pending Payment",
            "qr_string": qr_string,
            "md5": md5,
            "deeplink": deeplink,
            "message": "Order created. Scan QR to pay via Bakong."
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Checkout failed: {str(e)}")

@app.post("/bakong/check-status", response_model=schemas.BakongCheckStatusResponse, tags=["Bakong Payment"])
def bakong_check_status(data: schemas.BakongCheckStatusRequest, db: Session = Depends(get_db)):
    """
    **Full Checkout Flow — Step 2**
    
    Frontend polls this endpoint every ~5 seconds with the MD5 hash
    returned from `/bakong/checkout`.
    
    When payment is confirmed by Bakong:
    - Updates `bakong_transactions.payment_status` → **PAID**
    - Updates `customer_orders.order_status` → **Processing**
    - Saves Bakong response details (hash, fromAccountId, toAccountId, etc.)
    
    **Bakong Response Format (when paid):**
    ```json
    {
      "hash": "a7121ca103c...eb3671b9601a6",
      "fromAccountId": "customer@aclb",
      "toAccountId": "yourname@aclb",
      "currency": "USD",
      "amount": 49.99,
      "description": "Order #10045",
      "createdDateMs": 1739953000,
      "acknowledgedDateMs": 1739953004
    }
    ```
    """
    bakong_txn = db.query(models.BakongTransaction).filter(
        models.BakongTransaction.md5 == data.md5
    ).first()

    if not bakong_txn:
        raise HTTPException(status_code=404, detail="Transaction not found for this MD5")

    if bakong_txn.payment_status == "PAID":
        return {
            "md5": data.md5,
            "is_paid": True,
            "status": "Paid",
            "order_id": bakong_txn.order_id,
            "order_status": "Processing",
            "bakong_hash": bakong_txn.bakong_hash,
            "from_account": bakong_txn.from_account,
            "to_account": bakong_txn.to_account,
            "currency": bakong_txn.currency,
            "amount": bakong_txn.amount,
            "description": f"Order #{bakong_txn.order_id}"
        }

    try:
        from .services.bakong_service import get_payment_info
        result = get_payment_info(data.md5)
        is_paid = result is not None

        if is_paid:
       
            bakong_hash = None
            from_account = None
            to_account = None
            acknowledged_at = None

            if isinstance(result, dict):
                bakong_hash = result.get("hash")
                from_account = result.get("fromAccountId")
                to_account = result.get("toAccountId")
                ack_ms = result.get("acknowledgedDateMs")
                if ack_ms:
                    from datetime import datetime as dt
                    acknowledged_at = dt.fromtimestamp(ack_ms / 1000)

            bakong_txn.payment_status = "PAID"
            bakong_txn.bakong_hash = bakong_hash
            bakong_txn.from_account = from_account
            bakong_txn.to_account = to_account
            bakong_txn.acknowledged_at = acknowledged_at

            order = db.query(models.CustomerOrder).filter(
                models.CustomerOrder.order_id == bakong_txn.order_id
            ).first()
            if order:
                order.order_status = "Processing"

            db.commit()

            return {
                "md5": data.md5,
                "is_paid": True,
                "status": "Paid",
                "order_id": bakong_txn.order_id,
                "order_status": "Processing",
                "bakong_hash": bakong_hash,
                "from_account": from_account,
                "to_account": to_account,
                "currency": bakong_txn.currency,
                "amount": bakong_txn.amount,
                "description": f"Order #{bakong_txn.order_id}"
            }
        else:
            return {
                "md5": data.md5,
                "is_paid": False,
                "status": "Unpaid",
                "order_id": bakong_txn.order_id,
                "order_status": "Pending Payment"
            }

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Payment status check failed: {str(e)}")



@app.get("/bakong/transaction/{order_id}", response_model=schemas.BakongTransactionSchema, tags=["Bakong Payment"])
def bakong_get_transaction(order_id: int, db: Session = Depends(get_db)):
    """
    Get the Bakong transaction record for a specific order.
    Useful for displaying QR again or checking payment history.
    """
    txn = db.query(models.BakongTransaction).filter(
        models.BakongTransaction.order_id == order_id
    ).first()
    if not txn:
        raise HTTPException(status_code=404, detail="No Bakong transaction found for this order")
    return txn



@app.get("/bakong/transactions", response_model=List[schemas.BakongTransactionSchema], tags=["Bakong Payment"])
def bakong_list_transactions(
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    List all Bakong payment transactions.
    
    - **status**: Filter by payment_status (PENDING, PAID, EXPIRED)
    - **skip / limit**: Pagination
    """
    query = db.query(models.BakongTransaction)
    if status:
        query = query.filter(models.BakongTransaction.payment_status == status.upper())
    return query.order_by(models.BakongTransaction.created_at.desc()).offset(skip).limit(limit).all()



@app.post("/bakong/generate", response_model=schemas.BakongPaymentResponse, tags=["Bakong Payment"])
def bakong_generate_payment(data: schemas.BakongPaymentRequest):
    """
    Generate a standalone Bakong KHQR QR code (without creating an order).
    Use `/bakong/checkout` for the full checkout flow instead.
    """
    try:
        qr_string = generate_qr(
            amount=data.amount,
            currency=data.currency,
            bill_number=data.bill_number,
            store_label=data.store_label,
            phone_number=data.phone_number
        )
        from .services.bakong_service import khqr
        md5 = khqr.generate_md5(qr_string)
        deeplink = generate_deeplink(qr_string)

        return {
            "qr_string": qr_string,
            "md5": md5,
            "deeplink": deeplink,
            "currency": data.currency,
            "amount": data.amount,
            "status": "pending"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"QR generation failed: {str(e)}")



@app.post("/bakong/check", tags=["Bakong Payment"])
def bakong_check_payment(data: schemas.BakongCheckPaymentRequest):
    """
    Check payment status by MD5 (standalone, without order linking).
    Use `/bakong/check-status` for the full checkout flow instead.
    """
    try:
        from .services.bakong_service import get_payment_info
        result = get_payment_info(data.md5)
        is_paid = result is not None
        return {
            "md5": data.md5,
            "is_paid": is_paid,
            "status": "Paid" if is_paid else "Unpaid",
            "details": result if is_paid else None
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Payment check failed: {str(e)}")

@app.post("/bakong/details", tags=["Bakong Payment"])
def bakong_payment_details(data: schemas.BakongCheckPaymentRequest):
    """
    Get detailed payment information from Bakong by MD5 hash.
    """
    try:
        info = get_payment_info(data.md5)
        if not info:
            raise HTTPException(status_code=404, detail="Payment not found")
        return info
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to get payment details: {str(e)}")



@app.post("/payment/generate-qr", tags=["Payment QR"])
def payment_generate_qr(payment: schemas.PaymentQRRequest):
    """
    Generate a valid Bakong KHQR code image (PNG base64) from payment data.
    """
    import qrcode as qrcode_lib

    qr_content = generate_qr(
        amount=payment.amount,
        currency="USD",
        bill_number=f"INV-{payment.invoice_no}",
        store_label="Ecomerc Shop",
        phone_number="85512345678"
    )

    qr = qrcode_lib.QRCode(
        version=None,
        error_correction=qrcode_lib.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_content)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    buffer = io.BytesIO()
    img.save(buffer)
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.read()).decode("utf-8")

    return {
        "success": True,
        "invoice_no": payment.invoice_no,
        "qr_base64": img_base64,
        "qr_data_url": f"data:image/png;base64,{img_base64}",
        "encoded_payload": qr_content,
    }


@app.post("/payment/generate-qr/image", tags=["Payment QR"])
def payment_generate_qr_image(payment: schemas.PaymentQRRequest):
    """
    Returns the valid Bakong KHQR code as a raw PNG image (for direct <img src> or download).
    """
    import qrcode as qrcode_lib

    qr_content = generate_qr(
        amount=payment.amount,
        currency="USD",
        bill_number=f"INV-{payment.invoice_no}",
        store_label="Ecomerc Shop",
        phone_number="85512345678"
    )

    qr = qrcode_lib.QRCode(
        version=None,
        error_correction=qrcode_lib.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_content)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer)
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="image/png",
        headers={"Content-Disposition": f"inline; filename=qr_{payment.invoice_no}.png"},
    )


@app.post("/payment/decode-qr", tags=["Payment QR"])
def payment_decode_qr(request: schemas.QRDecodeRequest):
    """
    Parse the raw string decoded from a QR scan into payment fields.
    The frontend scans the QR and sends the decoded text here.
    """
    try:
        payment_data = json.loads(request.qr_data)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="QR data is not valid JSON")

    required = {"invoice_no", "amount", "payment_mode", "ref_no", "code", "payment_date"}
    missing = required - payment_data.keys()
    if missing:
        raise HTTPException(status_code=422, detail=f"Missing fields in QR: {missing}")

    return {
        "success": True,
        "message": "QR decoded successfully",
        "payment": payment_data,
    }



@app.get("/payment/demo", response_class=HTMLResponse, tags=["Payment QR"])
def payment_qr_demo_ui():
    """Serve the Payment QR demo page with generate + scan UI."""
    template_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates", "payment_qr.html")
    if not os.path.isfile(template_path):
        raise HTTPException(status_code=404, detail="Demo template not found")
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()


@app.get("/health", tags=["System"])
def health():
    return {"status": "ok", "date": str(date.today())}
