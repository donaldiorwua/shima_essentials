from store.models import Order, Product

class Cart:
    SESSION_KEY = "cart"

    def __init__(self, session):
        self.session = session
        raw_cart = self.session.get(self.SESSION_KEY, {})
        self.cart = {
            self._normalize_product_id(product_id): quantity
            for product_id, quantity in raw_cart.items()
}

    def add(self, product_id, quantity=1):
        product_id = self._normalize_product_id(product_id)
        if not isinstance(quantity, int) or isinstance(quantity, bool):
            raise ValueError("Quantity must be an integer")
        if quantity <= 0:
            raise ValueError("Quantity must be greater than zero")
        if product_id in self.cart:
            self.cart[product_id] += quantity
        else:
            self.cart[product_id] = quantity
        self.save()

    def save(self):
        self.session[self.SESSION_KEY] = self.cart
        self.session.modified = True

    def remove(self, product_id):
        product_id = self._normalize_product_id(product_id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def clear(self):
        self.cart.clear()
        self.save()

    def __len__(self):
        return sum(self.cart.values())

    def get_items(self):
        return self.cart.copy()

    @staticmethod
    def _normalize_product_id(product_id):
        if isinstance(product_id, bool):
            raise ValueError("Product ID must be an integer")
        if isinstance(product_id, int):
            if product_id <= 0:
                raise ValueError("Product ID must be greater than zero")
            return product_id
        if isinstance(product_id, str) and product_id.isdigit():
            product_id = int(product_id)
            if product_id <= 0:
                raise ValueError("Product ID must be greater than zero")
            return product_id
        raise ValueError("Product ID must be a positive integer")

    def set_quantity(self, product_id, quantity):
        product_id = self._normalize_product_id(product_id)

        if quantity < 0:
            raise ValueError("Quantity cannot be negative")

        if quantity == 0:
            self.remove(product_id)
            return

        self.cart[product_id] = quantity

