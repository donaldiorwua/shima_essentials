from django.urls import path

from . import views


urlpatterns = [
    path("checkout/", views.checkout, name="checkout"),
    path(
        "checkout/confirmation/<str:order_number>/",
        views.order_confirmation,
        name="order_confirmation",
    ),
    path("cart/", views.cart_view, name="cart"),
    path(
        "cart/add/<int:product_id>/",
        views.cart_add,
        name="cart_add",
    ),
    path(
        "cart/remove/<int:product_id>/",
        views.cart_remove,
        name="cart_remove",
    ),
    path(
        "cart/update/<int:product_id>/",
        views.cart_update,
        name="cart_update",
    ),
]

