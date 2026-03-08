"""Domain models for generic API"""

from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from datetime import datetime

class Item(BaseModel):
    id: Optional[int]
    name: str
    description: Optional[str]
    created_at: str


