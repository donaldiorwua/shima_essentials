from django.db import models
from django.core.validators import MinValueValidator


# Create your models here.
class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to="products/", blank=True, null=True)
    available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(price__gte=0),
                name="price_non_negative",
            )  
        ]

    def __str__(self):
        return self.name

class Customer(models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    email = models.EmailField()
    address = models.TextField(max_length=150)

    def __str__(self):
        return self.name

class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        CONFIRMED = "CONFIRMED", "Confirmed"
        PREPARING = "PREPARING", "Preparing"
        READY = "READY", "Ready"
        CANCELLED = "CANCELLED", "Cancelled"
        SHIPPED = "SHIPPED", "Shipped"
        DELIVERED = "DELIVERED", "Delivered"
    order_number = models.CharField(max_length=30, unique=True)
    customer_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    address = models.TextField(max_length=150)
    delivery_location = models.CharField(max_length=50)
    notes = models.TextField()
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
            constraints = [
                models.CheckConstraint(
                    condition=models.Q(subtotal__gte=0),
                    name="subtotal_non_negative",
                ),
                models.CheckConstraint(
                    condition=models.Q(delivery_fee__gte=0),
                    name="delivery_fee_non_negative",
                ),
                models.CheckConstraint(
                    condition=models.Q(total__gte=0),
                    name="total_non_negative",
                ),
                models.CheckConstraint(
                    condition=models.Q(total=models.F("subtotal") + models.F("delivery_fee")),
                    name="total_matches_breakdown",
                ),
            ]
    def __str__(self):
        return self.order_number

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='order_items')
    product_name_snapshot = models.CharField(max_length=50)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2,)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    line_total = models.DecimalField(max_digits=10, decimal_places=2)
    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(unit_price__gte=0),
                name="unit_price_non_negative",
            ),
            models.CheckConstraint(
                condition=models.Q(line_total__gte=0),
                name="line_total_non_negative",
            ),
            models.CheckConstraint(
                condition=models.Q(line_total=models.F("unit_price") * models.F("quantity")),
                name="line_total_matches_quantity",
            ),
        ]

    def __str__(self):
        return f"{self.product_name_snapshot} (X{self.quantity})"
 
class DeliverySetting(models.Model):
    location = models.CharField(max_length=50, unique=True)
    fee = models.DecimalField(max_digits=10, decimal_places=2)
    active = models.BooleanField(default=True)
    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(fee__gte=0),
                name="fee_non_negative",
            )
        ]

    def __str__(self):
        return f"Delivery Fee: {self.fee} (Active)"

class Notification(models.Model):
    class Channel(models.TextChoices):
            WHATSAPP = "WHATSAPP", "WhatsApp"
            EMAIL = "EMAIL", "Email"
            SMS = "SMS", "SMS"
    class Status(models.TextChoices):
                PENDING = "PENDING", "Pending"
                SENT = "SENT", "Sent"
                FAILED = "FAILED", "Failed"
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="notifications")
    channel = models.CharField(max_length=20, choices=Channel.choices, default=Channel.WHATSAPP)
    recipient = models.CharField(max_length=100)
    message = models.TextField(max_length=300)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    sent_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.channel
