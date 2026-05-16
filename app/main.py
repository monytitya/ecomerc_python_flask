from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .db.session import engine, get_db, Base
from .models import models
from .schemas import schemas
from fastapi.middleware.cors import CORSMiddleware
from a2wsgi import WSGIMiddleware
from flask import Flask, render_template, abort, jsonify

try:
    models.Base.metadata.create_all(bind=engine)
    print("Database tables synchronized.")
except Exception as e:
    print(f"Warning: Could not create tables on startup: {e}")
    print("Ensure your MySQL credentials in .env are correct.")

app = FastAPI(title="Ecomerc API - Comprehensive Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {
        "message": "Welcome to Ecomerc API",
        "documentation": "/docs",
        "admin_dashboard": "/flask/admin"
    }

@app.get("/products", response_model=List[schemas.Product])
def get_products(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.Product).offset(skip).limit(limit).all()

@app.get("/products/{product_id}", response_model=schemas.Product)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.product_id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@app.get("/categories/{cat_id}/products", response_model=List[schemas.Product])
def get_products_by_category(cat_id: int, db: Session = Depends(get_db)):
    return db.query(models.Product).filter(models.Product.cat_id == cat_id).all()

@app.get("/categories", response_model=List[schemas.Category])
def get_categories(db: Session = Depends(get_db)):
    return db.query(models.Category).all()

@app.post("/customers/register", response_model=schemas.Customer)
def register_customer(customer: schemas.CustomerCreate, db: Session = Depends(get_db)):
    db_customer = db.query(models.Customer).filter(models.Customer.customer_email == customer.customer_email).first()
    if db_customer:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    new_customer = models.Customer(**customer.model_dump())
    db.add(new_customer)
    db.commit()
    db.refresh(new_customer)
    return new_customer

@app.get("/customers/{customer_id}", response_model=schemas.Customer)
def get_customer(customer_id: int, db: Session = Depends(get_db)):
    customer = db.query(models.Customer).filter(models.Customer.customer_id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer

@app.get("/orders/customer/{customer_id}", response_model=List[schemas.Order])
def get_customer_orders(customer_id: int, db: Session = Depends(get_db)):
    return db.query(models.CustomerOrder).filter(models.CustomerOrder.customer_id == customer_id).all()

@app.post("/orders", response_model=schemas.Order)
def create_order(order: schemas.OrderCreate, db: Session = Depends(get_db)):
    new_order = models.CustomerOrder(**order.model_dump())
    db.add(new_order)
    db.commit()
    db.refresh(new_order)
    return new_order

flask_app = Flask(__name__, 
                  template_folder="../flask_app/templates",
                  static_folder="../flask_app/static")

@flask_app.route("/admin")
def admin_index():
    return render_template("index.html")

app.mount("/flask", WSGIMiddleware(flask_app))
