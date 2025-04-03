from django import forms
from .models import Truck

class TruckForm(forms.ModelForm):
    class Meta:
        model = Truck
        fields = ['registration_number', 'brand', 'model', 'capacity', 'is_available']
