from django.shortcuts import get_object_or_404, redirect, render
from store.models import Order, Product
from .exceptions import OrderCreationError
from .cart import Cart
from .forms import CheckoutForm
from .services import create_order
from decimal import Decimal
from store.models import DeliverySetting


def checkout(request):
    cart = Cart(request.session)
    cart_items = cart.get_items()
    products = []
    subtotal = Decimal("0.00")
    for product in Product.objects.filter(id__in=cart_items.keys()):
        quantity = cart_items[product.id]
        line_total = product.price * quantity
        subtotal += line_total
        products.append((product, quantity, line_total))
        
    form = CheckoutForm()
    delivery_fee = None
    total = None
    if request.method == "POST":
       
        form = CheckoutForm(request.POST)

        if form.is_valid():
            cleaned_data = form.cleaned_data
            delivery_setting = DeliverySetting.objects.get(
                location=cleaned_data["delivery_location"],
                active=True,
            )

            delivery_fee = delivery_setting.fee
            total = subtotal + delivery_fee

            order_data = {
                **cleaned_data,
                "cart": cart_items
            }
            try:
                order = create_order(**order_data)
                cart.clear()
                return redirect("order_confirmation", order_number=order.order_number)
            except OrderCreationError as exc:
                form.add_error(None, str(exc))

    return render(
        request,
        "orders/checkout.html",
        {
            "form": form,
            "cart": cart,
            "products": products,
            "subtotal": subtotal,
            "delivery_fee": delivery_fee,
            "total": total,
        },
    )

def order_confirmation(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    return render(
        request,
        "orders/order_confirmation.html",
        {"order": order},
    )


