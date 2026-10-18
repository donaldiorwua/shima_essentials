from urllib.parse import urlsplit

from django.conf import settings
from django.urls import reverse
from django.core import signing


RECEIPT_LINK_MAX_AGE = 7 * 24 * 60 * 60
RECEIPT_LINK_SALT = "orders.receipt-link"


def generate_receipt_token(order):
    """Generate a signed token tied to one saved order."""
    return signing.dumps(
        {"order_number": order.order_number},
        salt=RECEIPT_LINK_SALT,
    )


def verify_receipt_token(token, order_number):
    """Return True only for a valid, unexpired token for this order."""
    try:
        payload = signing.loads(
            token,
            salt=RECEIPT_LINK_SALT,
            max_age=RECEIPT_LINK_MAX_AGE,
        )
    except signing.BadSignature:
        return False

    return payload.get("order_number") == order_number

def build_receipt_url(order):
    """Build a public HTTPS receipt URL, or return None if not configured."""
    base_url = settings.SHIMA_PUBLIC_BASE_URL

    if not base_url:
        return None

    parsed_url = urlsplit(base_url)

    if (
        parsed_url.scheme != "https"
        or not parsed_url.netloc
        or parsed_url.username
        or parsed_url.password
        or parsed_url.query
        or parsed_url.fragment
    ):
        return None

    token = generate_receipt_token(order)
    receipt_path = reverse(
        "order_receipt",
        kwargs={
            "order_number": order.order_number,
            "token": token,
        },
    )

    return f"{base_url}{receipt_path}"