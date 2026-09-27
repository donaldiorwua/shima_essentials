from django import forms
from store.models import DeliverySetting

class CheckoutForm(forms.Form):
    customer_name = forms.CharField(max_length=100)
    phone = forms.CharField(max_length=15)
    address = forms.CharField(max_length=150)
    delivery_location = forms.ChoiceField()
    notes = forms.CharField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        delivery_locations = DeliverySetting.objects.filter(active=True)
        choices = [
            (location.location, location.location)
            for location in delivery_locations
        ]
        self.fields["delivery_location"].choices = choices