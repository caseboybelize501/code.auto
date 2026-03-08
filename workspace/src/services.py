from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from .models import Product, Category, Review
from .utils import calculate_average_rating


class ProductService:
    @staticmethod
    def get_products(
        db: Session,
        category_id: Optional[int] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        in_stock: Optional[bool] = None,
        search: Optional[str] = None,
        page: int = 1,
        size: int = 10
    ) -> dict:
        """
        Get products with filtering, pagination, and search capabilities
        """
        query = db.query(Product)
        
        # Apply filters
        if category_id:
            query = query.filter(Product.category_id == category_id)
        
        if min_price is not None:
            query = query.filter(Product.price >= min_price)
        
        if max_price is not None:
            query = query.filter(Product.price <= max_price)
        
        if in_stock is not None:
            query = query.filter(Product.in_stock == in_stock)
        
        if search:
            query = query.filter(Product.name.contains(search))
        
        # Count total results
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * size
        query = query.offset(offset).limit(size)
        
        products = query.all()
        
        return {
            "products": products,
            "total": total,
            "page": page,
            "size": size
        }

    @staticmethod
    def get_product_with_reviews(db: Session, product_id: int) -> dict:
        """Get product with its associated reviews and average rating"""
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return None
        
        reviews = db.query(Review).filter(Review.product_id == product_id).all()
        
        return {
            "product": product,
            "reviews": reviews,
            "average_rating": calculate_average_rating(reviews)
        }



class CategoryService:
    @staticmethod
    def get_categories(db: Session) -> List[Category]:
        """Get all categories"""
        return db.query(Category).all()

    @staticmethod
    def get_category(db: Session, category_id: int) -> Optional[Category]:
        """Get a specific category by ID"""
        return db.query(Category).filter(Category.id == category_id).first()



class InventoryService:
    @staticmethod
    def update_inventory(db: Session, product_id: int, stock_quantity: int) -> Product:
        """Update product inventory"""
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise ValueError("Product not found")
        
        product.stock_quantity = stock_quantity
        product.in_stock = stock_quantity > 0
        
        db.commit()
        db.refresh(product)
        
        return product

    @staticmethod
    def check_stock_availability(db: Session, product_id: int, quantity: int) -> bool:
        """Check if sufficient stock is available"""
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return False
        
        return product.stock_quantity >= quantity
