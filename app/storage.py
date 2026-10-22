# Сховище в пам'яті
books = {}        # ключ: isbn -> dict з даними книги
orders = {}       # ключ: order_id -> dict із даними замовлення
_counters = {"book": 0, "order": 0}


def next_book_id() -> int:
    _counters["book"] += 1
    return _counters["book"]


def next_order_id() -> int:
    _counters["order"] += 1
    return _counters["order"]


def reset():
    """Очищає все. Викликається в setUp кожного тесту."""
    books.clear()
    orders.clear()
    _counters["book"] = 0
    _counters["order"] = 0