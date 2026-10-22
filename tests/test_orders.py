import unittest
from fastapi.testclient import TestClient

from app.main import app
from app import storage


class OrderTestCase(unittest.TestCase):
    def setUp(self):
        storage.reset()
        self.client = TestClient(app)
        self.client.post("/books/", json={
            "isbn": "111", "title": "Kobzar", "author": "Taras Shevchenko",
            "price": 150.0, "quantity": 100})

    def order(self, customer_id=1, quantity=1):
        return self.client.post("/orders/", json={
            "customer_id": customer_id, "isbn": "111", "quantity": quantity})

    def set_status(self, order_id, status):
        return self.client.put(f"/orders/{order_id}/status", json={"status": status})


class TestCreateOrder(OrderTestCase):

    def test_order_ids_are_unique(self):
        """Кожне замовлення отримує унікальний ідентифікатор."""
        ids = {self.order().json()["id"] for _ in range(5)}
        self.assertEqual(len(ids), 5)

    def test_order_contains_all_details(self):
        """Замовлення містить клієнта, книгу і кількість."""
        data = self.order(customer_id=7, quantity=2).json()
        self.assertEqual(data["customer_id"], 7)
        self.assertEqual(data["isbn"], "111")
        self.assertEqual(data["title"], "Kobzar")
        self.assertEqual(data["quantity"], 2)

    def test_new_order_status_is_processing(self):
        """Нове замовлення має статус «на обробці»."""
        self.assertEqual(self.order().json()["status"], "processing")

    def test_missing_customer_rejected(self):
        """Без customer_id замовлення не створюється."""
        r = self.client.post("/orders/", json={"isbn": "111", "quantity": 1})
        self.assertEqual(r.status_code, 422)


class TestGetOrder(OrderTestCase):

    def test_get_order_by_id(self):
        """Замовлення можна отримати за id."""
        self.order(customer_id=3, quantity=2)
        r = self.client.get("/orders/1")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["customer_id"], 3)

    def test_get_nonexistent_order_404(self):
        """Неіснуюче замовлення дає 404."""
        self.assertEqual(self.client.get("/orders/999").status_code, 404)


class TestOrderStatus(OrderTestCase):

    def test_processing_to_shipped(self):
        """Статус змінюється з «на обробці» на «відправлено»."""
        self.order()
        r = self.set_status(1, "shipped")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(self.client.get("/orders/1").json()["status"], "shipped")

    def test_full_status_chain(self):
        """Повний шлях: processing -> shipped -> completed."""
        self.order()
        self.set_status(1, "shipped")
        self.assertEqual(self.set_status(1, "completed").status_code, 200)
        self.assertEqual(self.client.get("/orders/1").json()["status"], "completed")

    def test_invalid_status_value_rejected(self):
        """Неіснуючий статус відхиляється."""
        self.order()
        self.assertEqual(self.set_status(1, "flying").status_code, 422)

    def test_cannot_skip_status(self):
        """Не можна перескочити одразу на «виконано»."""
        self.order()
        self.assertEqual(self.set_status(1, "completed").status_code, 409)
        self.assertEqual(self.client.get("/orders/1").json()["status"], "processing")

    def test_cannot_go_backwards(self):
        """Не можна повернути статус назад."""
        self.order()
        self.set_status(1, "shipped")
        self.assertEqual(self.set_status(1, "processing").status_code, 409)

    def test_update_status_nonexistent_order_404(self):
        """Зміна статусу неіснуючого замовлення дає 404."""
        self.assertEqual(self.set_status(999, "shipped").status_code, 404)


class TestCustomerOrders(OrderTestCase):

    def test_customer_sees_all_own_orders(self):
        """Клієнт бачить усі свої замовлення."""
        self.order(customer_id=1)
        self.order(customer_id=1)
        self.order(customer_id=1)
        r = self.client.get("/customers/1/orders")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()), 3)

    def test_customer_does_not_see_others_orders(self):
        """У списку немає замовлень інших клієнтів."""
        self.order(customer_id=1)
        self.order(customer_id=2)
        orders = self.client.get("/customers/1/orders").json()
        self.assertEqual(len(orders), 1)
        self.assertEqual(orders[0]["customer_id"], 1)

    def test_customer_without_orders_gets_empty_list(self):
        """Клієнт без замовлень отримує порожній список."""
        r = self.client.get("/customers/42/orders")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), [])

    def test_customer_orders_reflect_status_change(self):
        """Зміна статусу видна у списку замовлень клієнта."""
        self.order(customer_id=1)
        self.set_status(1, "shipped")
        orders = self.client.get("/customers/1/orders").json()
        self.assertEqual(orders[0]["status"], "shipped")


if __name__ == "__main__":
    unittest.main(verbosity=2)