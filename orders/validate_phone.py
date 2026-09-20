from orders.exceptions import OrderCreationError

def normalize_phone(phone):
    if not phone or not phone.strip():
        raise OrderCreationError({"phone": "Phone is required"})

    phone = phone.strip()

    if phone[:4] == "+234":
        if len(phone) != 14:
            raise OrderCreationError({"phone": "phone number with country code must be 14 characters"})
        elif not phone[4:].isdigit():
            raise OrderCreationError({"phone": "Phone number must be digits with no letters"})
        elif phone[4] not in "789":
            raise OrderCreationError({"phone": "phone number must contain 7 or 8 or 9 after country code(+234)"})
        return phone
    elif len(phone) != 11 or not phone.isdigit():
        raise OrderCreationError({"phone": "phone number must be 11 digits with no letters"})
    elif phone[0] != "0" or phone[1] not in "789":
        raise OrderCreationError({"phone": "Phone number must start with 0 followed by 7 or 8 or 9"})
    else:
        return "+234" + phone[1:]

