import unittest
from fastapi.testclient import TestClient

from app.main import app
from app import storage


class BooksTestCase(unittest.TestCase):
    def setUp(self):
        """Перед кожним тестом чистимо сховище і створюємо клієнта."""
        storage.reset()
        self.client = TestClient(app)
        self.book = {
            "isbn": "123456789",
            "title": "Python Programming",
            "author": "John Doe",
            "price": 250.0,
            "quantity": 5,
            "description": "Підручник",
        }

    def create(self, **overrides):
        return self.client.post("/books/", json={**self.book, **overrides})


class TestCreateBook(BooksTestCase):

    def test_create_book_success(self):
        """Нова книга створюється і повертається з id."""
        r = self.create()
        self.assertEqual(r.status_code, 201)
        data = r.json()
        self.assertEqual(data["isbn"], "123456789")
        self.assertEqual(data["id"], 1)

    def test_created_book_is_stored(self):
        """Після створення книга є у списку та доступна за id."""
        self.create()
        self.assertEqual(len(self.client.get("/books/").json()), 1)
        r = self.client.get("/books/1")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["title"], "Python Programming")

    def test_duplicate_isbn_rejected(self):
        """Книгу з однаковим ISBN додати неможливо."""
        self.create()
        r = self.create(title="Another Book", author="Jane Doe")
        self.assertEqual(r.status_code, 409)
        self.assertEqual(len(self.client.get("/books/").json()), 1)

    def test_negative_price_rejected(self):
        """Від'ємна ціна — помилка валідації."""
        self.assertEqual(self.create(price=-1).status_code, 422)

    def test_negative_quantity_rejected(self):
        """Від'ємна кількість — помилка валідації."""
        self.assertEqual(self.create(quantity=-5).status_code, 422)

    def test_missing_required_field_rejected(self):
        """Без обов'язкового поля (title) книга не створюється."""
        data = dict(self.book)
        del data["title"]
        self.assertEqual(self.client.post("/books/", json=data).status_code, 422)


class TestGetBooks(BooksTestCase):

    def test_get_all_empty(self):
        """Порожній інвентар повертає порожній список."""
        r = self.client.get("/books/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), [])

    def test_get_all_returns_every_book(self):
        """Список містить усі додані книги."""
        self.create()
        self.create(isbn="987654321", title="Second")
        self.assertEqual(len(self.client.get("/books/").json()), 2)

    def test_get_nonexistent_book_404(self):
        """Запит неіснуючого id дає 404."""
        self.assertEqual(self.client.get("/books/999").status_code, 404)


class TestUpdateBook(BooksTestCase):

    def test_update_price_quantity_description(self):
        """Ціну, кількість і опис можна змінити."""
        self.create()
        r = self.client.put("/books/1", json={
            "price": 300.0, "quantity": 20, "description": "Нове видання"})
        self.assertEqual(r.status_code, 200)
        data = self.client.get("/books/1").json()
        self.assertEqual(data["price"], 300.0)
        self.assertEqual(data["quantity"], 20)
        self.assertEqual(data["description"], "Нове видання")

    def test_partial_update_keeps_other_fields(self):
        """Оновлення однієї ціни не чіпає решту полів."""
        self.create()
        self.client.put("/books/1", json={"price": 99.0})
        data = self.client.get("/books/1").json()
        self.assertEqual(data["price"], 99.0)
        self.assertEqual(data["quantity"], 5)
        self.assertEqual(data["author"], "John Doe")

    def test_isbn_cannot_be_changed(self):
        """Спроба змінити ISBN відхиляється, ISBN лишається старим."""
        self.create()
        r = self.client.put("/books/1", json={"isbn": "000000000"})
        self.assertEqual(r.status_code, 422)
        self.assertEqual(self.client.get("/books/1").json()["isbn"], "123456789")

    def test_update_nonexistent_book_404(self):
        """Оновлення неіснуючої книги дає 404."""
        r = self.client.put("/books/999", json={"price": 10.0})
        self.assertEqual(r.status_code, 404)

    def test_update_negative_price_rejected(self):
        """Від'ємна ціна при оновленні відхиляється."""
        self.create()
        r = self.client.put("/books/1", json={"price": -10})
        self.assertEqual(r.status_code, 422)
        self.assertEqual(self.client.get("/books/1").json()["price"], 250.0)


class TestDeleteBook(BooksTestCase):

    def test_delete_by_id(self):
        """Книга видаляється за id."""
        self.create()
        r = self.client.delete("/books/1")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json()["deleted"])
        self.assertEqual(self.client.get("/books/1").status_code, 404)

    def test_delete_by_isbn(self):
        """Книга видаляється за ISBN."""
        self.create()
        r = self.client.delete("/books/isbn/123456789")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json()["deleted"])
        self.assertEqual(self.client.get("/books/").json(), [])

    def test_delete_nonexistent_does_not_error(self):
        """Видалення неіснуючої книги не викликає помилки."""
        r = self.client.delete("/books/999")
        self.assertEqual(r.status_code, 200)
        self.assertFalse(r.json()["deleted"])

    def test_delete_nonexistent_isbn_does_not_error(self):
        """Те саме для видалення за неіснуючим ISBN."""
        r = self.client.delete("/books/isbn/no-such-isbn")
        self.assertEqual(r.status_code, 200)
        self.assertFalse(r.json()["deleted"])

    def test_delete_only_removes_target(self):
        """Видалення однієї книги не зачіпає іншу."""
        self.create()
        self.create(isbn="987654321", title="Second")
        self.client.delete("/books/1")
        books = self.client.get("/books/").json()
        self.assertEqual(len(books), 1)
        self.assertEqual(books[0]["isbn"], "987654321")


if __name__ == "__main__":
    unittest.main(verbosity=2)