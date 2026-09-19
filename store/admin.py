from django.contrib import admin
from .models import (
    Category, 
    Product, 
    Customer, 
    DeliverySetting,
    Order,
    OrderItem
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
