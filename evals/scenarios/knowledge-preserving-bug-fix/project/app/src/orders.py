"""Read a customer order history from the order store."""


def orders_for_customer(orders, customer_id):
    return sorted(orders, key=lambda order: order["created_at"], reverse=True)
