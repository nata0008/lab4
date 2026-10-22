from fastapi import FastAPI, HTTPException

from app import storage
from app.models import (BookCreate, BookUpdate, OrderCreate,
                        OrderStatus, OrderStatusUpdate)

app = FastAPI(title="Bookstore API")


def find_book_by_id(book_id: int):
    for book in storage.books.values():
        if book["id"] == book_id:
            return book
    return None


@app.get("/")
def root():
    return {"message": "ok"}


# ───────────── Інвентар книг ─────────────

@app.post("/books/", status_code=201)
def add_book(book: BookCreate):
    if book.isbn in storage.books:
        raise HTTPException(status_code=409, detail="Книга з таким ISBN вже існує")
    data = book.model_dump()
    data["id"] = storage.next_book_id()
    storage.books[book.isbn] = data
    return data


@app.get("/books/")
def get_books():
    return list(storage.books.values())


@app.get("/books/{book_id}")
def get_book(book_id: int):
    book = find_book_by_id(book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Книгу не знайдено")
    return book


@app.put("/books/{book_id}")
def update_book(book_id: int, updated: BookUpdate):
    book = find_book_by_id(book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Книгу не знайдено")
    changes = updated.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status_code=400, detail="Не передано жодного поля для оновлення")
    book.update(changes)
    return book


@app.delete("/books/{book_id}")
def delete_book(book_id: int):
    book = find_book_by_id(book_id)
    if book is None:
        return {"deleted": False, "message": "Книги не було в інвентарі"}
    del storage.books[book["isbn"]]
    return {"deleted": True, "message": "Книгу видалено"}


@app.delete("/books/isbn/{isbn}")
def delete_book_by_isbn(isbn: str):
    if storage.books.pop(isbn, None) is None:
        return {"deleted": False, "message": "Книги не було в інвентарі"}
    return {"deleted": True, "message": "Книгу видалено"}

# ───────────── Замовлення і покупки ─────────────

# Дозволений порядок статусів: на обробці -> відправлено -> виконано
STATUS_FLOW = [OrderStatus.PROCESSING, OrderStatus.SHIPPED, OrderStatus.COMPLETED]


@app.post("/orders/", status_code=201)
def create_order(order: OrderCreate):
    """Створення замовлення = покупка: перевіряє наявність і зменшує кількість."""
    book = storage.books.get(order.isbn)
    if book is None:
        raise HTTPException(status_code=404, detail="Книгу не знайдено")
    if order.quantity > book["quantity"]:
        raise HTTPException(
            status_code=409,
            detail=f"Запитано {order.quantity}, на складі лише {book['quantity']}")
    book["quantity"] -= order.quantity
    order_id = storage.next_order_id()
    data = {
        "id": order_id,
        "customer_id": order.customer_id,
        "isbn": order.isbn,
        "title": book["title"],
        "quantity": order.quantity,
        "total_price": round(book["price"] * order.quantity, 2),
        "status": OrderStatus.PROCESSING.value,
    }
    storage.orders[order_id] = data
    return data


@app.get("/orders/{order_id}")
def get_order(order_id: int):
    order = storage.orders.get(order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Замовлення не знайдено")
    return order


@app.put("/orders/{order_id}/status")
def update_order_status(order_id: int, update: OrderStatusUpdate):
    order = storage.orders.get(order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Замовлення не знайдено")
    current = STATUS_FLOW.index(OrderStatus(order["status"]))
    new = STATUS_FLOW.index(update.status)
    if new != current + 1:
        raise HTTPException(
            status_code=409,
            detail="Статус можна змінити лише на наступний крок")
    order["status"] = update.status.value
    return order


@app.get("/customers/{customer_id}/orders")
def get_customer_orders(customer_id: int):
    return [o for o in storage.orders.values() if o["customer_id"] == customer_id]