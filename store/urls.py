from django.urls import path
from . import views


urlpatterns = [
    path("", views.home, name="home"),
    path("products/", views.product_list, name="product_list"),
    path(
        "products/<slug:slug>/",
        views.category_products,
        name="category_products",
    ),
    path(
        "product/<int:product_id>/",
        views.product_detail,
        name="product_detail",
    ),
    path("contact/", views.contact, name="contact"),
    path("about/", views.about, name="about"),
]

