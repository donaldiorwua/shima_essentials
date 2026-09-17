from django.contrib import admin
from .models import Category, Product

admin.site.register(Category)

class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "available")
    search_fields = ("name", "description")
    list_filter = ("category", "available")
    
admin.site.register(Product, ProductAdmin)