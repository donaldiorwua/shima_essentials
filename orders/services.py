
class OrderCreationError(Exception):
    def __init__(self, errors: dict, message: str = "Validation failed"):
        self.errors = errors
        self.message = message
        super().__init__(message)

    def __str__(self):
        return f"{self.message}: {self.errors}"

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