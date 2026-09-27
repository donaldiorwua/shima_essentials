import secrets
import datetime
from store.models import Order

def generate_date_code():
    return datetime.date.today().strftime("%y%m%d")

def generate_random_code():
    allowed_characters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    return "".join(secrets.choice(allowed_characters) for _ in range(6))

def generate_order_number():
    while True:
        date_code = generate_date_code()
        random_code = generate_random_code()
        candidate = f"SE-{date_code}-{random_code}"

        if not Order.objects.filter(order_number=candidate).exists():
            return candidate

from unittest.mock import patch

with patch(
    "orders.order_number.generate_random_code",
    side_effect=["ABC123", "XYZ789"]
), patch(
    "orders.order_number.Order.objects.filter"
) as mock_filter:
    mock_filter.return_value.exists.side_effect = [True, False]

Order.objects.filter(
    order_number__in=[
        "SE-260924-PEZEV9",
        "SE-260924-5UO94P",
        "SE-260924-83LPKT",
    ]
).delete()