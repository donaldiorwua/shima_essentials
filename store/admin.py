from django.contrib import admin
from .models import (
    Category, 
    Product, 
    Customer, 
    DeliverySetting,
    Order,
    OrderItem,
    Notification
)

admin.site.register(Category)

class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "available")
    search_fields = ("name", "description")
    list_filter = ("category", "available")

admin.site.register(Product, ProductAdmin)

admin.site.register(Customer)
admin.site.register(DeliverySetting)

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = (
        "product_name_snapshot",
        "unit_price",
        "line_total",
    )


class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "order_number",
        "customer_name",
        "address",
        "total",
        "status",
        "created_at",
    )
    readonly_fields = (
        "order_number",
        "customer_name",
        "phone",
        "address",
        "subtotal",
        "delivery_fee",
        "total",
        "created_at",
        "updated_at",
    )
    search_fields = ("order_number", "customer_name")
    list_filter = ("status",)
    inlines = [OrderItemInline]

admin.site.register(Order, OrderAdmin)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "order",
        "channel",
        "recipient",
        "status",
        "sent_at",
    )
    list_filter = ("channel", "status", "sent_at")
    search_fields = (
        "order__order_number",
        "recipient",
        "message",
        "error_message",
    )
    readonly_fields = (
        "order",
        "channel",
        "recipient",
        "message",
        "status",
        "sent_at",
        "error_message",
    )
    ordering = ("-id",)
