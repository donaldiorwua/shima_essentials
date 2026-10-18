from django.test import TestCase
from orders.services import create_order, OrderCreationError
from django.urls import reverse
from django.test import override_settings
from decimal import Decimal
from django.contrib.messages import get_messages
from store.models import Category, Product, DeliverySetting, Order, OrderItem, Notification
from io import BytesIO
from pypdf import PdfReader
from unittest.mock import patch
from orders.pdf import generate_order_pdf
from orders.email_notifications import send_order_email
from orders.receipt_links import (
    generate_receipt_token,
    verify_receipt_token,
)
from orders.receipt_links import build_receipt_url

class CheckoutTests(TestCase):
    def test_empty_cart_redirects_to_cart(self):
        response = self.client.get(reverse("checkout"))

        self.assertRedirects(response, reverse("cart"))


class CartViewTests(TestCase):
    def setUp(self):
        session = self.client.session
        session["cart"] = {"123": 2}
        session.save()

    def test_cart_update_changes_quantity(self):
        response = self.client.post(
            reverse("cart_update", kwargs={"product_id": 123}),
            {"quantity": "4"},
        )

        self.assertRedirects(response, reverse("cart"))

        session = self.client.session
        self.assertEqual(session["cart"]["123"], 4)

    def test_cart_remove_deletes_product(self):
        response = self.client.post(
            reverse("cart_remove", kwargs={"product_id": 123}),
        )

        self.assertRedirects(response, reverse("cart"))

        session = self.client.session
        self.assertNotIn("123", session["cart"])


class CartAddTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name="Cakes",
            slug="test-cakes",
        )
        self.product = Product.objects.create(
            name="Test Cake",
            category=self.category,
            description="A test cake",
            price="5000.00",
            available=True,
        )

    def test_add_to_cart_shows_success_message(self):
        response = self.client.post(
            reverse(
                "cart_add",
                kwargs={"product_id": self.product.id},
            )
        )

        self.assertRedirects(response, reverse("cart"))

        session = self.client.session
        self.assertEqual(
            session["cart"][str(self.product.id)],
            1,
        )

        messages_list = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages_list), 1)
        self.assertEqual(
            str(messages_list[0]),
            "Test Cake added to your cart.",
        )

class SuccessfulCheckoutTests(TestCase):
    def setUp(self):
        category = Category.objects.create(
            name="Checkout Cakes",
            slug="checkout-cakes",
        )
        self.product = Product.objects.create(
            name="Checkout Cake",
            category=category,
            description="Cake for checkout testing",
            price="5000.00",
            available=True,
        )
        DeliverySetting.objects.create(
            location="Test Location",
            fee="2000.00",
            active=True,
        )

    @patch("orders.views.safely_send_order_email")
    def test_successful_checkout_schedules_email_notification(
        self,
        mock_send_email,
    ):
        session = self.client.session
        session["cart"] = {str(self.product.id): 1}
        session.save()

        with self.captureOnCommitCallbacks(execute=True) as callbacks:
            response = self.client.post(
                reverse("checkout"),
                {
                    "customer_name": "Email Checkout Customer",
                    "phone": "08012345678",
                    "address": "123 Test Street",
                    "delivery_location": "Test Location",
                    "notes": "Email integration test",
                },
            )

        self.assertEqual(response.status_code, 302)

        order = Order.objects.get(
            customer_name="Email Checkout Customer",
        )

        self.assertEqual(len(callbacks), 1)
        mock_send_email.assert_called_once_with(order)


    def test_order_service_rejects_zero_quantity(self):
        with self.assertRaises(OrderCreationError) as context:
            create_order(
                customer_name="Quantity Test",
                phone="08012345678",
                address="123 Test Street",
                delivery_location="Test Location",
                notes="",
                cart={self.product.id: 0},
            )

        self.assertIn("cart", context.exception.errors)
        self.assertEqual(Order.objects.count(), 0)

    def test_checkout_rejects_inactive_delivery_location(self):
        delivery_setting = DeliverySetting.objects.get(
            location="Test Location"
        )
        delivery_setting.active = False
        delivery_setting.save()

        session = self.client.session
        session["cart"] = {str(self.product.id): 1}
        session.save()

        response = self.client.post(reverse("checkout"), {
            "customer_name": "Inactive Location Test",
            "phone": "08012345678",
            "address": "123 Test Street",
            "delivery_location": "Test Location",
            "notes": "",
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Order.objects.count(), 0)

    def test_order_service_rejects_string_quantity(self):
        with self.assertRaises(OrderCreationError) as context:
            create_order(
                customer_name="Quantity Test",
                phone="08012345678",
                address="123 Test Street",
                delivery_location="Test Location",
                notes="",
                cart={self.product.id: "2"},
            )

        self.assertIn("cart", context.exception.errors)
        self.assertEqual(Order.objects.count(), 0)

    def test_order_service_rejects_boolean_quantity(self):
        with self.assertRaises(OrderCreationError) as context:
            create_order(
                customer_name="Quantity Test",
                phone="08012345678",
                address="123 Test Street",
                delivery_location="Test Location",
                notes="",
                cart={self.product.id: True},
            )

        self.assertIn("cart", context.exception.errors)
        self.assertEqual(Order.objects.count(), 0)

    def test_order_service_rejects_invalid_product_id(self):
        with self.assertRaises(OrderCreationError) as context:
            create_order(
                customer_name="Invalid Product Test",
                phone="08012345678",
                address="123 Test Street",
                delivery_location="Test Location",
                notes="",
                cart={"invalid-id": 1},
            )

        self.assertIn("cart", context.exception.errors)
        self.assertEqual(Order.objects.count(), 0)

    def test_order_service_rejects_nonexistent_product_id(self):
        nonexistent_product_id = self.product.id + 10000

        with self.assertRaises(OrderCreationError) as context:
            create_order(
                customer_name="Missing Product Test",
                phone="08012345678",
                address="123 Test Street",
                delivery_location="Test Location",
                notes="",
                cart={nonexistent_product_id: 1},
            )

        self.assertIn("cart", context.exception.errors)
        self.assertEqual(Order.objects.count(), 0)

    def test_order_service_rejects_empty_cart(self):
        with self.assertRaises(OrderCreationError) as context:
            create_order(
                customer_name="Empty Cart Test",
                phone="08012345678",
                address="123 Test Street",
                delivery_location="Test Location",
                notes="",
                cart={},
            )

        self.assertIn("cart", context.exception.errors)
        self.assertEqual(Order.objects.count(), 0)

    def test_order_service_rejects_duplicate_product_ids(self):
        with self.assertRaises(OrderCreationError) as context:
            create_order(
                customer_name="Duplicate Product Test",
                phone="08012345678",
                address="123 Test Street",
                delivery_location="Test Location",
                notes="",
                cart={
                    self.product.id: 1,
                    str(self.product.id): 2,
                },
            )

        self.assertIn("cart", context.exception.errors)
        self.assertEqual(Order.objects.count(), 0)

    def test_order_service_rejects_non_dictionary_cart(self):
        with self.assertRaises(OrderCreationError) as context:
            create_order(
                customer_name="Invalid Cart Test",
                phone="08012345678",
                address="123 Test Street",
                delivery_location="Test Location",
                notes="",
                cart=[self.product.id, 1],
            )

        self.assertIn("cart", context.exception.errors)
        self.assertEqual(Order.objects.count(), 0)

    def test_order_service_rejects_negative_quantity(self):
        with self.assertRaises(OrderCreationError) as context:
            create_order(
                customer_name="Quantity Test",
                phone="08012345678",
                address="123 Test Street",
                delivery_location="Test Location",
                notes="",
                cart={self.product.id: -1},
            )

        self.assertIn("cart", context.exception.errors)
        self.assertEqual(Order.objects.count(), 0)


    def test_checkout_rejects_unavailable_product(self):
        self.product.available = False
        self.product.save()

        session = self.client.session
        session["cart"] = {str(self.product.id): 1}
        session.save()

        response = self.client.post(reverse("checkout"), {
            "customer_name": "Unavailable Product Test",
            "phone": "08012345678",
            "address": "123 Test Street",
            "delivery_location": "Test Location",
            "notes": "",
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Order.objects.count(), 0)


    def test_successful_checkout_creates_order_and_clears_cart(self):
        session = self.client.session
        session["cart"] = {str(self.product.id): 2}
        session.save()

        response = self.client.post(
            reverse("checkout"),
            {
                "customer_name": "Test Customer",
                "phone": "08012345678",
                "address": "123 Test Street",
                "delivery_location": "Test Location",
                "notes": "Automated checkout test",
            },
        )

        self.assertEqual(response.status_code, 302)

        order = Order.objects.get()
        self.assertRedirects(
            response,
            reverse(
                "order_confirmation",
                kwargs={"order_number": order.order_number},
            ),
        )

        self.assertEqual(order.customer_name, "Test Customer")
        self.assertEqual(order.subtotal, Decimal("10000.00"))
        self.assertEqual(order.delivery_fee, Decimal("2000.00"))
        self.assertEqual(order.total, Decimal("12000.00"))
        self.assertEqual(
            order.total,
            order.subtotal + order.delivery_fee,
        )

        item = OrderItem.objects.get(order=order)
        self.assertEqual(item.product, self.product)
        self.assertEqual(item.quantity, 2)

        session = self.client.session
        self.assertEqual(session.get("cart", {}), {})

    def test_order_item_price_snapshot_survives_product_price_change(self):
        session = self.client.session
        session["cart"] = {str(self.product.id): 2}
        session.save()

        response = self.client.post(
            reverse("checkout"),
            {
                "customer_name": "Snapshot Test",
                "phone": "08012345678",
                "address": "123 Test Street",
                "delivery_location": "Test Location",
                "notes": "",
            },
        )

        self.assertEqual(response.status_code, 302)

        order = Order.objects.get()
        item = OrderItem.objects.get(order=order)

        self.assertEqual(item.product_name_snapshot, "Checkout Cake")
        self.assertEqual(item.unit_price, Decimal("5000.00"))
        self.assertEqual(item.line_total, Decimal("10000.00"))

        self.product.price = Decimal("7000.00")
        self.product.save()

        item.refresh_from_db()

        self.assertEqual(item.unit_price, Decimal("5000.00"))
        self.assertEqual(item.line_total, Decimal("10000.00"))

    @override_settings(WHATSAPP_BUSINESS_NUMBER="2348012345678")
    def test_confirmation_page_contains_whatsapp_link(self):
        session = self.client.session
        session["cart"] = {str(self.product.id): 1}
        session.save()

        checkout_response = self.client.post(
            reverse("checkout"),
            {
                "customer_name": "WhatsApp Test",
                "phone": "08012345678",
                "address": "123 Test Street",
                "delivery_location": "Test Location",
                "notes": "",
            },
        )

        self.assertEqual(checkout_response.status_code, 302)

        order = Order.objects.get()
        confirmation_response = self.client.get(
            reverse(
                "order_confirmation",
                kwargs={"order_number": order.order_number},
            )
        )

        self.assertEqual(confirmation_response.status_code, 200)

        page = confirmation_response.content.decode()
        self.assertIn("https://wa.me/2348012345678?text=", page)
        self.assertIn(order.order_number, page)
        self.assertIn("Send order details via WhatsApp", page)

    @override_settings(WHATSAPP_BUSINESS_NUMBER="")
    def test_confirmation_page_shows_error_when_whatsapp_number_missing(self):
        session = self.client.session
        session["cart"] = {str(self.product.id): 1}
        session.save()

        checkout_response = self.client.post(
            reverse("checkout"),
            {
                "customer_name": "WhatsApp Test",
                "phone": "08012345678",
                "address": "123 Test Street",
                "delivery_location": "Test Location",
                "notes": "",
            },
        )

        self.assertEqual(checkout_response.status_code, 302)

        order = Order.objects.get()
        confirmation_response = self.client.get(
            reverse(
                "order_confirmation",
                kwargs={"order_number": order.order_number},
            )
        )

        self.assertEqual(confirmation_response.status_code, 200)

        page = confirmation_response.content.decode()
        self.assertIn(order.order_number, page)
        self.assertIn("WhatsApp notification is not configured", page)
        self.assertNotIn("https://wa.me/", page)

    @override_settings(SHIMA_PUBLIC_BASE_URL="")
    def test_confirmation_page_shows_message_when_receipt_url_unavailable(self):
        session = self.client.session
        session["cart"] = {str(self.product.id): 1}
        session.save()

        checkout_response = self.client.post(
            reverse("checkout"),
            {
                "customer_name": "Receipt Test",
                "phone": "08012345678",
                "address": "123 Test Street",
                "delivery_location": "Test Location",
                "notes": "",
            },
        )

        self.assertEqual(checkout_response.status_code, 302)

        order = Order.objects.get()
        confirmation_response = self.client.get(
            reverse(
                "order_confirmation",
                kwargs={"order_number": order.order_number},
            )
        )

        self.assertEqual(confirmation_response.status_code, 200)

        page = confirmation_response.content.decode()
        self.assertIn(
            "A downloadable PDF receipt link is not currently available.",
            page,
        )
        self.assertNotIn("PDF receipt is available through the WhatsApp message link", page)


class OrderCreationErrorTests(TestCase):
    def test_error_preserves_validation_details(self):
        errors = {
            "cart": "Cart cannot be empty",
            "phone": "Invalid phone number",
        }

        error = OrderCreationError(errors)

        self.assertEqual(error.errors, errors)
        self.assertEqual(error.message, "Validation failed")
        self.assertIn("Validation failed", str(error))
        self.assertIn("Cart cannot be empty", str(error))

class OrderPDFTests(TestCase):
    def setUp(self):
        category = Category.objects.create(
            name="PDF Test Cakes",
            slug="pdf-test-cakes",
        )
        self.product = Product.objects.create(
            name="PDF Test Cake",
            category=category,
            description="Cake for PDF testing",
            price=Decimal("5000.00"),
            available=True,
        )
        DeliverySetting.objects.create(
            location="PDF Test Location",
            fee=Decimal("2000.00"),
            active=True,
        )

        self.order = create_order(
            customer_name="PDF Test Customer",
            phone="08012345678",
            address="123 PDF Test Street",
            delivery_location="PDF Test Location",
            notes="PDF verification test",
            cart={self.product.id: 2},
        )

    def test_pdf_contains_saved_order_details_and_prices(self):
        # Change the current product price after the order is saved.
        self.product.price = Decimal("7000.00")
        self.product.save()

        pdf_bytes = generate_order_pdf(self.order)

        self.assertTrue(pdf_bytes.startswith(b"%PDF-"))

        reader = PdfReader(BytesIO(pdf_bytes))
        pdf_text = "\n".join(
            page.extract_text() or ""
            for page in reader.pages
        )

        self.assertIn(self.order.order_number, pdf_text)
        self.assertIn("PDF Test Customer", pdf_text)
        self.assertIn("PDF Test Cake", pdf_text)
        self.assertIn("PDF verification test", pdf_text)

        # The PDF must use saved order-item prices, not the current product price.
        self.assertIn("₦5,000.00", pdf_text)
        self.assertIn("₦10,000.00", pdf_text)
        self.assertIn("₦2,000.00", pdf_text)
        self.assertIn("₦12,000.00", pdf_text)

        self.assertNotIn("₦7,000.00", pdf_text)
        self.assertNotIn("■", pdf_text)


class OrderEmailNotificationTests(TestCase):
    def setUp(self):
        category = Category.objects.create(
            name="Email Test Cakes",
            slug="email-test-cakes",
        )
        product = Product.objects.create(
            name="Email Test Cake",
            category=category,
            description="Cake for email testing",
            price=Decimal("5000.00"),
            available=True,
        )
        DeliverySetting.objects.create(
            location="Email Test Location",
            fee=Decimal("2000.00"),
            active=True,
        )
        self.order = create_order(
            customer_name="Email Test Customer",
            phone="08012345678",
            address="123 Email Test Street",
            delivery_location="Email Test Location",
            notes="Email attachment test",
            cart={product.id: 2},
        )

    @patch("orders.email_notifications.EmailMessage")
    @patch(
        "orders.email_notifications.settings.BUSINESS_MANAGER_EMAIL",
        "manager@example.com",
    )
    def test_successful_email_is_recorded(
        self,
        mock_email_class,
    ):
        mock_email = mock_email_class.return_value
        mock_email.send.return_value = 1

        notification = send_order_email(self.order)
        notification.refresh_from_db()

        self.assertEqual(
            notification.status,
            Notification.Status.SENT,
        )
        self.assertEqual(
            notification.recipient,
            "manager@example.com",
        )
        self.assertIsNotNone(notification.sent_at)
        mock_email.send.assert_called_once()

        mock_email.attach.assert_called_once()
        attachment_args = mock_email.attach.call_args.args

        self.assertEqual(
            attachment_args[0],
            f"{self.order.order_number}.pdf",
        )
        self.assertEqual(
            attachment_args[2],
            "application/pdf",
        )


    @patch("orders.email_notifications.EmailMessage.send",
           side_effect=RuntimeError("Email transport failed"))
    @patch("orders.email_notifications.settings.BUSINESS_MANAGER_EMAIL",
           "manager@example.com")
    def test_failed_email_does_not_delete_order(self, mock_send):
        notification = send_order_email(self.order)

        notification.refresh_from_db()

        self.assertEqual(
            notification.status,
            Notification.Status.FAILED,
        )
        self.assertIn(
            "Email transport failed",
            notification.error_message,
        )
        self.assertTrue(
            Order.objects.filter(pk=self.order.pk).exists()
        )


class ReceiptLinkTests(TestCase):
    def setUp(self):
        self.order = Order(
            order_number="SE-261017-ABC123",
        )
        self.token = generate_receipt_token(self.order)

    def test_valid_token_matches_its_order(self):
        self.assertTrue(
            verify_receipt_token(
                self.token,
                self.order.order_number,
            )
        )

    def test_token_cannot_authorize_another_order(self):
        self.assertFalse(
            verify_receipt_token(
                self.token,
                "SE-261017-XYZ789",
            )
        )

    def test_tampered_token_is_rejected(self):
        tampered_token = self.token + "tampered"

        self.assertFalse(
            verify_receipt_token(
                tampered_token,
                self.order.order_number,
            )
        )

    @override_settings(SHIMA_PUBLIC_BASE_URL="")
    def test_receipt_url_is_not_built_without_public_base_url(self):
        self.assertIsNone(build_receipt_url(self.order))

    @override_settings(SHIMA_PUBLIC_BASE_URL="http://shima.example.com")
    def test_receipt_url_rejects_http_base_url(self):
        self.assertIsNone(build_receipt_url(self.order))

    @override_settings(SHIMA_PUBLIC_BASE_URL="https://shima.example.com")
    def test_receipt_url_uses_https_and_valid_token(self):
        url = build_receipt_url(self.order)

        self.assertTrue(url.startswith("https://shima.example.com/"))

        response_path = url.split("https://shima.example.com", 1)[1]
        resolved = __import__("django.urls", fromlist=["resolve"]).resolve(
            response_path
        )

        self.assertEqual(resolved.url_name, "order_receipt")
        self.assertTrue(
            verify_receipt_token(
                resolved.kwargs["token"],
                self.order.order_number,
            )
        )


class OrderReceiptViewTests(TestCase):
    def setUp(self):
        self.order = Order.objects.create(
            order_number="SE-261017-RCP123",
            customer_name="Receipt Test",
            phone="+2348012345678",
            address="123 Test Street",
            delivery_location="Test Location",
            subtotal=Decimal("1000.00"),
            delivery_fee=Decimal("200.00"),
            total=Decimal("1200.00"),
        )
        self.token = generate_receipt_token(self.order)
        self.url = reverse(
            "order_receipt",
            kwargs={
                "order_number": self.order.order_number,
                "token": self.token,
            },
        )

    def test_valid_token_returns_pdf(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertTrue(response.content.startswith(b"%PDF"))
        self.assertEqual(response["Cache-Control"], "private, no-store")

    def test_invalid_token_cannot_access_receipt(self):
        url = reverse(
            "order_receipt",
            kwargs={
                "order_number": self.order.order_number,
                "token": "invalid-token",
            },
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)
        self.assertNotEqual(response["Content-Type"], "application/pdf")
