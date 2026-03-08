from typing import List, Optional
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, ForeignKey, desc, asc
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from config import settings

Base = declarative_base()

# Database models

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(Text)
    price = Column(Float)
    category_id = Column(Integer)
    inventory_count = Column(Integer)

# Initialize database
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

class ProductService:
    def __init__(self):
        self.db = SessionLocal()
    
    def get_products(self, category_id: Optional[int] = None, search: Optional[str] = None, 
                    skip: int = 0, limit: int = 20, sort_by: Optional[str] = None, 
                    order: str = "asc") -> List[Product]:
        query = self.db.query(Product)
        
        # Apply filters
        if category_id:
            query = query.filter(Product.category_id == category_id)
        
        if search:
            query = query.filter(Product.name.contains(search))
        
        # Apply sorting
        if sort_by:
            if hasattr(Product, sort_by):
                column = getattr(Product, sort_by)
                if order.lower() == "desc":
                    query = query.order_by(desc(column))
                else:
                    query = query.order_by(asc(column))
        
        # Apply pagination
        return query.offset(skip).limit(limit).all()
    
    def get_product_by_id(self, product_id: int) -> Optional[Product]:
        return self.db.query(Product).filter(Product.id == product_id).first()
    
    def create_product(self, product_data) -> Product:
        product = Product(**product_data.dict())
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)
        return product
    
    def update_product(self, product_id: int, product_data) -> Optional[Product]:
        product = self.get_product_by_id(product_id)
        if product:
            for key, value in product_data.dict(exclude_unset=True).items():
                setattr(product, key, value)
            self.db.commit()
            self.db.refresh(product)
        return product
    
    def delete_product(self, product_id: int) -> bool:
        product = self.get_product_by_id(product_id)
        if product:
            self.db.delete(product)
            self.db.commit()
            return True
        return False
    
    def __del__(self):
        self.db.close()