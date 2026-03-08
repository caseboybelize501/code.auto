from typing import List, Optional
from sqlalchemy import create_engine, Column, Integer, String, Text, Float, ForeignKey, desc, asc
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from config import settings

Base = declarative_base()

# Database models

class Review(Base):
    __tablename__ = "reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    rating = Column(Integer)
    comment = Column(Text)

# Initialize database
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

class ReviewService:
    def __init__(self):
        self.db = SessionLocal()
    
    def get_reviews_by_product(self, product_id: int, skip: int = 0, limit: int = 20) -> List[Review]:
        return self.db.query(Review).filter(Review.product_id == product_id).offset(skip).limit(limit).all()
    
    def create_review(self, review_data) -> Review:
        review = Review(**review_data.dict())
        self.db.add(review)
        self.db.commit()
        self.db.refresh(review)
        return review
    
    def __del__(self):
        self.db.close()