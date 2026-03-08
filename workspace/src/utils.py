import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any
from sqlalchemy.orm import Session
from .models import Product, Category, Review


def generate_product_id() -> str:
    """Generate a unique product ID"""
    return secrets.token_urlsafe(16)


def calculate_average_rating(reviews: list) -> float:
    """Calculate average rating from a list of reviews"""
    if not reviews:
        return 0.0
    
    total_rating = sum(review.rating for review in reviews)
    return round(total_rating / len(reviews), 1)


def get_product_with_reviews(db: Session, product_id: int) -> Dict[str, Any]:
    """Get product with its associated reviews"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return None
    
    reviews = db.query(Review).filter(Review.product_id == product_id).all()
    
    return {
        "product": product,
        "reviews": reviews,
        "average_rating": calculate_average_rating(reviews)
    }


def validate_product_fields(name: str, price: float, category_id: int) -> bool:
    """Validate required product fields"""
    if not name or len(name.strip()) == 0:
        return False
    
    if price is None or price < 0:
        return False
    
    if category_id is None or category_id <= 0:
        return False
    
    return True


def validate_category_fields(name: str) -> bool:
    """Validate required category fields"""
    if not name or len(name.strip()) == 0:
        return False
    
    return True


def validate_review_fields(rating: int, comment: str, author: str) -> bool:
    """Validate required review fields"""
    if rating is None or rating < 1 or rating > 5:
        return False
    
    if not comment or len(comment.strip()) == 0:
        return False
    
    if not author or len(author.strip()) == 0:
        return False
    
    return True