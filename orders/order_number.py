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
