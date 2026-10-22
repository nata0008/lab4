from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class BookCreate(BaseModel):
    isbn: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    author: str = Field(..., min_length=1)
    price: float = Field(..., ge=0)
    quantity: int = Field(..., ge=0)
    description: Optional[str] = None


class BookUpdate(BaseModel):
    # ISBN тут свідомо відсутній: змінювати його не можна
    price: Optional[float] = Field(None, ge=0)
    quantity: Optional[int] = Field(None, ge=0)
    description: Optional[str] = None

    model_config = {"extra": "forbid"}  # передали isbn -> 422


class OrderStatus(str, Enum):
    PROCESSING = "processing"   # на обробці
    SHIPPED = "shipped"         # відправлено
    COMPLETED = "completed"     # виконано


class OrderCreate(BaseModel):
    customer_id: int = Field(..., ge=1)
    isbn: str = Field(..., min_length=1)
    quantity: int = Field(..., ge=1)


class OrderStatusUpdate(BaseModel):
    status: OrderStatus