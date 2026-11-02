def history_for(customer_id, orders):
    return sorted(
        (order for order in orders if order["customer_id"] == customer_id),
        key=lambda order: order["date"],
        reverse=True,
    )
