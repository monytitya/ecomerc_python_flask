from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .db.session import engine, get_db, Base
from .models import models
from .schemas import schemas
from fastapi.middleware.cors import CORSMiddleware
from a2wsgi import WSGIMiddleware
from flask import Flask, render_template, abort, jsonify

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Ecomerc API - FastAPI + Flask Hybrid")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Welcome to Ecomerc API (FastAPI)"}

@app.get("/products", response_model=List[schemas.Product])
def get_products(db: Session = Depends(get_db)):
    return db.query(models.Product).all()

@app.get("/categories", response_model=List[schemas.Category])
def get_categories(db: Session = Depends(get_db)):
    return db.query(models.Category).all()

@app.get("/products/{product_id}", response_model=schemas.Product)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.product_id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@app.post("/customers/register", response_model=schemas.Customer)
def register_customer(customer: schemas.CustomerCreate, db: Session = Depends(get_db)):
    db_customer = db.query(models.Customer).filter(models.Customer.customer_email == customer.customer_email).first()
    if db_customer:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    new_customer = models.Customer(
        customer_name=customer.customer_name,
        customer_email=customer.customer_email,
        customer_pass=customer.customer_pass, # Note: In production, hash this!
        customer_country=customer.customer_country,
        customer_city=customer.customer_city
    )
    db.add(new_customer)
    db.commit()
    db.refresh(new_customer)
    return new_customer


flask_app = Flask(__name__, 
                  template_folder="../flask_app/templates",
                  static_folder="../flask_app/static")

@flask_app.route("/admin")
def admin_index():
    return render_template("index.html")

# Mount Flask app into FastAPI
app.mount("/flask", WSGIMiddleware(flask_app))
