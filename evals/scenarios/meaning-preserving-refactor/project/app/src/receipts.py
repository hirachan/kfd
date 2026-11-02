"""Public receipt rendering and its private formatting helper."""


def _format_amount(pence):
    pounds, pennies = divmod(pence, 100)
    return f"£{pounds}.{pennies:02d}"


def render_receipt(total_pence):
    return f"Total: {_format_amount(total_pence)}"
