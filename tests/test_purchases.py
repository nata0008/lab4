import unittest
from fastapi.testclient import TestClient

from app.main import app
from app import storage


class PurchaseTestCase(unittest.TestCase):
    def setUp(self):
        storage.reset()
        self.client = TestClient(app)
        self.client.post("/books/", json={
            "isbn": "111", "title": "Kobzar", "author": "Taras Shevchenko",
            "price": 150.0, "quantity": 10})

    def buy(self, quantity, isbn="111", customer_id=1):
        return self.client.post("/orders/", json={
            "customer_id": customer_id, "isbn": isbn, "quantity": quantity})

    def stock(self):
        return self.client.get("/books/1").json()["quantity"]


class TestPurchase(PurchaseTestCase):

    def test_purchase_success_when_in_stock(self):
        """Покупка успішна, якщо книга є в наявності."""
        r = self.buy(3)
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.json()["quantity"], 3)

    def test_purchase_total_price(self):
        """Сума замовлення = ціна * кількість."""
        self.assertEqual(self.buy(3).json()["total_price"], 450.0)

    def test_stock_decreases_after_purchase(self):
        """Кількість книг в інвентарі зменшується після покупки."""
        self.buy(3)
        self.assertEqual(self.stock(), 7)

    def test_buy_entire_stock(self):
        """Можна купити рівно стільки, скільки є на складі."""
        self.assertEqual(self.buy(10).status_code, 201)
        self.assertEqual(self.stock(), 0)

    def test_purchases_accumulate(self):
        """Кілька покупок підряд послідовно зменшують запас."""
        self.buy(2)
        self.buy(3)
        self.assertEqual(self.stock(), 5)

    def test_sold_out_book_cannot_be_bought(self):
        """Коли запас вичерпано, наступна покупка неможлива."""
        self.buy(10)
        self.assertEqual(self.buy(1).status_code, 409)
        self.assertEqual(self.stock(), 0)


class TestPurchaseErrors(PurchaseTestCase):

    def test_buy_more_than_in_stock_rejected(self):
        """Купити більше, ніж є, неможливо; запас не змінюється."""
        r = self.buy(11)
        self.assertEqual(r.status_code, 409)
        self.assertEqual(self.stock(), 10)

    def test_buy_nonexistent_book_rejected(self):
        """Купити книгу, якої немає в інвентарі, неможливо."""
        self.assertEqual(self.buy(1, isbn="no-such").status_code, 404)

    def test_failed_purchase_creates_no_order(self):
        """Невдала покупка не створює замовлення."""
        self.buy(999)
        self.assertEqual(self.client.get("/orders/1").status_code, 404)

    def test_zero_quantity_rejected(self):
        """Нульова кількість відхиляється."""
        self.assertEqual(self.buy(0).status_code, 422)

    def test_negative_quantity_rejected(self):
        """Від'ємна кількість відхиляється, запас не змінюється."""
        self.assertEqual(self.buy(-5).status_code, 422)
        self.assertEqual(self.stock(), 10)


if __name__ == "__main__":
    unittest.main(verbosity=2)