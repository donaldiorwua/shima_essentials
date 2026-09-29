from django.shortcuts import redirect, render
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
                return redirect("checkout")
            except OrderCreationError as exc:
                form.add_error(None, str(exc))
            else:
                pass

    return render(request, "orders/checkout.html", {"form": form, "cart": cart})

