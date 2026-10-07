from urllib.parse import quote

def build_whatsapp_message(order):
    lines = [
        "SHIMA ESSENTIALS ORDER",
        "",
        f"Order: {order.order_number}",
        f"Customer: {order.customer_name}",
        f"Delivery location: {order.delivery_location}",
        f"Address: {order.address}",
        "",
        "Items:",
    ]

    for item in order.items.all():
        lines.append(
            f"- {item.product_name_snapshot} x {item.quantity} "
            f"= ₦{item.line_total}"
        )

    lines.extend(
        [
            "",
            f"Subtotal: ₦{order.subtotal}",
            f"Delivery fee: ₦{order.delivery_fee}",
            f"Total: ₦{order.total}",
        ]
    )

    if order.notes:
        lines.extend(
            [
                "",
                f"Notes: {order.notes}",
            ]
        )

    return "\n".join(lines)


def build_whatsapp_url(order, phone_number):
    message = build_whatsapp_message(order)
    encoded_message = quote(message)

    return f"https://wa.me/{phone_number}?text={encoded_message}"