from sqlalchemy import create_engine, text
from app.db.session import SessionLocal, engine, SQLALCHEMY_DATABASE_URL
from app.models import models
import os

def create_db_if_not_exists():
    # Parse the URL to get the server address without the DB name
    # e.g. mysql+pymysql://root@localhost:3306/ecom_store -> mysql+pymysql://root@localhost:3306
    url_parts = SQLALCHEMY_DATABASE_URL.rsplit('/', 1)
    base_url = url_parts[0]
    db_name = url_parts[1]
    
    # Connect to MySQL server without database
    temp_engine = create_engine(base_url)
    with temp_engine.connect() as conn:
        conn.execution_options(isolation_level="AUTOCOMMIT").execute(text(f"CREATE DATABASE IF NOT EXISTS {db_name}"))
        print(f"Database '{db_name}' checked/created.")
    temp_engine.dispose()

def seed_data():
    db = SessionLocal()
    
    # Check if we already have data
    if db.query(models.Category).first():
        print("Database already has data. Skipping seed.")
        db.close()
        return

    # Categories
    cats = [
        models.Category(cat_id=2, cat_title="Feminine", cat_top="no", cat_image="feminelg.png"),
        models.Category(cat_id=3, cat_title="Kids", cat_top="no", cat_image="kidslg.jpg"),
        models.Category(cat_id=4, cat_title="Others", cat_top="yes", cat_image="othericon.png"),
        models.Category(cat_id=5, cat_title="Men", cat_top="yes", cat_image="malelg.png"),
    ]
    
    # Products
    prods = [
        models.Product(
            product_id=5, 
            cat_id=5, 
            product_title="Denim Borg Lined Western Jacket", 
            product_url="product-url-5", 
            product_price=100,
            status="product"
        ),
        models.Product(
            product_id=8, 
            cat_id=2, 
            product_title="Sleeveless Flaux Fur Hybrid Coat", 
            product_url="product-url-8", 
            product_price=100,
            status="product"
        )
    ]

    try:
        db.add_all(cats)
        db.commit()
        db.add_all(prods)
        db.commit()
        print("Database seeded successfully!")
    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    try:
        create_db_if_not_exists()
        # Create tables
        models.Base.metadata.create_all(bind=engine)
        seed_data()
    except Exception as e:
        print(f"Setup failed: {e}")
        print("\nTIP: Ensure your MySQL password in .env is correct.")
