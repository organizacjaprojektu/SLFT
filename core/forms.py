from django import forms
from .models import Truck, Driver
from django.contrib.auth.models import User

class TruckForm(forms.ModelForm):
    class Meta:
        model = Truck
        fields = ['registration_number', 'brand', 'model', 'capacity', 'is_available']

class DriverForm(forms.ModelForm):
    username = forms.CharField(max_length=150, required=True)
    password = forms.CharField(widget=forms.PasswordInput, required=True)
    first_name = forms.CharField(max_length=50, required=True)
    last_name = forms.CharField(max_length=50, required=True)

    class Meta:
        model = Driver
        fields = ['license_number', 'phone_number', 'is_available']

    def save(self, commit=True):
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            password=self.cleaned_data['password'],
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name']
        )
        driver = super().save(commit=False)
        driver.user = user
        if commit:
            driver.save()
        return driver