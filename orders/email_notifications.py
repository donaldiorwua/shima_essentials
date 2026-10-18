
from django.conf import settings
from django.core.mail import EmailMessage
from django.utils import timezone
import logging
from store.models import Notification, Order
from orders.pdf import generate_order_pdf

logger = logging.getLogger(__name__)

def send_order_email(order: Order) -> Notification:
    recipient = settings.BUSINESS_MANAGER_EMAIL.strip()

    notification = Notification.objects.create(
        order=order,
        channel=Notification.Channel.EMAIL,
        recipient=recipient or "UNCONFIGURED",
        message=f"Order notification for {order.order_number}",
        status=Notification.Status.PENDING,
    )

    try:
        if not recipient:
            raise ValueError(
                "Business manager email is not configured."
            )

        pdf_bytes = generate_order_pdf(order)

        email = EmailMessage(
            subject=f"SHIMA ESSENTIALS Order {order.order_number}",
           body=(
                f"A new order has been received.\n\n"
                f"Order number: {order.order_number}\n"
                f"Customer: {order.customer_name}\n"
                f"Total: NGN{order.total:,.2f}\n\n"
                f"The order details are attached as a PDF."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient],
        )
        email.attach(
            f"{order.order_number}.pdf",
            pdf_bytes,
            "application/pdf",
        )
        email.send(fail_silently=False)

        notification.status = Notification.Status.SENT
        notification.sent_at = timezone.now()
        notification.error_message = ""

    except Exception as exc:
        notification.status = Notification.Status.FAILED
        notification.error_message = str(exc)[:2000]

    notification.save(
        update_fields=[
            "status",
            "sent_at",
            "error_message",
        ]
    )

    return notification

def safely_send_order_email(order: Order) -> None:
    try:
        send_order_email(order)
    except Exception:
        logger.exception(
            "Unexpected email notification error for order %s",
            order.order_number,
        )

