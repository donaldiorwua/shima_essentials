from django.shortcuts import get_object_or_404, redirect, render
from store.models import Order
from .exceptions import OrderCreationError
from .cart import Cart
from .forms import CheckoutForm
from .services import create_order


def checkout(request):
    cart = Cart(request.session)
    form = CheckoutForm()

    if request.method == "POST":
        form = CheckoutForm(request.POST)

        if form.is_valid():
            cleaned_data = form.cleaned_data
            cart_items = cart.get_items()

            order_data = {
                **cleaned_data,
                "cart": cart_items
            }
            try:
                order = create_order(**order_data)
                return redirect("order_confirmation", order_number=order.order_number)
            except OrderCreationError as exc:
                form.add_error(None, str(exc))
            else:
                pass

    return render(request, "orders/checkout.html", {"form": form, "cart": cart})


def order_confirmation(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    return render(
        request,
        "orders/order_confirmation.html",
        {"order": order},
    )

