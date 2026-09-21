from orders.validate_phone import normalize_phone
from orders.exceptions import OrderCreationError
from store.models import Product

def create_order(
    *,
    customer_name,
    phone,
    address,
    delivery_location,
    notes,
    cart
    ):
   """
    Creates an order from checkout information and cart data.
    Validates the supplied checkout data and cart.
    Calculates line totals and order totals using trusted database values.
    """
   errors = {}

   if not customer_name or not customer_name.strip():
        errors["customer_name"] = "Customer name is required"

   try:
        phone = normalize_phone(phone)
   except OrderCreationError as e:
        errors.update(e.errors)

   if not address or not address.strip():
        errors["address"] = "Address is required"

   if not delivery_location or not delivery_location.strip():
        errors["delivery_location"] = "Delivery location is required"

   if not isinstance(cart, dict):
        errors["cart"] = "Cart must be a dictionary"
   elif not cart:
        errors["cart"] = "Cart cannot be empty"
   else:
        cart_errors = {}
        validated_cart = {}

        for raw_id, quantity in cart.items():
            entry_errors = []
            product_id = None

            if isinstance(raw_id, str) and raw_id.isdigit():
                product_id = int(raw_id)
            else:
                entry_errors.append("Invalid product ID")

            if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity <= 0:
                entry_errors.append("Invalid quantity")

            if product_id is not None and product_id in validated_cart:
                entry_errors.append(
                    f"Duplicate product ID"
                )

            if entry_errors:
                cart_errors[raw_id] = "; ".join(entry_errors)
            else:
                validated_cart[product_id] = quantity

        
        if validated_cart:
            products_by_id = Product.objects.in_bulk(validated_cart.keys())

            for product_id in validated_cart:
                product = products_by_id.get(product_id)

                if product is None:
                    cart_errors[product_id] = "Product does not exist"
                    continue

                if not product.available:
                    cart_errors[product_id] = "Product is not available"
                    continue

        if cart_errors:
            errors["cart"] = cart_errors

   if errors:
        raise OrderCreationError(errors)