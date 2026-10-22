# Bookstore API (Практична робота 4)

API для керування інвентарем книжкового магазину, обробки покупок і відстеження замовлень. FastAPI, дані зберігаються в пам'яті.

## Встановлення і запуск

```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Сервер: http://127.0.0.1:8000. Автоматична документація (Swagger): http://127.0.0.1:8000/docs

## Запуск тестів

З кореня проєкту (папка lab4), з активованим venv:

```
python -m unittest discover -s tests -t . -v
```

## Опис API

### Книги

| Метод | Ендпоінт | Опис | Коди |
|---|---|---|---|
| POST | /books/ | Додати книгу | 201, 409 (дубль ISBN), 422 |
| GET | /books/ | Усі книги | 200 |
| GET | /books/{id} | Книга за ID | 200, 404 |
| PUT | /books/{id} | Оновити price, quantity, description | 200, 404, 422 (у т.ч. спроба змінити ISBN) |
| DELETE | /books/{id} | Видалити за ID | 200 (`deleted: false`, якщо не було) |
| DELETE | /books/isbn/{isbn} | Видалити за ISBN | 200 |

Тіло POST /books/:
```json
{"isbn": "123", "title": "Kobzar", "author": "Taras Shevchenko",
 "price": 150.0, "quantity": 10, "description": "optional"}
```

### Замовлення

| Метод | Ендпоінт | Опис | Коди |
|---|---|---|---|
| POST | /orders/ | Створити замовлення (покупка) | 201, 404, 409, 422 |
| GET | /orders/{id} | Замовлення за ID | 200, 404 |
| PUT | /orders/{id}/status | Змінити статус | 200, 404, 409, 422 |
| GET | /customers/{id}/orders | Усі замовлення клієнта | 200 |

Тіло POST /orders/: `{"customer_id": 1, "isbn": "123", "quantity": 2}`
Тіло PUT статусу: `{"status": "shipped"}`

Статуси: `processing` (на обробці) → `shipped` (відправлено) → `completed` (виконано). Лише вперед, по одному кроку.

## Прийняті рішення

- Створення замовлення є покупкою: перевіряє наявність і зменшує кількість.
- Одне замовлення містить одну книгу.
- Видалення неіснуючої книги не дає помилки.
- ISBN змінювати не можна.

## Деплоймент

Локальний запуск (див. вище).