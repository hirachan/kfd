"""Render a small order confirmation label."""

from html import escape

LABEL_COLOR = "slateblue"


def confirmation_label(order_id):
    return f'<span style="color: {LABEL_COLOR}">Order confirmed: {escape(str(order_id))}</span>'
