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

def cart_view(request):
    cart = Cart(request.session)
    cart_items = cart.get_items()

    products = Product.objects.filter(
        id__in=cart_items.keys(),
        available=True,
    )

    items = []
    subtotal = Decimal("0.00")

    for product in products:
        quantity = cart_items[product.id]
        line_total = product.price * quantity
        subtotal += line_total

        items.append(
            {
                "product": product,
                "quantity": quantity,
                "line_total": line_total,
            }
        )

    return render(
        request,
        "orders/cart.html",
        {
            "items": items,
            "subtotal": subtotal,
        },
    )

def cart_add(request, product_id):
    if request.method != "POST":
        return redirect("product_detail", product_id=product_id)

    product = get_object_or_404(
        Product,
        id=product_id,
        available=True,
    )

    cart = Cart(request.session)
    cart.add(product.id, 1)
    cart.save()

    return redirect("cart")

def cart_remove(request, product_id):
    if request.method != "POST":
        return redirect("cart")

    cart = Cart(request.session)
    cart.remove(product_id)
    cart.save()

    return redirect("cart")

def cart_update(request, product_id):
    if request.method != "POST":
        return redirect("cart")

    try:
        quantity = int(request.POST.get("quantity", 0))
    except (TypeError, ValueError):
        return redirect("cart")

    cart = Cart(request.session)
    cart.set_quantity(product_id, quantity)
    cart.save()

    return redirect("cart")