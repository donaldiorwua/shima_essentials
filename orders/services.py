from orders.validate_phone import normalize_phone
from orders.exceptions import OrderCreationError
from store.models import Product, DeliverySetting
from decimal import Decimal
from django.db import transaction
from orders.order_number import generate_order_number
from store.models import Order, OrderItem

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
    
   delivery_fee = Decimal("0.00")
   subtotal = Decimal("0.00")
   total = Decimal("0.00")

   errors = {}
   calculated_items = {}

   customer_name = customer_name.strip() if isinstance(customer_name, str) else customer_name
   address = address.strip() if isinstance(address, str) else address
   delivery_location = delivery_location.strip() if isinstance(delivery_location, str) else delivery_location
   notes = notes.strip() if isinstance(notes, str) else notes

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

   if not notes:
       notes = ""
   
   if not isinstance(cart, dict):
        errors["cart"] = "Cart must be a dictionary"
   elif not cart:
        errors["cart"] = "Cart cannot be empty"
   
   cart_errors = {}
   validated_cart = {}

   for raw_id, quantity in cart.items():
        entry_errors = []
        product_id = None

        if isinstance(raw_id, bool):
            entry_errors.append("Invalid product ID")
        elif isinstance(raw_id, int) and raw_id > 0:
            product_id = raw_id
        elif isinstance(raw_id, str) and raw_id.isdigit() and int(raw_id) > 0:
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
   if cart_errors:
        errors["cart"] = cart_errors

   if errors:
        raise OrderCreationError(errors)

   with transaction.atomic():
        if validated_cart:
            products_by_id = Product.objects.select_for_update().in_bulk(validated_cart.keys())
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
                raise OrderCreationError(errors)

            for product_id in validated_cart:
                product = products_by_id[product_id]
                quantity = validated_cart[product_id]
                line_total = quantity * product.price
                calculated_items[product_id] = {
                    "product": product,
                    "quantity": quantity,
                    "unit_price": product.price,
                    "line_total": line_total,
                }
            
            for item in calculated_items.values():
                subtotal += item["line_total"]

        delivery_setting = DeliverySetting.objects.select_for_update().filter(
            location=delivery_location,
        ).first()

        if delivery_setting is None:
            errors["delivery_location"] = "Delivery is not available for this location"
        elif not delivery_setting.active:
            errors["delivery_location"] = "Delivery is not available for this location"
        if errors:
            raise OrderCreationError(errors)
        
        assert delivery_setting is not None
        delivery_fee = delivery_setting.fee
        total = subtotal + delivery_fee

        order = Order.objects.create(
            order_number=generate_order_number(),
            customer_name=customer_name,
            phone=phone,
            address=address,
            delivery_location=delivery_location,
            notes=notes,
            subtotal=subtotal,
            delivery_fee=delivery_fee,
            total=total,
        )
        for item in calculated_items.values():
            OrderItem.objects.create(
                order=order,
                product=item["product"],
                product_name_snapshot=item["product"].name,
                unit_price=item["unit_price"],
                quantity=item["quantity"],
                line_total=item["line_total"],
            )
   return order

